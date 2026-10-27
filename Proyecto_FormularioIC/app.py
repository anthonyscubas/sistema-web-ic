import calendar
from io import BytesIO
from flask import send_file
from werkzeug.utils import secure_filename
from models import ReporteAnalistaExcel
from datetime import date
import os
import hmac
import click
from functools import wraps
import secrets
import re
import unicodedata
from ia import generar_analisis_gerencial

from flask import Flask, flash, jsonify, redirect, render_template, request, send_from_directory, url_for, session, abort
from dotenv import load_dotenv
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy import inspect, text

from calculos import calcular_resultado
from config import Config
from inicializar_bd import crear_base_si_falta
from models import (
    Alerta, Analista, Canal, Controller, CoordinadorCanal, CorreoAcceso, EntregaAlerta,
    EntregaAlertaCoordinador, EncuestaAlicorp, EncuestaInterna, Reporte, db,
)
from alertas_email import procesar_alertas, enviar_correo

load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


@app.context_processor
def csrf_template():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["csrf_token"]}


@app.before_request
def verificar_csrf():
    if request.method == "POST" and not hmac.compare_digest(
        request.form.get("csrf_token", ""), session.get("csrf_token", "")
    ):
        abort(400, "Formulario caducado. Recarga la página e inténtalo de nuevo.")


@app.before_request
def proteger_modulos():
    """Protege también el acceso directo por URL según el rol del correo."""
    if request.endpoint in (None, "static", "ingresar", "seleccionar_modulo", "salir", "portada"):
        return

    if request.endpoint in (
        "admin",
        "descargar_plantilla_reportes",
        "cargar_excel_analistas"
    ):
        if session.get("admin") is True and acceso_vigente("admin"):
            return
    elif request.endpoint == "dashboard":
        if (session.get("admin") is True and acceso_vigente("admin")) or (session.get("coordinador") is True and acceso_vigente("coordinador")):
            return
    elif request.endpoint == "encuesta_interna":
        if controller_actual():
            return
    elif request.endpoint == "encuesta_alicorp":
        if session.get("alicorp") is True and acceso_vigente("alicorp"):
            return
        
    elif request.endpoint == "consultar_reportes_analistas":
        if (
            (session.get("admin") is True and acceso_vigente("admin"))
            or controller_actual()
            or (session.get("alicorp") is True and acceso_vigente("alicorp"))
        ):
            return

    if session.get("admin") or session.get("controller_id") or session.get("alicorp") or session.get("coordinador"):
        abort(403)

    return redirect(url_for("ingresar"))



def solo_admin(func):
    @wraps(func)
    def protegido(*args, **kwargs):
        if session.get("admin") is not True or not acceso_vigente("admin"):
            return redirect(url_for("ingresar", siguiente=request.path))
        return func(*args, **kwargs)
    return protegido


def acceso_vigente(rol):
    correo = session.get("correo_acceso")
    if not correo:
        return False
    preparar_accesos()
    return CorreoAcceso.query.filter_by(correo=correo, rol=rol, activo=True).first() is not None


def controller_actual():
    ident = session.get("controller_id")
    controller = db.session.get(Controller, ident) if isinstance(ident, int) else None
    if not controller or not controller.activo:
        return None
    correo = (session.get("correo_acceso") or "").strip().lower()
    if controller.correo.strip().lower() != correo:
        return None
    cuenta = CorreoAcceso.query.filter_by(correo=correo, rol="controller", activo=True).first()
    return controller if cuenta else None


ADMIN_CORREO = "admi@gmail.com"

CANALES_INICIALES = (
    "Minorista - Bodegas",
    "Minorista - Mercados",
    "Mayorista",
    "Consumidor Final",
    "Moderno",
)


def preparar_canales():
    """Inicializa catálogo sin eliminar ni modificar registros existentes."""
    Canal.__table__.create(db.engine, checkfirst=True)
    if Canal.query.first() is None:
        existentes = set(CANALES_INICIALES)
        for modelo in (Analista, Controller, CoordinadorCanal):
            existentes.update(nombre for (nombre,) in db.session.query(modelo.canal).distinct().all() if nombre)
        for nombre in sorted(existentes):
            db.session.add(Canal(nombre=nombre, activo=True))
        db.session.commit()
    else:
        # Recupera canales heredados que no estuvieran en el catálogo.
        actuales = {c.nombre for c in Canal.query.all()}
        for modelo in (Analista, Controller, CoordinadorCanal):
            for (nombre,) in db.session.query(modelo.canal).distinct().all():
                if nombre and nombre not in actuales:
                    db.session.add(Canal(nombre=nombre, activo=True))
                    actuales.add(nombre)
        db.session.commit()


def canal_valido(canal):
    return Canal.query.filter_by(nombre=canal, activo=True).first() is not None


def correo_valido(correo):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo)) and len(correo) <= 180


_ESQUEMA_PREPARADO = False


def asegurar_columnas_evaluacion():
    """Agrega las columnas del nuevo formulario sin borrar datos existentes."""
    global _ESQUEMA_PREPARADO
    if _ESQUEMA_PREPARADO:
        return

    inspector = inspect(db.engine)

    # Conserva el histórico de analistas: desactivar ya no equivale a borrarlo del pasado.
    if inspector.has_table("analistas"):
        columnas_analistas = {c["name"].lower() for c in inspector.get_columns("analistas")}
        if "baja_periodo" not in columnas_analistas:
            db.session.execute(text("ALTER TABLE analistas ADD baja_periodo VARCHAR(7) NULL"))
            db.session.commit()
            inspector = inspect(db.engine)

    cambios = {
        "encuestas_internas": {
            "publica_reportes_tiempo": "INT NULL",
            "participa_reuniones": "INT NULL",
            "comunica_incidencias_tiempo": "INT NULL",
            "resuelve_incidencias_tiempo": "INT NULL",
            "solicita_datos_tiempo": "INT NULL",
            "envia_validar_plazo": "INT NULL",
            "capacita_actualizaciones": "INT NULL",
            "evaluador_correo": "VARCHAR(180) NULL",
            "comunica_status_tiempo": "INT NULL",
            "registra_inconsistencias": "INT NULL",
            "propone_soluciones": "INT NULL",
        },
        "encuestas_alicorp": {
            "publica_reportes_tiempo": "INT NULL",
            "participa_reuniones": "INT NULL",
            "comunica_incidencias_tiempo": "INT NULL",
            "resuelve_incidencias_tiempo": "INT NULL",
            "comunica_status_tiempo": "INT NULL",
            "verifica_consistencia_datos": "INT NULL",
            "propone_soluciones": "INT NULL",
            "evaluador_correo": "VARCHAR(180) NULL",
            "registra_inconsistencias": "INT NULL",
        },
    }

    for tabla, columnas in cambios.items():
        if not inspector.has_table(tabla):
            continue
        existentes = {c["name"].lower() for c in inspector.get_columns(tabla)}
        for nombre, tipo in columnas.items():
            if nombre.lower() not in existentes:
                db.session.execute(text(f"ALTER TABLE {tabla} ADD {nombre} {tipo}"))
    db.session.commit()
    _ESQUEMA_PREPARADO = True


