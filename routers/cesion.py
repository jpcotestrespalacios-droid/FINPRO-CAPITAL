import json
import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from supabase_db import get_sb
from services.dian_radian import dian_service
from routers.autenticacion import get_current_user
from notifications import email_cesion_aceptada, email_cesion_rechazada
from routers.notificaciones import get_user_pref
from routers.pagos import verificar_limite_cesiones, incrementar_uso_cesion

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
    if data.valor_cesion <= 0:
        raise HTTPException(400, "El valor de cesión debe ser mayor a cero")
    if data.valor_cesion > factura["valor_total"]:
        raise HTTPException(400, f"El valor de cesión ({data.valor_cesion}) no puede exceder el valor total de la factura ({factura['valor_total']})")

    # Verificar límite de cesiones del plan
    limite = verificar_limite_cesiones(sb, current_user["id"])
    if not limite["puede_ceder"]:
        raise HTTPException(429, f"Límite de cesiones alcanzado ({limite['usadas']}/{limite['limite']}) para el plan {limite['plan']}. Actualiza tu plan en /api/v1/pagos/planes")

    # Número de cesión único basado en UUID para evitar race conditions en concurrencia
    numero_cesion = f"CES{datetime.now().year}{uuid.uuid4().hex[:8].upper()}"
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
        "xml_respuesta_dian": json.dumps(respuesta_dian, default=str),
        "estado": estado_cesion,
        "descripcion_estado": respuesta_dian.get("descripcion", ""),
    }).execute()

    if respuesta_dian["exitoso"]:
        sb.table("facturas").update({"estado": "CEDIDA"}).eq("cufe", data.cufe_factura).execute()
        incrementar_uso_cesion(sb, current_user["id"])

        # Auto-notificar al deudor (Ley 1231/2008) — no bloquea el flujo
        try:
            import secrets
            token_deudor = secrets.token_urlsafe(32)
            url_base = f"https://{factura.get('emisor_nit', 'app')}.finprocapital.co"
            sb.table("notificaciones_deudor").insert({
                "cude": cude,
                "deudor_nit": factura["adquiriente_nit"],
                "deudor_email": factura.get("adquiriente_email", ""),
                "estado": "ENVIADA" if factura.get("adquiriente_email") else "FALLIDA",
                "token_confirmacion": token_deudor,
                "enviado_en": fecha_cesion.isoformat(),
            }).execute()

            if factura.get("adquiriente_email"):
                from notifications import send_email
                import html as _html
                url_confirmar = f"{url_base}/api/v1/deudor/confirmar/{token_deudor}"
                send_email(
                    factura["adquiriente_email"],
                    f"Notificación legal de cesión — {_html.escape(factura['emisor_nombre'])}",
                    f"""<div style="font-family:-apple-system,Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
                    <div style="background:#0B1829;padding:20px;border-radius:10px 10px 0 0">
                      <h2 style="color:#fff;margin:0;font-size:17px">⚡ FinPro Capital — Notificación Legal</h2>
                    </div>
                    <div style="background:#fff;padding:28px;border:1px solid #E4E9F0;border-top:none">
                      <div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;padding:12px 16px;margin-bottom:20px">
                        <strong style="color:#92400E">⚠ Aviso legal — Ley 1231 de 2008</strong>
                      </div>
                      <p style="color:#374151">Estimado/a <strong>{_html.escape(factura['adquiriente_nombre'])}</strong>,</p>
                      <p style="color:#374151;font-size:14px"><strong>{_html.escape(factura['emisor_nombre'])}</strong>
                        ha cedido en RADIAN el crédito de la factura a
                        <strong>{_html.escape(data.cesionario_nombre)}</strong>.</p>
                      <p style="color:#374151;font-size:14px">
                        A partir de ahora, los pagos deben realizarse únicamente a
                        <strong>{_html.escape(data.cesionario_nombre)}</strong>.
                      </p>
                      <div style="text-align:center;margin:28px 0">
                        <a href="{url_confirmar}"
                           style="background:#1A4FD6;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;display:inline-block">
                          ✓ Confirmar recepción
                        </a>
                      </div>
                    </div>
                    </div>""",
                )
        except Exception as _e:
            print(f"[cesion] Aviso auto-notificacion deudor: {_e}")

    # Enviar email de notificación (no bloquea el flujo)
    try:
        pref_key = "notify_cesion_aceptada" if respuesta_dian["exitoso"] else "notify_cesion_rechazada"
        if get_user_pref(sb, current_user["id"], pref_key):
            factura_num = f"{factura.get('prefijo', 'FV')}-{factura.get('numero', '')}"
            if respuesta_dian["exitoso"]:
                email_cesion_aceptada(
                    current_user["email"], current_user["nombre"],
                    cude, data.valor_cesion,
                    factura["emisor_nombre"], data.cesionario_nombre, factura_num,
                )
            else:
                email_cesion_rechazada(
                    current_user["email"], current_user["nombre"],
                    cude, data.valor_cesion,
                    respuesta_dian.get("descripcion", ""), factura_num,
                )
    except Exception:
        pass  # no interrumpir el flujo principal

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
