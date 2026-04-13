"""
routers/pagos.py
Integración Wompi — suscripciones y control de límites de cesiones.

Endpoints:
  GET    /planes                   — listar planes y precios
  POST   /iniciar-pago             — generar link de pago Wompi (checkout widget)
  POST   /webhook                  — recibir confirmación de pago de Wompi
  GET    /suscripcion              — estado de suscripción del usuario
  GET    /verificar-limite         — verificar si puede ceder (para uso interno)
  GET    /historial                — historial de pagos
"""
import hashlib
import hmac
import json
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel

from supabase_db import get_sb
from routers.autenticacion import get_current_user
from config import settings

router = APIRouter()

# ─── Configuración de planes ──────────────────────────────────────────────────

PLANES = {
    "starter": {
        "nombre": "Starter",
        "precio_cop": 0,
        "max_cesiones": 5,
        "descripcion": "5 cesiones/mes gratis — ideal para comenzar",
        "caracteristicas": [
            "5 cesiones mensuales",
            "Portal del deudor",
            "Notificaciones email",
            "Soporte por email",
        ],
    },
    "professional": {
        "nombre": "Professional",
        "precio_cop": 149_000,
        "max_cesiones": 50,
        "descripcion": "50 cesiones/mes — para empresas en crecimiento",
        "caracteristicas": [
            "50 cesiones mensuales",
            "Multi-usuario (hasta 5 miembros)",
            "Reportes Excel avanzados",
            "Soporte prioritario",
            "API access",
        ],
    },
    "enterprise": {
        "nombre": "Enterprise",
        "precio_cop": 490_000,
        "max_cesiones": 9999,
        "descripcion": "Cesiones ilimitadas — para grandes volúmenes",
        "caracteristicas": [
            "Cesiones ilimitadas",
            "Miembros ilimitados",
            "SLA 99.9%",
            "Manager dedicado",
            "Integraciones custom",
        ],
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_o_crear_suscripcion(sb, usuario_id: int) -> dict:
    """Obtiene la suscripción activa del usuario, o crea una starter gratuita."""
    res = sb.table("suscripciones").select("*").eq("usuario_id", usuario_id).eq(
        "estado", "ACTIVA"
    ).order("created_at", desc=True).limit(1).execute()

    if res.data:
        return res.data[0]

    # Crear suscripción starter gratuita
    nueva = sb.table("suscripciones").insert({
        "usuario_id": usuario_id,
        "plan": "starter",
        "estado": "ACTIVA",
        "max_cesiones": 5,
        "cesiones_usadas": 0,
        "periodo_inicio": date.today().isoformat(),
        "periodo_fin": (date.today() + timedelta(days=30)).isoformat(),
    }).execute()
    return nueva.data[0]


def verificar_limite_cesiones(sb, usuario_id: int) -> dict:
    """
    Verifica si el usuario puede crear otra cesión este mes.
    Retorna dict con 'puede_ceder', 'usadas', 'limite', 'plan'.
    """
    sus = _get_o_crear_suscripcion(sb, usuario_id)

    # Reiniciar contador si el período venció
    hoy = date.today().isoformat()
    if sus.get("periodo_fin") and hoy > sus["periodo_fin"]:
        sb.table("suscripciones").update({
            "cesiones_usadas": 0,
            "periodo_inicio": hoy,
            "periodo_fin": (date.today() + timedelta(days=30)).isoformat(),
        }).eq("id", sus["id"]).execute()
        sus["cesiones_usadas"] = 0

    puede = sus["cesiones_usadas"] < sus["max_cesiones"]
    return {
        "puede_ceder": puede,
        "usadas": sus["cesiones_usadas"],
        "limite": sus["max_cesiones"],
        "plan": sus["plan"],
        "suscripcion_id": sus["id"],
    }


def incrementar_uso_cesion(sb, usuario_id: int) -> None:
    """Incrementa el contador de cesiones usadas en la suscripción activa."""
    sus = _get_o_crear_suscripcion(sb, usuario_id)
    sb.table("suscripciones").update({
        "cesiones_usadas": sus["cesiones_usadas"] + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", sus["id"]).execute()


def _verificar_firma_wompi(payload_str: str, checksum_header: str) -> bool:
    """Verifica la firma del webhook de Wompi usando HMAC-SHA256."""
    if not hasattr(settings, "WOMPI_EVENTS_KEY") or not settings.WOMPI_EVENTS_KEY:
        return True  # En dev sin clave, aceptar todo
    expected = hmac.new(
        settings.WOMPI_EVENTS_KEY.encode(),
        payload_str.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, checksum_header or "")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/planes", summary="Listar planes y precios")
async def listar_planes():
    return {"planes": PLANES}


@router.post("/iniciar-pago", summary="Generar datos para pago Wompi (checkout)")
async def iniciar_pago(plan: str, current_user: dict = Depends(get_current_user)):
    if plan not in PLANES:
        raise HTTPException(400, f"Plan inválido. Opciones: {list(PLANES)}")
    if PLANES[plan]["precio_cop"] == 0:
        raise HTTPException(400, "El plan Starter es gratuito — no requiere pago")

    sb = get_sb()
    referencia = f"FPC-{current_user['id']}-{uuid.uuid4().hex[:8].upper()}"
    monto_centavos = PLANES[plan]["precio_cop"] * 100  # Wompi trabaja en centavos

    # Calcular firma de integridad Wompi
    # Fórmula: SHA-256 de "{referencia}{monto_centavos}COP{integrity_key}"
    integrity_key = getattr(settings, "WOMPI_INTEGRITY_KEY", "")
    cadena = f"{referencia}{monto_centavos}COP{integrity_key}"
    firma = hashlib.sha256(cadena.encode()).hexdigest()

    # Registrar pago pendiente
    sb.table("pagos").insert({
        "usuario_id": current_user["id"],
        "referencia": referencia,
        "monto": PLANES[plan]["precio_cop"],
        "moneda": "COP",
        "estado": "PENDIENTE",
        "plan_comprado": plan,
    }).execute()

    public_key = getattr(settings, "WOMPI_PUBLIC_KEY", "")
    return {
        "referencia": referencia,
        "monto_centavos": monto_centavos,
        "moneda": "COP",
        "plan": plan,
        "firma_integridad": firma,
        "wompi_public_key": public_key,
        "redirect_url": "/pago-exitoso",
        "instrucciones": "Usa estos datos para inicializar el widget de Wompi en el frontend.",
        "widget_script": "https://checkout.wompi.co/widget.js",
    }


@router.post("/webhook", summary="Webhook de confirmación de pago Wompi", include_in_schema=False)
async def webhook_wompi(request: Request, x_event_checksum: Optional[str] = Header(None)):
    body_bytes = await request.body()
    body_str = body_bytes.decode()

    if not _verificar_firma_wompi(body_str, x_event_checksum or ""):
        raise HTTPException(401, "Firma de webhook inválida")

    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(400, "Payload inválido")

    evento = payload.get("event", "")
    if evento != "transaction.updated":
        return {"ok": True, "ignorado": True}

    data = payload.get("data", {}).get("transaction", {})
    referencia = data.get("reference", "")
    wompi_id = data.get("id", "")
    estado_wompi = data.get("status", "")  # APPROVED, DECLINED, VOIDED, ERROR

    estado_map = {
        "APPROVED": "APROBADO",
        "DECLINED": "RECHAZADO",
        "VOIDED": "VOIDED",
        "ERROR": "ERROR",
    }
    estado_local = estado_map.get(estado_wompi, "ERROR")

    sb = get_sb()
    pago_res = sb.table("pagos").select("*").eq("referencia", referencia).execute()
    if not pago_res.data:
        return {"ok": True, "ignorado": True, "motivo": "referencia no encontrada"}

    pago = pago_res.data[0]

    sb.table("pagos").update({
        "wompi_transaction_id": wompi_id,
        "estado": estado_local,
        "wompi_payload": payload,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", pago["id"]).execute()

    # Si fue aprobado, actualizar/crear suscripción
    if estado_local == "APROBADO" and pago.get("plan_comprado"):
        plan = pago["plan_comprado"]
        max_ces = PLANES.get(plan, {}).get("max_cesiones", 5)
        usuario_id = pago["usuario_id"]

        # Cancelar suscripción activa anterior
        sb.table("suscripciones").update({
            "estado": "CANCELADA",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("usuario_id", usuario_id).eq("estado", "ACTIVA").execute()

        # Crear nueva suscripción
        nueva_sus = sb.table("suscripciones").insert({
            "usuario_id": usuario_id,
            "plan": plan,
            "estado": "ACTIVA",
            "max_cesiones": max_ces,
            "cesiones_usadas": 0,
            "periodo_inicio": date.today().isoformat(),
            "periodo_fin": (date.today() + timedelta(days=30)).isoformat(),
        }).execute()

        # Vincular pago a suscripción
        if nueva_sus.data:
            sb.table("pagos").update({
                "suscripcion_id": nueva_sus.data[0]["id"]
            }).eq("id", pago["id"]).execute()

        # Email de confirmación
        try:
            usuario_res = sb.table("usuarios").select("email,nombre").eq("id", usuario_id).execute()
            if usuario_res.data:
                u = usuario_res.data[0]
                from notifications import send_email
                send_email(
                    u["email"],
                    f"Pago confirmado — Plan {plan.capitalize()} activado",
                    f"""<div style="font-family:-apple-system,Arial,sans-serif;max-width:560px;margin:0 auto;padding:20px">
                    <div style="background:#0B1829;padding:20px;border-radius:10px 10px 0 0">
                      <h2 style="color:#fff;margin:0">⚡ FinPro Capital — Pago confirmado</h2>
                    </div>
                    <div style="background:#fff;padding:28px;border:1px solid #E4E9F0;border-top:none">
                      <p>Hola <strong>{u['nombre'].split()[0]}</strong>,</p>
                      <p>Tu pago fue confirmado. El plan <strong>{plan.capitalize()}</strong>
                         está activo con <strong>{max_ces} cesiones/mes</strong>.</p>
                      <p style="font-size:12px;color:#64748B">Referencia: {referencia}</p>
                    </div>
                    </div>""",
                )
        except Exception as e:
            print(f"[pagos] Error email confirmacion: {e}")

    return {"ok": True}


@router.get("/suscripcion", summary="Estado de mi suscripción")
async def mi_suscripcion(current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    sus = _get_o_crear_suscripcion(sb, current_user["id"])
    limite = verificar_limite_cesiones(sb, current_user["id"])
    plan_info = PLANES.get(sus["plan"], {})
    return {
        **sus,
        "puede_ceder": limite["puede_ceder"],
        "plan_nombre": plan_info.get("nombre", sus["plan"]),
        "precio_cop": plan_info.get("precio_cop", 0),
    }


@router.get("/verificar-limite", summary="Verificar si puedo crear una cesión")
async def verificar_limite(current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    return verificar_limite_cesiones(sb, current_user["id"])


@router.get("/historial", summary="Historial de pagos")
async def historial_pagos(skip: int = 0, limit: int = 50, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    res = sb.table("pagos").select("*").eq(
        "usuario_id", current_user["id"]
    ).order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    return {"total": len(res.data), "pagos": res.data or []}