def preparar_accesos():
    """Asegura accesos por correo y las tablas auxiliares del sistema."""
    CorreoAcceso.__table__.create(db.engine, checkfirst=True)
    preparar_canales()
    CoordinadorCanal.__table__.create(db.engine, checkfirst=True)
    EntregaAlertaCoordinador.__table__.create(db.engine, checkfirst=True)
    asegurar_columnas_evaluacion()

    admin = CorreoAcceso.query.filter_by(correo=ADMIN_CORREO).first()
    if not admin:
        db.session.add(CorreoAcceso(correo=ADMIN_CORREO, rol="admin", activo=True))

    for controller in Controller.query.all():
        correo = controller.correo.strip().lower()
        cuenta = CorreoAcceso.query.filter_by(correo=correo).first()
        if cuenta is None:
            db.session.add(CorreoAcceso(correo=correo, rol="controller", activo=controller.activo))
        elif cuenta.rol == "controller":
            cuenta.activo = controller.activo

    # El Coordinador usa el mismo correo registrado para alertas, pero su único módulo es Dashboard.
    for coordinador in CoordinadorCanal.query.all():
        correo = coordinador.correo.strip().lower()
        cuenta = CorreoAcceso.query.filter_by(correo=correo).first()
        if cuenta is None:
            db.session.add(CorreoAcceso(correo=correo, rol="coordinador", activo=coordinador.activo))
        elif cuenta.rol == "coordinador":
            cuenta.activo = coordinador.activo
        elif cuenta.rol == "controller":
            # Corrige instalaciones anteriores que convertían coordinador -> controller.
            es_controller_real = Controller.query.filter(db.func.lower(Controller.correo) == correo).first() is not None
            if not es_controller_real:
                cuenta.rol = "coordinador"
                cuenta.activo = coordinador.activo
    db.session.commit()


@app.route("/correo", methods=["POST"])
def seleccionar_modulo():
    correo = request.form.get("correo", "").strip().lower()
    if correo_valido(correo):
        preparar_accesos()
        cuenta = CorreoAcceso.query.filter_by(correo=correo, activo=True).first()
        session.clear()

        if cuenta and cuenta.rol == "admin":
            session["admin"] = True
            session["correo_acceso"] = correo
            return redirect(url_for("portada"))

        if cuenta and cuenta.rol == "controller":
            controller = Controller.query.filter(
                db.func.lower(Controller.correo) == correo,
                Controller.activo == True,
            ).first()
            if controller:
                session["controller_id"] = controller.id
                session["correo_acceso"] = correo
                return redirect(url_for("encuesta_interna"))

        if cuenta and cuenta.rol == "alicorp":
            session["alicorp"] = True
            session["correo_acceso"] = correo
            return redirect(url_for("encuesta_alicorp"))

        if cuenta and cuenta.rol == "coordinador":
            coordinador = CoordinadorCanal.query.filter(
                db.func.lower(CoordinadorCanal.correo) == correo,
                CoordinadorCanal.activo == True,
            ).first()
            if coordinador:
                session["coordinador"] = True
                session["coordinador_id"] = coordinador.id
                session["correo_acceso"] = correo
                return redirect(url_for("dashboard"))

    session.clear()
    flash("Correo no registrado o inactivo. Solicita acceso al administrador.", "error")
    return redirect(url_for("portada"))


@app.route("/ingresar")
def ingresar():
    return redirect(url_for("portada"))


@app.route("/salir", methods=["POST"])
def salir():
    session.clear()
    return redirect(url_for("portada"))


def periodo_actual():
    hoy = date.today()

    if hoy.month == 1:
        return f"{hoy.year - 1}-12"

    return f"{hoy.year}-{hoy.month - 1:02d}"


def entero(campo):
    valor = request.form.get(campo, "").strip()
    if not valor.isdigit():
        raise ValueError("Todos los valores cuantitativos deben ser enteros desde cero.")
    return int(valor)


def validar_pares(pares):
    for logrado, total, mensaje in pares:
        if logrado > total:
            raise ValueError(mensaje)


def normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.upper().strip().split())


def periodo_valido(periodo):
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", str(periodo or "").strip()))


def reportes_asignados(analista_id, periodo):
    return Reporte.query.filter_by(
        analista_id=analista_id,
        periodo=periodo,
        activo=True,
    ).count()


