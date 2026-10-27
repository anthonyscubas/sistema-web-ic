import os
from urllib.parse import quote_plus

def construir_url_sqlserver():
    driver = os.getenv(
        "SQLSERVER_DRIVER",
        "ODBC Driver 17 for SQL Server"
    )
    host = os.getenv(
        "SQLSERVER_HOST",
        r"LAPTOP-ANTHONY"
    )
    database = os.getenv(
        "SQLSERVER_DATABASE",
        "EvaluacionIC"
    )
    trust = os.getenv(
        "SQLSERVER_TRUST_CERTIFICATE",
        "yes"
    )
    cadena = (
        f"DRIVER={{{driver}}};"
        f"SERVER={host};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
        f"Encrypt=yes;"
        f"TrustServerCertificate={trust};"
    )
    return "mssql+pyodbc:///?odbc_connect=" + quote_plus(cadena)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "desarrollo-cambiar-en-produccion")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or construir_url_sqlserver()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

