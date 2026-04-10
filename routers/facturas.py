from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from supabase_db import get_sb
from routers.autenticacion import get_current_user

router = APIRouter()

ESTADOS_VALIDOS = {"EMITIDA", "VALIDADA_DIAN", "EN_CESION", "CEDIDA", "PAGADA", "RECHAZADA"}


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
async def registrar_factura(data: FacturaCreate, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    if sb.table("facturas").select("id").eq("cufe", data.cufe).execute().data:
        raise HTTPException(status_code=400, detail="Factura ya registrada")
    result = sb.table("facturas").insert({
        "cufe": data.cufe,
        "numero": data.numero,
        "prefijo": data.prefijo,
        "emisor_id": current_user["id"],
        "emisor_nit": data.emisor_nit,
        "emisor_nombre": data.emisor_nombre,
        "adquiriente_nit": data.adquiriente_nit,
        "adquiriente_nombre": data.adquiriente_nombre,
        "valor_base": data.valor_base,
        "valor_iva": data.valor_iva,
        "valor_total": data.valor_total,
        "fecha_emision": data.fecha_emision.isoformat(),
        "fecha_vencimiento": data.fecha_vencimiento.isoformat(),
        "estado": "EMITIDA",
        "es_titulo_valor": False,
    }).execute()
    factura = result.data[0] if result.data else {}
    return {"mensaje": "Factura registrada", "id": factura.get("id"), "cufe": data.cufe}


@router.put("/{cufe}/habilitar-cesion", summary="Habilitar factura para cesión")
async def habilitar_cesion(cufe: str, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    if not sb.table("facturas").select("id").eq("cufe", cufe).execute().data:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    sb.table("facturas").update({"es_titulo_valor": True, "estado": "VALIDADA_DIAN"}).eq("cufe", cufe).execute()
    return {"mensaje": "Factura habilitada como título valor - lista para cesión", "cufe": cufe}


@router.get("/{cufe}", summary="Consultar factura")
async def consultar_factura(cufe: str, current_user: dict = Depends(get_current_user)):
    result = get_sb().table("facturas").select("*").eq("cufe", cufe).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return result.data[0]


@router.get("/", summary="Listar facturas")
async def listar_facturas(
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    if estado and estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Permitidos: {sorted(ESTADOS_VALIDOS)}")
    sb = get_sb()
    query = sb.table("facturas").select("*", count="exact").eq("emisor_id", current_user["id"])
    if estado:
        query = query.eq("estado", estado)
    result = query.range(skip, skip + limit - 1).execute()
    return {"total": result.count or len(result.data), "facturas": result.data}