@app.route("/")
def portada():
    if session.get("admin") is True and acceso_vigente("admin"):
        return render_template("portada.html", rol="admin")
    if controller_actual():
        return redirect(url_for("encuesta_interna"))
    if session.get("alicorp") is True and acceso_vigente("alicorp"):
        return redirect(url_for("encuesta_alicorp"))
    if session.get("coordinador") is True and acceso_vigente("coordinador"):
        return redirect(url_for("dashboard"))
    return render_template("portada.html", rol=None)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    vista = request.args.get("vista", "resumen")
    if vista not in ("resumen", "historico"):
        return redirect(url_for("dashboard", vista="resumen"))
    periodo_historico = request.args.get("periodo_historico", periodo_actual())
    if not periodo_valido(periodo_historico):
        periodo_historico = periodo_actual()
    periodo = request.args.get("periodo", periodo_actual())
    if not periodo_valido(periodo):
        periodo = periodo_actual()

    # Dashboard histórico: un analista se muestra si pertenecía al equipo en el periodo consultado.
    # Al desactivarlo en octubre, sigue visible en septiembre pero ya no desde octubre.
    # Administrador: todos los canales
    # Coordinador: únicamente su canal asignado
    consulta_analistas = Analista.query

    if session.get("coordinador") is True:
        coordinador = db.session.get(
            CoordinadorCanal,
            session.get("coordinador_id")
        )

        if not coordinador or not coordinador.activo:
            abort(403)

        consulta_analistas = consulta_analistas.filter(
            Analista.canal == coordinador.canal
        )

    analistas = []

    for analista in consulta_analistas.order_by(Analista.nombre).all():
        alta_periodo = analista.creado_en.strftime("%Y-%m") if analista.creado_en else None

        vigente_desde_alta = not alta_periodo or periodo >= alta_periodo

        vigente_antes_baja = (
            analista.activo
            or not analista.baja_periodo
            or periodo < analista.baja_periodo
        )

        tiene_datos = (
            Reporte.query.filter_by(
                analista_id=analista.id,
                periodo=periodo
            ).first() is not None

            or EncuestaInterna.query.filter_by(
                analista_id=analista.id,
                periodo=periodo
            ).first() is not None

            or EncuestaAlicorp.query.filter_by(
                analista_id=analista.id,
                periodo=periodo
            ).first() is not None
        )

        if tiene_datos or (vigente_desde_alta and vigente_antes_baja):
            analistas.append(analista)
    resultados = [
        calcular_resultado(a, periodo, Reporte, EncuestaInterna, EncuestaAlicorp)
        for a in analistas
    ]
    con_evaluacion = [r for r in resultados if r["evaluaciones_realizadas"] > 0]
    completos = [r for r in resultados if r["evaluacion_completa"]]
    promedio = (
        round(sum(r["nota_final"] for r in con_evaluacion) / len(con_evaluacion), 2)
        if con_evaluacion else None
    )
    resumen = {
        "evaluados": len(con_evaluacion),
        "completos": len(completos),
        "en_proceso": sum(r["evaluaciones_realizadas"] == 1 for r in resultados),
        "sin_evaluar": sum(r["evaluaciones_realizadas"] == 0 for r in resultados),
        "promedio": promedio,
        "excelentes": sum(r["estado"] == "Excelente" for r in con_evaluacion),
        "cumplen": sum(r["estado"] == "Cumple" for r in con_evaluacion),
        "desarrollo": sum(r["estado"] == "En desarrollo" for r in con_evaluacion),
        "requiere_mejora": sum(r["estado"] == "Requiere mejora" for r in con_evaluacion),
    }

    canales = {}
    for resultado in resultados:
        canal = resultado["analista"].canal.strip() or "Sin canal"
        datos = canales.setdefault(canal, {"canal": canal, "total": 0, "evaluados": 0, "suma": 0.0})
        datos["total"] += 1
        if resultado["evaluaciones_realizadas"] > 0:
            datos["evaluados"] += 1
            datos["suma"] += resultado["nota_final"]
    por_canal = sorted(({
        "canal": datos["canal"],
        "total": datos["total"],
        "evaluados": datos["evaluados"],
        "promedio": round(datos["suma"] / datos["evaluados"], 2) if datos["evaluados"] else None,
    } for datos in canales.values()), key=lambda fila: fila["canal"].casefold())
        # ============================================================
    # HISTÓRICO DE EVOLUCIÓN
    # ============================================================

    anio = periodo[:4]

    historico = []

    for analista in analistas:
        meses_analista = []

        for mes in range(1, 13):
            periodo_mes = f"{anio}-{mes:02d}"

            resultado_mes = calcular_resultado(
                analista,
                periodo_mes,
                Reporte,
                EncuestaInterna,
                EncuestaAlicorp
            )

            # Solo mostramos meses donde existe al menos una evaluación
            if resultado_mes["evaluaciones_realizadas"] > 0:
                meses_analista.append({
                    "periodo": periodo_mes,
                    "nota_final": resultado_mes["nota_final"],
                    "nota_interna": resultado_mes["nota_interna"],
                    "nota_alicorp": resultado_mes["nota_alicorp"],
                    "porcentaje_interno": resultado_mes["porcentaje_interno"],
                    "porcentaje_alicorp": resultado_mes["porcentaje_alicorp"]
                })

        historico.append({
            "id": analista.id,
            "nombre": analista.nombre,
            "canal": analista.canal,
            "meses": meses_analista
        })
    analisis_ia = None
    error_ia = None
    if request.method == "POST":
        periodo_solicitado = request.form.get("periodo", "").strip()
        if not periodo_valido(periodo_solicitado):
            error_ia = "Selecciona un periodo válido."
        elif periodo_solicitado != periodo:
            error_ia = "El periodo solicitado no coincide con el mostrado."
        elif not con_evaluacion:
            error_ia = "Se necesita al menos una encuesta registrada para generar el análisis."
        else:
            try:
                analisis_ia = generar_analisis_gerencial(periodo, resumen, por_canal, resultados)
            except RuntimeError as exc:
                error_ia = str(exc)

    # Histórico de respuestas: consulta independiente del periodo del resumen.
    historico_respuestas = []
    if vista == "historico":
        preguntas_interna = (
            ('solicita_datos_tiempo', '¿El analista solicita los datos necesarios para realizar el reporte a tiempo?'),
            ('envia_validar_plazo', '¿El analista envia a validar la información relevada en los plazos solicitados?'),
            ('publica_reportes_tiempo', '¿El analista envia / publica los reportes / solicitudes a tiempo?'),
            ('comunica_incidencias_tiempo', '¿El analista comunica a tiempo incidencias encontradas en la data al equipo comercial y cliente?'),
            ('resuelve_incidencias_tiempo', '¿El analista atiende y resuelve las incidencias levantadas a tiempo?'),
            ('capacita_actualizaciones', '¿El analista capacita al equipo comercial en el uso de plataforma app /web cuando hay actualizaciones?'),
            ('comunica_status_tiempo', '¿El analista comunica status de avances del relevo de la información a tiempo?'),
            ('registra_inconsistencias', '¿El analista registró inconsistencia en el/los reporte a cargo del analista?'),
            ('propone_soluciones', "¿El analista aplica soluciones Innovadora en el/los reporte/KPI's a su cargo?"),
        )
        preguntas_alicorp = (
            ('publica_reportes_tiempo', '¿El analista envia / publica los reportes / solicitudes a tiempo?'),
            ('participa_reuniones', '¿El analista participa en reuniones CLAVES con el cliente?'),
            ('resuelve_incidencias_tiempo', '¿El analista atiende y resuelve las incidencias levantadas a tiempo?'),
            ('registra_inconsistencias', '¿El analista registró inconsistencia en el/los reporte a cargo del analista?'),
            ('propone_soluciones', "¿El analista aplica soluciones Innovadora en el/los reporte/KPI's a su cargo?"),
        )
        for modelo, etiqueta, preguntas in (
            (EncuestaInterna, "Interna", preguntas_interna),
            (EncuestaAlicorp, "Alicorp", preguntas_alicorp),
        ):
            consulta = (
                modelo.query
                .join(Analista, Analista.id == modelo.analista_id)
                .filter(modelo.periodo == periodo_historico)
            )

            if session.get("coordinador") is True:
                consulta = consulta.filter(
                    Analista.canal == coordinador.canal
                )

            filas = consulta.order_by(Analista.nombre).all()
            for fila in filas:
                historico_respuestas.append({
                    "tipo": etiqueta,
                    "analista": fila.analista.nombre,
                    "canal": fila.analista.canal,
                    "evaluador": fila.evaluador,
                    "periodo": fila.periodo,
                    "comentario": getattr(fila, "comentario", None) or "",
                    "respuestas": [(pregunta, getattr(fila, campo)) for campo, pregunta in preguntas],
                })

    return render_template(
        "dashboard.html",
        vista=vista,
        periodo_historico=periodo_historico,
        historico_respuestas=historico_respuestas,
        resultados=resultados,
        resumen=resumen,
        por_canal=por_canal,
        periodo=periodo,
        historico=historico,
        analisis_ia=analisis_ia,
        error_ia=error_ia,
    )



