from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Canal(db.Model):
    """Catálogo administrable de canales; mantiene compatibilidad con campos canal existentes."""
    __tablename__ = "canales"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Analista(db.Model):
    __tablename__ = "analistas"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False)
    canal = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(180))
    correo_controller = db.Column("correo_coordinador", db.String(180))
    activo = db.Column(db.Boolean, nullable=False, default=True)
    baja_periodo = db.Column(db.String(7))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Controller(db.Model):
    """Controller responsable de completar la evaluación interna del IC.

    La tabla física se mantiene como 'coordinadores' para compatibilidad con
    instalaciones existentes del proyecto.
    """

    __tablename__ = "coordinadores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False)
    correo = db.Column(db.String(180), nullable=False, unique=True)
    canal = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)




class CoordinadorCanal(db.Model):
    """Coordinador que recibe alertas de analistas según el canal asignado."""

    __tablename__ = "coordinadores_alerta"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False)
    correo = db.Column(db.String(180), nullable=False, unique=True)
    canal = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class CorreoAcceso(db.Model):
    __tablename__ = "correos_acceso"
    id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(180), nullable=False, unique=True)
    rol = db.Column(db.String(20), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)


class Reporte(db.Model):
    __tablename__ = "reportes"
    id = db.Column(db.Integer, primary_key=True)
    analista_id = db.Column(db.Integer, db.ForeignKey("analistas.id"), nullable=False)
    periodo = db.Column(db.String(7), nullable=False, index=True)
    indicador = db.Column(db.String(160), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    analista = db.relationship("Analista", backref="reportes")

class ReporteAnalistaExcel(db.Model):
    __tablename__ = "reportes_analistas_excel"

    id = db.Column(db.Integer, primary_key=True)
    periodo = db.Column(db.String(7), nullable=False, index=True)
    canal = db.Column(db.String(100))
    programa = db.Column(db.String(150))
    analista = db.Column(db.String(160))
    nombre_reporte = db.Column(db.String(500))
    kpi = db.Column(db.Text)
    frecuencia = db.Column(db.String(100))
    contacto_comercial = db.Column(db.String(200))
    contacto_interno = db.Column(db.String(200))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)


class EncuestaInterna(db.Model):
    __tablename__ = "encuestas_internas"
    id = db.Column(db.Integer, primary_key=True)
    analista_id = db.Column(db.Integer, db.ForeignKey("analistas.id"), nullable=False)
    periodo = db.Column(db.String(7), nullable=False, index=True)
    evaluador = db.Column(db.String(160), nullable=False)


    publica_reportes_tiempo = db.Column(db.Integer)
    participa_reuniones = db.Column(db.Integer)
    comunica_incidencias_tiempo = db.Column(db.Integer)
    resuelve_incidencias_tiempo = db.Column(db.Integer)
    solicita_datos_tiempo = db.Column(db.Integer)
    envia_validar_plazo = db.Column(db.Integer)
    capacita_actualizaciones = db.Column(db.Integer)
    comunica_status_tiempo = db.Column(db.Integer)
    registra_inconsistencias = db.Column(db.Integer)
    propone_soluciones = db.Column(db.Integer)
    evaluador_correo = db.Column(db.String(180))


    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    analista = db.relationship("Analista", backref="encuestas_internas")
    __table_args__ = (
        db.UniqueConstraint("analista_id", "periodo", name="uq_interna_analista_periodo"),
    )


class EncuestaAlicorp(db.Model):
    __tablename__ = "encuestas_alicorp"
    id = db.Column(db.Integer, primary_key=True)
    analista_id = db.Column(db.Integer, db.ForeignKey("analistas.id"), nullable=False)
    periodo = db.Column(db.String(7), nullable=False, index=True)
    evaluador = db.Column(db.String(160), nullable=False)

    publica_reportes_tiempo = db.Column(db.Integer)
    participa_reuniones = db.Column(db.Integer)
    comunica_incidencias_tiempo = db.Column(db.Integer)
    resuelve_incidencias_tiempo = db.Column(db.Integer)
    comunica_status_tiempo = db.Column(db.Integer)
    verifica_consistencia_datos = db.Column(db.Integer)
    propone_soluciones = db.Column(db.Integer)
    registra_inconsistencias = db.Column(db.Integer)
    evaluador_correo = db.Column(db.String(180))

    comentario = db.Column(db.Text)


    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    analista = db.relationship("Analista", backref="encuestas_alicorp")
    __table_args__ = (
        db.UniqueConstraint("analista_id", "periodo", name="uq_alicorp_analista_periodo"),
    )


class Alerta(db.Model):
    __tablename__ = "alertas"
    id = db.Column(db.Integer, primary_key=True)
    analista_id = db.Column(db.Integer, db.ForeignKey("analistas.id"), nullable=False)
    periodo = db.Column(db.String(7), nullable=False)
    tipo = db.Column(db.String(80), nullable=False)
    motivo = db.Column(db.String(500), nullable=False)
    enviada = db.Column(db.Boolean, nullable=False, default=False)
    enviada_en = db.Column(db.DateTime)
    __table_args__ = (
        db.UniqueConstraint("analista_id", "periodo", "tipo", name="uq_alerta_unica"),
    )


class EntregaAlerta(db.Model):
    __tablename__ = "entregas_alertas"
    id = db.Column(db.Integer, primary_key=True)
    alerta_id = db.Column(db.Integer, db.ForeignKey("alertas.id"), nullable=False)
    controller_id = db.Column("coordinador_id", db.Integer, db.ForeignKey("coordinadores.id"), nullable=False)
    enviada_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("alerta_id", "coordinador_id", name="uq_entrega_alerta"),
    )




class EntregaAlertaCoordinador(db.Model):
    """Registro de alertas ya enviadas a Coordinadores de canal."""

    __tablename__ = "entregas_alertas_coordinador"
    id = db.Column(db.Integer, primary_key=True)
    alerta_id = db.Column(db.Integer, db.ForeignKey("alertas.id"), nullable=False)
    coordinador_id = db.Column(db.Integer, db.ForeignKey("coordinadores_alerta.id"), nullable=False)
    enviada_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("alerta_id", "coordinador_id", name="uq_entrega_alerta_coordinador"),
    )


# Alias útil para el nuevo módulo de Coordinadores.
Coordinador = CoordinadorCanal
