"""
Modelos de base de datos - SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class EstadoFactura(str, enum.Enum):
    EMITIDA = "EMITIDA"
    VALIDADA_DIAN = "VALIDADA_DIAN"
    EN_CESION = "EN_CESION"
    CEDIDA = "CEDIDA"
    PAGADA = "PAGADA"
    RECHAZADA = "RECHAZADA"


class EstadoCesion(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADA_DIAN = "ENVIADA_DIAN"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    nombre = Column(String)
    nit = Column(String, index=True)
    hashed_password = Column(String)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    facturas = relationship("Factura", back_populates="emisor")


class Factura(Base):
    __tablename__ = "facturas"
    id = Column(Integer, primary_key=True, index=True)
    cufe = Column(String, unique=True, index=True)  # Código Único Factura Electrónica
    numero = Column(String, index=True)
    prefijo = Column(String)
    
    # Emisor
    emisor_id = Column(Integer, ForeignKey("usuarios.id"))
    emisor_nit = Column(String)
    emisor_nombre = Column(String)
    
    # Adquiriente
    adquiriente_nit = Column(String, index=True)
    adquiriente_nombre = Column(String)
    
    # Valores
    valor_base = Column(Float)
    valor_iva = Column(Float)
    valor_total = Column(Float)
    
    # Fechas
    fecha_emision = Column(DateTime)
    fecha_vencimiento = Column(DateTime)
    
    # Estado
    estado = Column(Enum(EstadoFactura), default=EstadoFactura.EMITIDA)
    es_titulo_valor = Column(Boolean, default=False)  # Endosable para RADIAN
    
    # XML DIAN
    xml_firmado = Column(Text)
    xml_respuesta_dian = Column(Text)
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    emisor = relationship("Usuario", back_populates="facturas")
    cesiones = relationship("Cesion", back_populates="factura")


class Cesion(Base):
    __tablename__ = "cesiones"
    id = Column(Integer, primary_key=True, index=True)
    
    factura_id = Column(Integer, ForeignKey("facturas.id"))
    cufe_factura = Column(String, index=True)
    
    # Cedente (quien cede)
    cedente_nit = Column(String)
    cedente_nombre = Column(String)
    
    # Cesionario (quien recibe)
    cesionario_nit = Column(String)
    cesionario_nombre = Column(String)
    
    # Deudor
    deudor_nit = Column(String)
    deudor_nombre = Column(String)
    
    # Valor cedido
    valor_cesion = Column(Float)
    
    # RADIAN
    cude = Column(String, unique=True, index=True)  # Código Único Documento Electrónico
    numero_cesion = Column(String)
    fecha_cesion = Column(DateTime)
    
    # Estado
    estado = Column(Enum(EstadoCesion), default=EstadoCesion.PENDIENTE)
    
    # XMLs
    xml_evento = Column(Text)
    xml_respuesta_dian = Column(Text)
    descripcion_estado = Column(String)
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    factura = relationship("Factura", back_populates="cesiones")