@app.route("/controller/encuesta", methods=["GET", "POST"])
def encuesta_interna():

    controller = controller_actual()

    if not controller:
        abort(403)

    # Todos los analistas activos, sin filtrar por canal
    analistas = Analista.query.filter_by(
        activo=True
    ).order_by(Analista.nombre).all()

    campos = ('solicita_datos_tiempo', 'envia_validar_plazo', 'publica_reportes_tiempo', 'comunica_incidencias_tiempo', 'resuelve_incidencias_tiempo', 'capacita_actualizaciones', 'comunica_status_tiempo', 'registra_inconsistencias', 'propone_soluciones')

    if request.method == "POST":

        try:
            periodo = request.form.get("periodo", periodo_actual()).strip()

            if not periodo_valido(periodo):
                raise ValueError(
                    "Solo se puede evaluar el periodo vigente."
                )

            if not analistas:
                raise ValueError(
                    "No hay analistas activos para evaluar."
                )

            # Validar todas las respuestas antes de guardar
            respuestas = []

            for analista in analistas:

                valores = {}

                for campo in campos:

                    nombre_campo = f"a_{analista.id}_{campo}"

                    valor = int(request.form[nombre_campo])

                    if not 1 <= valor <= 5:
                        raise ValueError(
                            "Cada respuesta debe estar entre 1 y 5."
                        )

                    valores[campo] = valor

                respuestas.append((analista, valores))

            # Guardar todas las evaluaciones
            for analista, valores in respuestas:

                fila = EncuestaInterna.query.filter_by(
                    analista_id=analista.id,
                    periodo=periodo
                ).first()

                if fila is None:

                    fila = EncuestaInterna(
                        analista_id=analista.id,
                        periodo=periodo,
                        evaluador=controller.nombre
                    )

                    db.session.add(fila)

                fila.evaluador = controller.nombre

                fila.evaluador_correo = (
                    controller.correo.strip().lower()
                )

                for campo, valor in valores.items():
                    setattr(fila, campo, valor)

            db.session.commit()

            flash(
                f"Evaluación interna guardada para "
                f"{len(respuestas)} analistas.",
                "success"
            )

            return redirect(url_for("encuesta_interna"))

        except (ValueError, KeyError, TypeError) as exc:

            db.session.rollback()

            flash(
                f"No se guardaron cambios: {exc}",
                "error"
            )

    return render_template(
        "encuesta_interna.html",
        analistas=analistas,
        controller=controller,
        periodo=periodo_actual()
    )


CAMPOS_ALICORP = ('publica_reportes_tiempo', 'participa_reuniones', 'resuelve_incidencias_tiempo', 'registra_inconsistencias', 'propone_soluciones')

