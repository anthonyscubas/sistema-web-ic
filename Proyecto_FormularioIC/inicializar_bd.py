"""Inicialización automática de la base SQL Server al arrancar Flask."""
import re
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError


def crear_base_si_falta(uri):
    """Se conecta a master y crea la base destino solo si no existe.

    La cuenta de SQL Server debe tener permiso CREATE DATABASE. No borra datos.
    """
    url = make_url(uri)
    if not url.drivername.startswith("mssql"):
        return

    nombre = url.database
    if "odbc_connect" in url.query:
        cadena = url.query["odbc_connect"]
        encontrado = re.search(r"(?i)(?:^|;)\s*DATABASE\s*=\s*([^;]+)", cadena)
        if not encontrado:
            raise RuntimeError("No se encontró DATABASE en la conexión ODBC.")
        nombre = encontrado.group(1).strip()
        cadena_master = re.sub(
            r"(?i)((?:^|;)\s*DATABASE\s*=\s*)[^;]+",
            lambda match: match.group(1) + "master",
            cadena,
            count=1,
        )
        master_url = url.update_query_dict({"odbc_connect": cadena_master})
    else:
        master_url = url.set(database="master")

    if not nombre or not re.fullmatch(r"[\w\- ]{1,128}", nombre, re.UNICODE):
        raise RuntimeError("Nombre de base de datos no válido.")
    motor = create_engine(master_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        with motor.connect() as conexion:
            existe = conexion.execute(text("SELECT DB_ID(:nombre)"), {"nombre": nombre}).scalar()
            if existe is None:
                identificador = "[" + nombre.replace("]", "]]" ) + "]"
                conexion.exec_driver_sql(f"CREATE DATABASE {identificador}")
                print(f"Base de datos {nombre} creada automáticamente.")
            else:
                print(f"Base de datos {nombre} encontrada.")
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "No se pudo comprobar o crear la base de datos automáticamente. "
            "Verifica que la instancia SQL Server sea correcta y que tu usuario "
            "tenga acceso a master y permiso CREATE DATABASE."
        ) from exc
    finally:
        motor.dispose()
