from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from supabase_db import get_sb
from services.dian_radian import dian_service
from routers.autenticacion import get_current_user

router = APIRouter()


class CesionRequest(BaseModel):
    cufe_factura: str
    cesionario_nit: str
    cesionario_nombre: str
    valor_cesion: float
    descripcion: Optional[str] = "Endoso en propiedad - cesión de factura electrónica"


@router.post("/crear", summary="Ceder una factura electrónica")
async def crear_cesion(data: CesionRequest, current_user: dict = Depends(get_current_user)):
    sb = get_sb()

    fact = sb.table("facturas").select("*").eq("cufe", data.cufe_factura).execute()
    if not fact.data:
        raise HTTPException(404, f"Factura con CUFE {data.cufe_factura} no encontrada")
    factura = fact.data[0]

    if factura["emisor_nit"] != current_user["nit"]:
        raise HTTPException(403, "Solo el emisor de la factura puede realizar la cesión")
    if not factura["es_titulo_valor"]:
        raise HTTPException(400, "La factura no está habilitada como título valor")
    if factura["estado"] == "CEDIDA":
        raise HTTPException(400, "Esta factura ya fue cedida")
    if factura["estado"] == "PAGADA":
        raise HTTPException(400, "Esta factura ya fue pagada, no se puede ceder")

    total = sb.table("cesiones").select("id", count="exact").execute().count or 0
    numero_cesion = f"CES{datetime.now().year}{str(total + 1).zfill(8)}"
    fecha_cesion = datetime.now()

    xml_evento, cude = dian_service.construir_xml_cesion(
        cufe_factura=data.cufe_factura,
        numero_cesion=numero_cesion,
        cedente_nit=factura["emisor_nit"],
        cedente_nombre=factura["emisor_nombre"],
        cesionario_nit=data.cesionario_nit,
        cesionario_nombre=data.cesionario_nombre,
        deudor_nit=factura["adquiriente_nit"],
        deudor_nombre=factura["adquiriente_nombre"],
        valor_cesion=data.valor_cesion,
        fecha_cesion=fecha_cesion,
    )
    xml_firmado = dian_service.firmar_xml(xml_evento)
    respuesta_dian = dian_service.enviar_evento_radian(xml_firmado)

    estado_cesion = "ACEPTADA" if respuesta_dian["exitoso"] else "RECHAZADA"

    result = sb.table("cesiones").insert({
        "factura_id": factura["id"],
        "cufe_factura": data.cufe_factura,
        "cedente_nit": factura["emisor_nit"],
        "cedente_nombre": factura["emisor_nombre"],
        "cesionario_nit": data.cesionario_nit,
        "cesionario_nombre": data.cesionario_nombre,
        "deudor_nit": factura["adquiriente_nit"],
        "deudor_nombre": factura["adquiriente_nombre"],
        "valor_cesion": data.valor_cesion,
        "cude": cude,
        "numero_cesion": numero_cesion,
        "fecha_cesion": fecha_cesion.isoformat(),
        "xml_evento": xml_firmado,
        "xml_respuesta_dian": str(respuesta_dian),
        "estado": estado_cesion,
        "descripcion_estado": respuesta_dian.get("descripcion", ""),
    }).execute()

    if respuesta_dian["exitoso"]:
        sb.table("facturas").update({"estado": "CEDIDA"}).eq("cufe", data.cufe_factura).execute()

    nueva = result.data[0] if result.data else {}
    return {
        "id": nueva.get("id"),
        "cude": cude,
        "cufe_factura": data.cufe_factura,
        "cedente_nit": factura["emisor_nit"],
        "cesionario_nit": data.cesionario_nit,
        "valor_cesion": data.valor_cesion,
        "estado": estado_cesion,
        "fecha_cesion": fecha_cesion,
        "mensaje": "✅ Cesión registrada en RADIAN exitosamente" if respuesta_dian["exitoso"] else f"❌ Error DIAN: {respuesta_dian.get('descripcion')}",
    }


@router.get("/", summary="Listar todas las cesiones del usuario")
async def listar_cesiones(skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    facturas = sb.table("facturas").select("id").eq("emisor_id", current_user["id"]).execute()
    if not facturas.data:
        return {"total": 0, "cesiones": []}
    ids = [f["id"] for f in facturas.data]
    result = sb.table("cesiones").select("*", count="exact").in_("factura_id", ids).order("fecha_cesion", desc=True).range(skip, skip + limit - 1).execute()
    return {"total": result.count or len(result.data), "cesiones": result.data or []}


@router.get("/{cude}/estado", summary="Consultar estado de cesión en DIAN")
async def consultar_estado_cesion(cude: str, current_user: dict = Depends(get_current_user)):
    result = get_sb().table("cesiones").select("*").eq("cude", cude).execute()
    if not result.data:
        raise HTTPException(404, "Cesión no encontrada")
    cesion = result.data[0]
    estado_dian = dian_service.consultar_estado_evento(cude)
    return {
        "cude": cude,
        "estado_local": cesion["estado"],
        "estado_dian": estado_dian,
        "fecha_cesion": cesion["fecha_cesion"],
        "cedente": cesion["cedente_nombre"],
        "cesionario": cesion["cesionario_nombre"],
        "valor": cesion["valor_cesion"],
    }


@router.get("/factura/{cufe}", summary="Ver cesiones de una factura")
async def cesiones_por_factura(cufe: str, current_user: dict = Depends(get_current_user)):
    result = get_sb().table("cesiones").select("*").eq("cufe_factura", cufe).execute()
    cesiones = result.data or []
    return {
        "cufe": cufe,
        "total": len(cesiones),
        "cesiones": [
            {"id": c["id"], "cude": c["cude"], "cedente": c["cedente_nombre"],
             "cesionario": c["cesionario_nombre"], "valor": c["valor_cesion"],
             "estado": c["estado"], "fecha": c["fecha_cesion"]}
            for c in cesiones
        ],
    }


@router.get("/xml/{cude}", summary="Descargar XML del evento de cesión")
async def descargar_xml_cesion(cude: str, current_user: dict = Depends(get_current_user)):
    result = get_sb().table("cesiones").select("xml_evento").eq("cude", cude).execute()
    if not result.data:
        raise HTTPException(404, "Cesión no encontrada")
    return Response(
        content=result.data[0]["xml_evento"],
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=cesion_{cude[:16]}.xml"},
    )