@app.route("/alicorp/encuesta", methods=["GET", "POST"])
def encuesta_alicorp():
    correo_evaluador = (session.get("correo_acceso") or "").strip().lower()
    analistas = Analista.query.filter_by(activo=True).order_by(Analista.nombre).all()

    if request.method == "POST":
        try:
            periodo = request.form.get("periodo", "").strip()
            if not periodo_valido(periodo):
                raise ValueError("Solo se puede evaluar el periodo vigente.")
            # Guardar únicamente filas completas de analistas que fueron evaluados.
            respuestas = []

            for analista in analistas:
                valores = {}

                for campo in CAMPOS_ALICORP:
                    dato = request.form.get(
                        f"a_{analista.id}_{campo}", ""
                    ).strip()

                    if not dato:
                        continue

                    valor = int(dato)

                    if not 1 <= valor <= 5:
                        raise ValueError("El puntaje debe estar entre 1 y 5.")

                    valores[campo] = valor

                # No respondió este analista: ignorar.
                if not valores:
                    continue

                # Respondió parcialmente: pedir completar.
                if len(valores) != len(CAMPOS_ALICORP):
                    raise ValueError(
                        f"Completa todas las preguntas de {analista.nombre}."
                    )

                comentario = request.form.get(
                    f"comentario_{analista.id}", ""
                ).strip()[:800]

                respuestas.append((analista, valores, comentario))

            if not respuestas:
                raise ValueError("Debes evaluar al menos un analista.")
            for analista, valores, comentario in respuestas:
                fila = EncuestaAlicorp.query.filter_by(analista_id=analista.id, periodo=periodo).first()
                if fila is None:
                    fila = EncuestaAlicorp(analista_id=analista.id, periodo=periodo,
                        evaluador=correo_evaluador)
                    db.session.add(fila)
                fila.evaluador = correo_evaluador
                fila.evaluador_correo = correo_evaluador
                fila.comentario = comentario
                for campo, valor in valores.items():
                    setattr(fila, campo, valor)
            db.session.commit()
            flash(f"Evaluación Alicorp guardada para {len(respuestas)} analistas.", "success")
            return redirect(url_for("encuesta_alicorp"))
        except (ValueError, KeyError, TypeError) as exc:
            db.session.rollback()
            flash(f"No se guardaron cambios: {exc}", "error")

    return render_template(
        "encuesta_alicorp.html",
        analistas=analistas,
        periodo=periodo_actual(),
        correo_evaluador=correo_evaluador,
    )


