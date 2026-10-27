PUNTAJE_MAX_INTERNO = 45.0
PUNTAJE_MAX_ALICORP = 55.0
PUNTAJE_MAX_TOTAL = 100.0

PESOS_INTERNOS = {'solicita_datos_tiempo': 5, 'envia_validar_plazo': 5, 'publica_reportes_tiempo': 7, 'comunica_incidencias_tiempo': 5, 'resuelve_incidencias_tiempo': 6, 'capacita_actualizaciones': 4, 'comunica_status_tiempo': 4, 'registra_inconsistencias': 5, 'propone_soluciones': 4}
PESOS_ALICORP = {'publica_reportes_tiempo': 14, 'participa_reuniones': 9, 'resuelve_incidencias_tiempo': 13, 'registra_inconsistencias': 10, 'propone_soluciones': 9}


def proporcion(logros, total, cero_es_diez=True):
    """Compatibilidad para evaluaciones históricas del modelo anterior."""
    if total == 0:
        return 10.0 if cero_es_diez else 0.0
    return round(max(0, min(10, logros / total * 10)), 2)


def puntaje_escala(valor):
    """Convierte una respuesta 1..5 a una nota comparable de 2..10."""
    if valor is None:
        return None
    return round(max(1, min(5, int(valor))) * 2.0, 2)


def puntos_por_pregunta(valor, maximo):
    """Convierte una respuesta 1..5 al aporte real de una pregunta."""
    nota_10 = puntaje_escala(valor)
    if nota_10 is None:
        return None
    return round((nota_10 / 10.0) * maximo, 2)


def _nota_interna_nueva(interno):
    if any(getattr(interno, campo, None) is None for campo in PESOS_INTERNOS):
        return None
    aportes = {campo: puntos_por_pregunta(6 - getattr(interno, campo) if campo == "registra_inconsistencias" else getattr(interno, campo), peso)
               for campo, peso in PESOS_INTERNOS.items()}
    total = round(sum(aportes.values()), 2)
    return {
        "cumplimiento_interno": puntaje_escala(interno.publica_reportes_tiempo),
        "calidad_interna": puntaje_escala(interno.resuelve_incidencias_tiempo),
        "autonomia": puntaje_escala(interno.solicita_datos_tiempo),
        "prevencion_comunicacion": puntaje_escala(interno.comunica_incidencias_tiempo),
        "mejora_continua": puntaje_escala(interno.capacita_actualizaciones),
        "aportes_internos": aportes, "nota_interna": total,
        "porcentaje_interno": round(total / 45 * 100, 2),
        "modelo_interno": "9_preguntas_45",
    }


def _nota_alicorp_nueva(alicorp):
    if any(getattr(alicorp, campo, None) is None for campo in PESOS_ALICORP):
        return None
    aportes = {campo: puntos_por_pregunta(6 - getattr(alicorp, campo) if campo == "registra_inconsistencias" else getattr(alicorp, campo), peso)
               for campo, peso in PESOS_ALICORP.items()}
    total = round(sum(aportes.values()), 2)
    return {**{campo: puntaje_escala(getattr(alicorp, campo))
               for campo in PESOS_ALICORP},
            "aportes_alicorp": aportes, "nota_alicorp": total,
            "porcentaje_alicorp": round(total/55*100,2),
            "modelo_alicorp": "5_preguntas_55"}


def calcular_resultado(analista, periodo, Reporte, EncuestaInterna, EncuestaAlicorp):
    """Calcula el puntaje vigente del IC sobre una base total de 100 puntos.

    La evaluación interna aporta como máximo 45 puntos y Alicorp 55 puntos.
    Las evaluaciones pendientes aportan provisionalmente 90% de su máximo.
    """

    asignados = Reporte.query.filter_by(
        analista_id=analista.id, periodo=periodo, activo=True
    ).count()
    interno = EncuestaInterna.query.filter_by(
        analista_id=analista.id, periodo=periodo
    ).first()
    alicorp = EncuestaAlicorp.query.filter_by(
        analista_id=analista.id, periodo=periodo
    ).first()

    resultado = {
        "analista": analista,
        "periodo": periodo,
        "asignados": asignados,
        "interno_completo": interno is not None and _nota_interna_nueva(interno) is not None,
        "alicorp_completo": alicorp is not None and _nota_alicorp_nueva(alicorp) is not None,
        "max_interno": PUNTAJE_MAX_INTERNO,
        "max_alicorp": PUNTAJE_MAX_ALICORP,
        "max_total": PUNTAJE_MAX_TOTAL,
    }

    if interno:
        datos_internos = _nota_interna_nueva(interno)
        resultado.update(datos_internos or {"nota_interna": None, "modelo_interno": "historico_sin_respuestas_vigentes", "aportes_internos": None})
    else:
        resultado.update(
            cumplimiento_interno=None,
            calidad_interna=None,
            autonomia=None,
            prevencion_comunicacion=None,
            mejora_continua=None,
            aportes_internos=None,
            nota_interna=None,
            porcentaje_interno=None,
            modelo_interno=None,
        )

    if alicorp:
        datos_alicorp = _nota_alicorp_nueva(alicorp)
        resultado.update(datos_alicorp or {"nota_alicorp": None, "modelo_alicorp": "historico_sin_respuestas_vigentes", "aportes_alicorp": None})
    else:
        resultado.update(
            solicita_datos_tiempo=None,
            envia_validar_plazo=None,
            publica_reportes_tiempo=None,
            participa_reuniones=None,
            comunica_incidencias_tiempo=None,
            resuelve_incidencias_tiempo=None,
            capacita_actualizaciones=None,
            comunica_status_tiempo=None,
            aportes_alicorp=None,
            nota_alicorp=None,
            porcentaje_alicorp=None,
            modelo_alicorp=None,
        )

    evaluaciones = int(resultado["interno_completo"]) + int(resultado["alicorp_completo"])
    base_interna = resultado.get("nota_interna") if resultado.get("nota_interna") is not None else PUNTAJE_MAX_INTERNO * 0.9
    base_alicorp = resultado.get("nota_alicorp") if resultado.get("nota_alicorp") is not None else PUNTAJE_MAX_ALICORP * 0.9
    nota_final = round(base_interna + base_alicorp, 2)

    if evaluaciones == 0:
        estado = "Sin evaluar"
    elif nota_final >= 90.0:
        estado = "Excelente"
    elif nota_final >= 75.0:
        estado = "Cumple"
    elif nota_final >= 60.0:
        estado = "En desarrollo"
    else:
        estado = "Requiere mejora"

    resultado.update(
        nota_final=nota_final,
        estado=estado,
        evaluaciones_realizadas=evaluaciones,
        evaluacion_completa=evaluaciones == 2,
        progreso_evaluacion=f"{evaluaciones}/2",
        puntaje_base_interna=base_interna,
        puntaje_base_alicorp=base_alicorp,
    )
    return resultado
