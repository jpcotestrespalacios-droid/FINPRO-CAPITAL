"""
Configuración del sistema RADIAN API
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "RADIAN API"
    SECRET_KEY: str = "tu-clave-secreta-aqui-cambiar-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS — lista de orígenes permitidos (separados por coma en .env)
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Base de datos (Supabase PostgreSQL)
    DATABASE_URL: str = "sqlite:///./radian.db"  # Solo para desarrollo local

    # Supabase
    SUPABASE_URL: str = "https://ucacmeyfybjdntieudsm.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""  # Nunca exponer — solo en variables de entorno

    # DIAN - Ambiente de Pruebas (Habilitación)
    DIAN_AMBIENTE: str = "2"  # 1=Producción, 2=Pruebas

    # URLs DIAN Webservices
    DIAN_WS_RADIAN: str = "https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc"  # Habilitación
    # DIAN_WS_RADIAN: str = "https://vpfe.dian.gov.co/WcfDianCustomerServices.svc"  # Producción

    DIAN_WS_RADIAN_WSDL: str = "https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl"

    # Certificado digital (firma XML)
    CERT_PATH: str = "./certs/certificado.p12"
    CERT_PASSWORD: str = "password-certificado"

    # Email — Resend (resend.com — 3 000 emails/mes gratis)
    # Obtener en: https://resend.com/api-keys
    RESEND_API_KEY: str = ""

    # Cron jobs — clave para proteger los endpoints /api/v1/notificaciones/cron/*
    # Generar con: python -c "import secrets; print(secrets.token_hex(32))"
    CRON_API_KEY: str = ""

    # NIT empresa
    NIT_EMPRESA: str = "900000000"
    RAZON_SOCIAL: str = "TU EMPRESA SAS"

    # Prefijos RADIAN
    PREFIJO_CESION: str = "CES"

    # Identificador de software registrado en DIAN (fijo por proveedor, no aleatorio)
    SOFTWARE_ID: str = "software-id-registrado-dian"

    # Clave técnica para cálculo del CUDE (asignada por la DIAN al registrar el software)
    CLAVE_TECNICA_DIAN: str = "fc8eac422eba16e22ffd8c6f94b3f40a6e38162c"

    # Wompi — pasarela de pagos Colombia (https://wompi.com)
    # Obtener en: https://dashboard.wompi.co → Desarrolladores → Llaves API
    WOMPI_PUBLIC_KEY: str = ""   # pub_test_... o pub_prod_...
    WOMPI_PRIVATE_KEY: str = ""  # prv_test_... o prv_prod_...
    WOMPI_INTEGRITY_KEY: str = "" # Para firmar transacciones
    WOMPI_EVENTS_KEY: str = ""    # Para verificar webhooks

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