@app.route("/admin", methods=["GET", "POST"])
@solo_admin
def admin():
    # Mantener la pestaña de administración después de cada operación.
    # Se acepta únicamente una vista conocida: nunca una URL proporcionada por el cliente.
    vistas_permitidas = {"analistas", "coordinadores", "controllers", "alicorp", "canales", "reportes"}
    vista_actual = request.args.get("vista", "analistas")
    if vista_actual not in vistas_permitidas:
        vista_actual = "analistas"

    if request.method == "POST":
        accion = request.form.get("accion")
        vistas_por_accion = {
            "crear_canal": "canales", "editar_canal": "canales", "estado_canal": "canales",
            "crear_analista": "analistas", "estado_analista": "analistas",
            "eliminar_analista": "analistas",
            "crear_controller": "controllers", "estado_controller": "controllers",
            "crear_coordinador": "coordinadores", "editar_coordinador": "coordinadores",
            "estado_coordinador": "coordinadores", "enviar_alertas": "coordinadores",
            "crear_alicorp": "alicorp", "estado_alicorp": "alicorp",
        }
        vista_post = vistas_por_accion.get(accion, "analistas")
        periodo_post = request.form.get("periodo", periodo_actual())
        if not periodo_valido(periodo_post):
            periodo_post = periodo_actual()

        def volver_admin(**kwargs):
            return redirect(url_for("admin", vista=vista_post, periodo=periodo_post, **kwargs))

        if accion in {"crear_canal", "editar_canal", "estado_canal"}:
            preparar_canales()
            if accion == "crear_canal":
                nombre = " ".join(request.form.get("nombre", "").strip().split())
                if not nombre or len(nombre) > 100:
                    flash("El nombre del canal debe tener entre 1 y 100 caracteres.", "error")
                    return volver_admin()
                if Canal.query.filter(db.func.lower(Canal.nombre) == nombre.lower()).first():
                    flash("Ese canal ya está registrado.", "error")
                    return volver_admin()
                db.session.add(Canal(nombre=nombre, activo=True))
            else:
                canal = db.session.get(Canal, request.form.get("canal_id", type=int))
                if canal is None:
                    abort(404)
                if accion == "estado_canal":
                    canal.activo = not canal.activo
                else:
                    nombre = " ".join(request.form.get("nombre", "").strip().split())
                    if not nombre or len(nombre) > 100:
                        flash("El nombre del canal debe tener entre 1 y 100 caracteres.", "error")
                        return volver_admin(editar_canal=canal.id)
                    duplicado = Canal.query.filter(db.func.lower(Canal.nombre) == nombre.lower(), Canal.id != canal.id).first()
                    if duplicado:
                        flash("Ya existe un canal con ese nombre.", "error")
                        return volver_admin(editar_canal=canal.id)
                    anterior = canal.nombre
                    if anterior != nombre:
                        # Mantener las relaciones por canal en las tablas ya desplegadas.
                        for modelo in (Analista, Controller, CoordinadorCanal):
                            db.session.query(modelo).filter(modelo.canal == anterior).update(
                                {modelo.canal: nombre}, synchronize_session=False
                            )
                        canal.nombre = nombre

        elif accion == "crear_analista":
            nombre = request.form.get("nombre", "").strip()
            canal = request.form.get("canal", "").strip()
            correo = request.form.get("correo", "").strip().lower()
            if not nombre or not canal_valido(canal):
                flash("Completa el nombre y selecciona un canal válido.", "error")
                return volver_admin()
            if correo and not correo_valido(correo):
                flash("El correo del analista no es válido.", "error")
                return volver_admin()
            db.session.add(Analista(nombre=nombre, canal=canal, correo=correo, correo_controller=""))

        elif accion == "crear_controller":
            nombre = request.form.get("nombre", "").strip()
            correo = request.form.get("correo", "").strip().lower()
            canal = request.form.get("canal", "").strip()
            if not nombre or not canal_valido(canal) or not correo_valido(correo):
                flash("Completa nombre, correo y selecciona un canal válido.", "error")
                return volver_admin()
            preparar_accesos()
            if Controller.query.filter(db.func.lower(Controller.correo) == correo).first() or CorreoAcceso.query.filter_by(correo=correo).first():
                flash("Ya existe un acceso con ese correo.", "error")
                return volver_admin()
            controller = Controller(nombre=nombre, correo=correo, canal=canal)
            db.session.add(controller)
            db.session.add(CorreoAcceso(correo=correo, rol="controller", activo=True))

        elif accion == "crear_coordinador":
            nombre = request.form.get("nombre", "").strip()
            correo = request.form.get("correo", "").strip().lower()
            canal = request.form.get("canal", "").strip()
            if not nombre or not correo_valido(correo) or not canal_valido(canal):
                flash("Completa nombre, correo y selecciona un canal válido.", "error")
                return volver_admin()
            preparar_accesos()
            if CoordinadorCanal.query.filter(db.func.lower(CoordinadorCanal.correo) == correo).first() or CorreoAcceso.query.filter_by(correo=correo).first():
                flash("Ya existe un acceso con ese correo.", "error")
                return volver_admin()
            if CoordinadorCanal.query.filter_by(canal=canal).first():
                flash(f"El canal {canal} ya tiene un Coordinador asignado. Edítalo si deseas reemplazarlo.", "error")
                return volver_admin()
            db.session.add(CoordinadorCanal(nombre=nombre, correo=correo, canal=canal, activo=True))
            db.session.add(CorreoAcceso(correo=correo, rol="coordinador", activo=True))

        elif accion == "editar_coordinador":
            coordinador_id = int(request.form["coordinador_id"])
            coordinador = db.session.get(CoordinadorCanal, coordinador_id)
            if not coordinador:
                abort(404)
            nombre = request.form.get("nombre", "").strip()
            correo = request.form.get("correo", "").strip().lower()
            canal = request.form.get("canal", "").strip()
            if not nombre or not correo_valido(correo) or not canal_valido(canal):
                flash("Completa nombre, correo y selecciona un canal válido.", "error")
                return volver_admin(editar_coordinador=coordinador_id)
            correo_repetido = CoordinadorCanal.query.filter(
                db.func.lower(CoordinadorCanal.correo) == correo,
                CoordinadorCanal.id != coordinador_id,
            ).first()
            canal_repetido = CoordinadorCanal.query.filter(
                CoordinadorCanal.canal == canal,
                CoordinadorCanal.id != coordinador_id,
            ).first()
            if correo_repetido:
                flash("Ya existe otro Coordinador con ese correo.", "error")
                return volver_admin(editar_coordinador=coordinador_id)
            if canal_repetido:
                flash(f"El canal {canal} ya tiene otro Coordinador asignado.", "error")
                return volver_admin(editar_coordinador=coordinador_id)
            correo_anterior = coordinador.correo.strip().lower()
            cuenta = CorreoAcceso.query.filter_by(correo=correo_anterior, rol="coordinador").first()
            otra_cuenta = CorreoAcceso.query.filter(CorreoAcceso.correo == correo, CorreoAcceso.id != (cuenta.id if cuenta else -1)).first()
            if otra_cuenta:
                flash("Ese correo ya tiene otro acceso registrado.", "error")
                return volver_admin(editar_coordinador=coordinador_id)
            coordinador.nombre = nombre
            coordinador.correo = correo
            coordinador.canal = canal
            if cuenta:
                cuenta.correo = correo
                cuenta.activo = coordinador.activo
            else:
                db.session.add(CorreoAcceso(correo=correo, rol="coordinador", activo=coordinador.activo))

        elif accion == "estado_coordinador":
            coordinador = db.session.get(CoordinadorCanal, int(request.form["coordinador_id"]))
            if not coordinador:
                abort(404)
            coordinador.activo = not coordinador.activo
            cuenta = CorreoAcceso.query.filter_by(correo=coordinador.correo.strip().lower(), rol="coordinador").first()
            if cuenta:
                cuenta.activo = coordinador.activo

        elif accion == "crear_alicorp":
            correo = request.form.get("correo", "").strip().lower()
            preparar_accesos()
            if not correo_valido(correo) or CorreoAcceso.query.filter_by(correo=correo).first() or Controller.query.filter(db.func.lower(Controller.correo) == correo).first():
                flash("Correo inválido o ya registrado.", "error")
                return volver_admin()
            db.session.add(CorreoAcceso(correo=correo, rol="alicorp", activo=True))

        elif accion == "estado_alicorp":
            cuenta = db.session.get(CorreoAcceso, int(request.form["correo_id"]))
            if not cuenta or cuenta.rol != "alicorp":
                abort(404)
            cuenta.activo = not cuenta.activo

        elif accion == "estado_controller":
            c = db.session.get(Controller, int(request.form["controller_id"]))
            if not c:
                abort(404)
            c.activo = not c.activo
            cuenta = CorreoAcceso.query.filter_by(correo=c.correo.strip().lower(), rol="controller").first()
            if cuenta:
                cuenta.activo = c.activo

        elif accion == "enviar_alertas":
            periodo_alerta = request.form.get("periodo", "")
            if not periodo_valido(periodo_alerta):
                flash("Selecciona un periodo válido para las alertas.", "error")
            else:
                try:
                    enviados, pendientes, errores = procesar_alertas(periodo_alerta)
                    flash(
                        f"Alertas a Coordinadores: {enviados} correo(s) enviados; {pendientes} pendientes. " + " | ".join(errores[:3]),
                        "error" if errores else "success",
                    )
                except ValueError as exc:
                    flash(str(exc), "error")
            return redirect(url_for("admin", vista="coordinadores", periodo=periodo_alerta))

        elif accion == "estado_analista":
            a = db.session.get(Analista, int(request.form["analista_id"]))
            if not a:
                abort(404)
            a.activo = not a.activo
            a.baja_periodo = None if a.activo else periodo_actual()

        elif accion == "eliminar_analista":
            analista_id = int(request.form["analista_id"])
            a = db.session.get(Analista, analista_id)
            if not a:
                flash("El analista ya no existe.", "error")
                return volver_admin()
            ids_alertas = [fila.id for fila in Alerta.query.filter_by(analista_id=analista_id).all()]
            if ids_alertas:
                EntregaAlerta.query.filter(EntregaAlerta.alerta_id.in_(ids_alertas)).delete(synchronize_session=False)
                EntregaAlertaCoordinador.query.filter(EntregaAlertaCoordinador.alerta_id.in_(ids_alertas)).delete(synchronize_session=False)
            Alerta.query.filter_by(analista_id=analista_id).delete(synchronize_session=False)
            EncuestaAlicorp.query.filter_by(analista_id=analista_id).delete(synchronize_session=False)
            EncuestaInterna.query.filter_by(analista_id=analista_id).delete(synchronize_session=False)
            Reporte.query.filter_by(analista_id=analista_id).delete(synchronize_session=False)
            db.session.delete(a)

        # Se conserva la lógica antigua de reportes por compatibilidad con la BD,
        # aunque esos módulos ya no se muestran en la interfaz del administrador.
        elif accion == "crear_reporte":
            db.session.add(Reporte(analista_id=int(request.form["analista_id"]),
                                   periodo=request.form["periodo"], indicador=request.form["indicador"].strip()))
        elif accion == "estado_reporte":
            r = db.session.get(Reporte, int(request.form["reporte_id"]))
            if r:
                r.activo = not r.activo
        elif accion == "cargar_reportes_excel":
            archivo = request.files.get("archivo_excel")
            if not archivo or not archivo.filename:
                flash("Selecciona el Excel de carga.", "error")
                return volver_admin()
            if not archivo.filename.lower().endswith(".xlsx"):
                flash("El archivo debe ser .xlsx y respetar el molde descargable.", "error")
                return volver_admin()
            try:
                creados, omitidos, errores = cargar_reportes_desde_excel(archivo.stream)
                db.session.commit()
                mensaje = f"Carga terminada: {creados} reporte(s) creado(s) y {omitidos} omitido(s)."
                if errores:
                    mensaje += " Errores: " + " | ".join(errores[:5])
                    if len(errores) > 5:
                        mensaje += f" | y {len(errores) - 5} error(es) adicional(es)."
                flash(mensaje, "success" if not errores else "error")
                return volver_admin()
            except (InvalidFileException, KeyError, ValueError) as exc:
                db.session.rollback()
                flash(f"No se pudo cargar el Excel: {exc}", "error")
                return volver_admin()

        db.session.commit()
        flash("Cambios guardados.", "success")
        return volver_admin()

    periodo = request.args.get("periodo", periodo_actual())
    if not periodo_valido(periodo):
        periodo = periodo_actual()
    preparar_canales()
    editar_canal_id = request.args.get("editar_canal", type=int)
    canal_edicion = db.session.get(Canal, editar_canal_id) if editar_canal_id else None
    editar_id = request.args.get("editar_coordinador", type=int)
    coordinador_edicion = db.session.get(CoordinadorCanal, editar_id) if editar_id else None
    return render_template(
        "admin.html",
        analistas=Analista.query.order_by(Analista.nombre).all(),
        controllers=Controller.query.order_by(Controller.nombre).all(),
        coordinadores=CoordinadorCanal.query.order_by(CoordinadorCanal.canal).all(),
        coordinador_edicion=coordinador_edicion,
        correos_alicorp=CorreoAcceso.query.filter_by(rol="alicorp").order_by(CorreoAcceso.correo).all(),
        reportes=Reporte.query.filter_by(periodo=periodo).order_by(Reporte.id.desc()).all(),
        periodo=periodo,
        canales=[c.nombre for c in Canal.query.filter_by(activo=True).order_by(Canal.nombre).all()],
        canales_registrados=Canal.query.order_by(Canal.nombre).all(),
        canal_edicion=canal_edicion,
        vista_actual=vista_actual,
    )


