"""
Router de Facturas
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from database import get_db, Factura, EstadoFactura, Usuario
from routers.autenticacion import get_current_user

router = APIRouter()

ESTADOS_VALIDOS = {e.value for e in EstadoFactura}


class FacturaCreate(BaseModel):
    cufe: str
    numero: str
    prefijo: Optional[str] = "FV"
    emisor_nit: str
    emisor_nombre: str
    adquiriente_nit: str
    adquiriente_nombre: str
    valor_base: float
    valor_iva: float
    valor_total: float
    fecha_emision: datetime
    fecha_vencimiento: datetime


@router.post("/registrar", summary="Registrar factura electrónica")
async def registrar_factura(
    data: FacturaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una factura electrónica ya validada por la DIAN para gestión en RADIAN"""
    if db.query(Factura).filter(Factura.cufe == data.cufe).first():
        raise HTTPException(status_code=400, detail="Factura ya registrada")

    factura = Factura(**data.dict(), emisor_id=current_user.id)
    db.add(factura)
    db.commit()
    db.refresh(factura)
    return {"mensaje": "Factura registrada", "id": factura.id, "cufe": factura.cufe}


@router.put("/{cufe}/habilitar-cesion", summary="Habilitar factura para cesión (título valor)")
async def habilitar_cesion(
    cufe: str,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """
    Marca la factura como título valor endosable.
    Prerequisito: El adquiriente debe haber enviado el evento 032 (Recibo de la factura)
    y el evento 033 (Aceptación expresa).
    """
    factura = db.query(Factura).filter(Factura.cufe == cufe).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    factura.es_titulo_valor = True
    factura.estado = EstadoFactura.VALIDADA_DIAN
    db.commit()
    return {"mensaje": "Factura habilitada como título valor - lista para cesión", "cufe": cufe}


@router.get("/{cufe}", summary="Consultar factura")
async def consultar_factura(
    cufe: str,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    factura = db.query(Factura).filter(Factura.cufe == cufe).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura


@router.get("/", summary="Listar facturas")
async def listar_facturas(
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    if estado and estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Valores permitidos: {sorted(ESTADOS_VALIDOS)}"
        )
    query = db.query(Factura)
    if estado:
        query = query.filter(Factura.estado == estado)
    total = query.count()
    facturas = query.offset(skip).limit(limit).all()
    return {"total": total, "facturas": facturas}