def cargar_reportes_desde_excel(stream):
    libro = load_workbook(stream, read_only=True, data_only=True)
    if "Carga_Reportes" not in libro.sheetnames:
        raise ValueError("No existe la hoja Carga_Reportes.")
    hoja = libro["Carga_Reportes"]
    filas = hoja.iter_rows(values_only=True)
    encabezados = next(filas, None)
    requeridos = ["ID_ANALISTA", "ANALISTA", "PERIODO", "INDICADOR"]
    encabezados_limpios = [normalizar_texto(x) for x in (encabezados or [])]
    if encabezados_limpios[:4] != requeridos:
        raise ValueError("Los encabezados deben ser ID_ANALISTA, ANALISTA, PERIODO e INDICADOR.")

    analistas = Analista.query.all()
    por_id = {a.id: a for a in analistas}
    por_nombre = {normalizar_texto(a.nombre): a for a in analistas}
    existentes = {
        (r.analista_id, r.periodo, normalizar_texto(r.indicador))
        for r in Reporte.query.all()
    }
    creados = 0
    omitidos = 0
    errores = []
    for numero_fila, fila in enumerate(filas, start=2):
        valores = list(fila[:4]) + [None] * max(0, 4 - len(fila))
        id_valor, nombre, periodo, indicador = valores[:4]
        if not any(v not in (None, "") for v in valores[:4]):
            continue
        if normalizar_texto(nombre) == "EJEMPLO ANALISTA":
            omitidos += 1
            continue
        analista = None
        if id_valor not in (None, ""):
            try:
                analista = por_id.get(int(id_valor))
            except (TypeError, ValueError):
                errores.append(f"Fila {numero_fila}: ID_ANALISTA inválido.")
                continue
        if not analista and nombre not in (None, ""):
            analista = por_nombre.get(normalizar_texto(nombre))
        if not analista:
            errores.append(f"Fila {numero_fila}: analista no encontrado.")
            continue
        if not analista.activo:
            errores.append(f"Fila {numero_fila}: {analista.nombre} está inactivo.")
            continue
        periodo = str(periodo or "").strip()
        indicador = str(indicador or "").strip()
        if not periodo_valido(periodo):
            errores.append(f"Fila {numero_fila}: periodo inválido; usa AAAA-MM.")
            continue
        if not indicador:
            errores.append(f"Fila {numero_fila}: indicador vacío.")
            continue
        clave = (analista.id, periodo, normalizar_texto(indicador))
        if clave in existentes:
            omitidos += 1
            continue
        db.session.add(Reporte(analista_id=analista.id, periodo=periodo, indicador=indicador))
        existentes.add(clave)
        creados += 1
    return creados, omitidos, errores


@app.route("/admin/plantilla-reportes")
@solo_admin
def descargar_plantilla_reportes():
    return send_from_directory(
        app.static_folder,
        "Plantilla_Carga_Reportes.xlsx",
        as_attachment=True,
        download_name="Plantilla_Carga_Reportes.xlsx",
    )


# ============================================================
# REPORTES DE ANALISTAS - CARGA DESDE EXCEL
# ============================================================

MESES_EXCEL = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SETIEMBRE": 9,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12
}


# ============================================================
# CARGAR EXCEL DESDE EL ADMINISTRADOR
# ============================================================

@app.route("/admin/cargar-excel-analistas", methods=["POST"])
@solo_admin
def cargar_excel_analistas():

    archivo = request.files.get("archivo_excel")

    if not archivo or not archivo.filename.lower().endswith(".xlsx"):
        flash("Selecciona un archivo Excel .xlsx", "error")
        return redirect(url_for("admin", vista="reportes"))

    try:
        anio = int(request.form["anio"])

        if not 2020 <= anio <= 2100:
            raise ValueError("Año inválido.")

        libro = load_workbook(
            BytesIO(archivo.read()),
            read_only=True,
            data_only=True
        )

        try:
            hoja = libro.active
            filas = hoja.iter_rows(values_only=True)
            encabezados = next(filas, None)

            esperados = [
                "N°",
                "CANAL",
                "PROGRAMA",
                "ANALISTA",
                "NOMBRE DE REPORTE",
                "KPI QUE SE REVISAN",
                "FRECUENCIA ACTUALIZACION",
                "CONTACTO COMERCIAL ALICORP",
                "CONTACTO INTERNO IC",
                "MES"
            ]

            if not encabezados:
                raise ValueError("El Excel está vacío.")

            recibidos = [
                normalizar_texto(v)
                for v in encabezados[:10]
            ]

            if recibidos != [
                normalizar_texto(v) for v in esperados
            ]:
                raise ValueError(
                    "Las columnas del Excel no coinciden."
                )

            registros = []
            periodos = set()

            for numero, fila in enumerate(filas, start=2):

                valores = list(fila[:10])
                valores += [None] * (10 - len(valores))

                if not any(
                    v is not None for v in valores
                ):
                    continue

                mes = normalizar_texto(valores[9])
                numero_mes = MESES_EXCEL.get(mes)

                if not numero_mes:
                    raise ValueError(
                        f"Fila {numero}: mes inválido: {valores[9]}"
                    )

                periodo = f"{anio}-{numero_mes:02d}"
                periodos.add(periodo)

                def dato(i):
                    return (
                        str(valores[i]).strip()
                        if valores[i] is not None
                        else ""
                    )

                if not dato(1) or not dato(3) or not dato(4):
                    raise ValueError(
                        f"Fila {numero}: faltan Canal, "
                        "Analista o Nombre de Reporte."
                    )

                registros.append(
                    ReporteAnalistaExcel(
                        periodo=periodo,
                        canal=dato(1),
                        programa=dato(2),
                        analista=dato(3),
                        nombre_reporte=dato(4),
                        kpi=dato(5),
                        frecuencia=dato(6),
                        contacto_comercial=dato(7),
                        contacto_interno=dato(8)
                    )
                )

        finally:
            libro.close()

        if not registros:
            raise ValueError(
                "No hay reportes para cargar."
            )

        # Reemplazar solamente los meses del Excel
        ReporteAnalistaExcel.query.filter(
            ReporteAnalistaExcel.periodo.in_(periodos)
        ).delete(synchronize_session=False)

        db.session.add_all(registros)
        db.session.commit()

        flash(
            f"Se cargaron {len(registros)} reportes correctamente.",
            "success"
        )

    except Exception as exc:
        db.session.rollback()

        flash(
            f"Error al cargar reportes: {exc}",
            "error"
        )

    return redirect(
        url_for("admin", vista="reportes")
    )


# ============================================================
# CONSULTAR REPORTES DESDE ALICORP E INTERNO
# ============================================================

@app.route("/reportes-analistas")
def consultar_reportes_analistas():

    registros = ReporteAnalistaExcel.query.order_by(
        ReporteAnalistaExcel.periodo.desc(),
        ReporteAnalistaExcel.canal,
        ReporteAnalistaExcel.analista
    ).all()

    return jsonify([
        {
            "periodo": r.periodo,
            "canal": r.canal,
            "analista": r.analista,
            "reporte": r.nombre_reporte,
            "kpi": r.kpi,
            "frecuencia": r.frecuencia
        }
        for r in registros
    ])

@app.cli.command("crear-tablas")
def crear_tablas():
    crear_base_si_falta(app.config["SQLALCHEMY_DATABASE_URI"])
    db.create_all()
    preparar_accesos()
    print("Tablas preparadas en SQL Server.")


@app.cli.command("enviar-alertas")
@click.option("--periodo", required=True, help="Periodo AAAA-MM")
def enviar_alertas_comando(periodo):
    if not periodo_valido(periodo):
        raise ValueError("El periodo debe tener el formato AAAA-MM.")
    enviados, pendientes, errores = procesar_alertas(periodo)
    print(f"Correos enviados: {enviados}; pendientes: {pendientes}")
    for error in errores: print(error)


@app.cli.command("probar-correo")
@click.option("--destino", required=True, help="Tu propia dirección de correo para la prueba")
def probar_correo_comando(destino):
    """Manda una prueba sin generar alertas ni marcar entregas como enviadas."""
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", destino):
        raise click.BadParameter("Indica una dirección de correo válida.")
    try:
        enviar_correo(destino, "Prueba | Evaluación IC",
                      "Esta es una prueba de correo de Evaluación IC. No se enviaron alertas a Coordinadores.")
    except Exception as exc:
        raise click.ClickException(f"No se pudo enviar la prueba: {exc}") from exc
    click.echo(f"Correo de prueba enviado a {destino}. Revisa también la carpeta de enviados.")


if __name__ == "__main__":
    crear_base_si_falta(app.config["SQLALCHEMY_DATABASE_URI"])
    with app.app_context():
        db.create_all()
        preparar_accesos()
    app.run(debug=True)
