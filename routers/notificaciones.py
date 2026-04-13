"""
routers/notificaciones.py
Preferencias de email por usuario + endpoints cron protegidos con API key.

Tabla Supabase requerida (ver migrations/email_preferences.sql):
  email_preferences(user_id, notify_bienvenida, notify_cesion_aceptada,
                    notify_cesion_rechazada, notify_vencimiento_7d,
                    notify_vencimiento_vencida, notify_reporte_mensual)
"""
import os
import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from supabase_db import get_sb
from routers.autenticacion import get_current_user
from notifications import (
    email_vencimiento_7dias,
    email_facturas_vencidas,
    email_reporte_mensual,
)

router = APIRouter()
logger = logging.getLogger(__name__)

CRON_API_KEY = os.getenv("CRON_API_KEY", "")

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


# ── SCHEMAS ────────────────────────────────────────────────────────────────────

class PreferenciasUpdate(BaseModel):
    notify_bienvenida: Optional[bool] = None
    notify_cesion_aceptada: Optional[bool] = None
    notify_cesion_rechazada: Optional[bool] = None
    notify_vencimiento_7d: Optional[bool] = None
    notify_vencimiento_vencida: Optional[bool] = None
    notify_reporte_mensual: Optional[bool] = None


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _get_or_create_prefs(sb, user_id: str) -> dict:
    """Obtiene o crea el registro de preferencias del usuario (todos true por defecto)."""
    result = sb.table("email_preferences").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]
    defaults = {
        "user_id": user_id,
        "notify_bienvenida": True,
        "notify_cesion_aceptada": True,
        "notify_cesion_rechazada": True,
        "notify_vencimiento_7d": True,
        "notify_vencimiento_vencida": True,
        "notify_reporte_mensual": True,
    }
    new = sb.table("email_preferences").insert(defaults).execute()
    return new.data[0] if new.data else defaults


def get_user_pref(sb, user_id: str, key: str) -> bool:
    """Retorna True si el usuario tiene habilitada la notificación `key`.
    Falla silenciosamente retornando True (enviar por defecto)."""
    try:
        prefs = _get_or_create_prefs(sb, user_id)
        return bool(prefs.get(key, True))
    except Exception as exc:
        logger.warning("No se pudo leer pref %s para %s: %s", key, user_id, exc)
        return True


def _check_cron_key(key: Optional[str]) -> None:
    if not CRON_API_KEY:
        raise HTTPException(status_code=500, detail="CRON_API_KEY no configurada en el servidor")
    if key != CRON_API_KEY:
        raise HTTPException(status_code=403, detail="API key de cron inválida")


# ── PREFERENCIAS ───────────────────────────────────────────────────────────────

@router.get("/preferencias", summary="Obtener preferencias de notificaciones del usuario")
async def get_preferencias(current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    prefs = _get_or_create_prefs(sb, current_user["id"])
    return {
        "notify_bienvenida":         prefs.get("notify_bienvenida", True),
        "notify_cesion_aceptada":    prefs.get("notify_cesion_aceptada", True),
        "notify_cesion_rechazada":   prefs.get("notify_cesion_rechazada", True),
        "notify_vencimiento_7d":     prefs.get("notify_vencimiento_7d", True),
        "notify_vencimiento_vencida":prefs.get("notify_vencimiento_vencida", True),
        "notify_reporte_mensual":    prefs.get("notify_reporte_mensual", True),
    }


@router.put("/preferencias", summary="Actualizar preferencias de notificaciones")
async def update_preferencias(
    data: PreferenciasUpdate,
    current_user: dict = Depends(get_current_user),
):
    sb = get_sb()
    _get_or_create_prefs(sb, current_user["id"])   # garantiza que exista el row
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        sb.table("email_preferences").update(updates).eq("user_id", current_user["id"]).execute()
    return {"ok": True}


# ── CRON: VENCIMIENTOS ─────────────────────────────────────────────────────────

@router.post(
    "/cron/check-vencimientos",
    summary="Cron diario — alertas de vencimiento (requiere X-Cron-Key)",
    include_in_schema=False,
)
async def cron_check_vencimientos(
    x_cron_key: Optional[str] = Header(None, alias="X-Cron-Key"),
):
    _check_cron_key(x_cron_key)

    sb = get_sb()
    hoy = date.today()
    en_7 = hoy + timedelta(days=7)
    enviados_7d = 0
    enviados_vencidas = 0
    errores = []

    try:
        # ── Facturas que vencen EXACTAMENTE en 7 días ──
        r7 = (
            sb.table("facturas")
            .select("*")
            .eq("fecha_vencimiento", en_7.isoformat())
            .not_.in_("estado", ["CEDIDA", "PAGADA"])
            .execute()
        )
        por_usuario: dict[str, list] = {}
        for f in (r7.data or []):
            uid = f.get("emisor_id")
            if uid:
                por_usuario.setdefault(uid, []).append(f)

        for uid, facts in por_usuario.items():
            try:
                u = sb.table("usuarios").select("email,nombre").eq("id", uid).execute()
                if not u.data:
                    continue
                user = u.data[0]
                if get_user_pref(sb, uid, "notify_vencimiento_7d"):
                    email_vencimiento_7dias(user["email"], user["nombre"], facts)
                    enviados_7d += 1
            except Exception as e:
                errores.append(f"7d uid={uid}: {e}")
                logger.error("Error alerta 7d uid=%s: %s", uid, e)

        # ── Facturas vencidas hoy (vencimiento < hoy) ──
        rv = (
            sb.table("facturas")
            .select("*")
            .lt("fecha_vencimiento", hoy.isoformat())
            .not_.in_("estado", ["CEDIDA", "PAGADA"])
            .execute()
        )
        por_usuario_v: dict[str, list] = {}
        for f in (rv.data or []):
            uid = f.get("emisor_id")
            if uid:
                por_usuario_v.setdefault(uid, []).append(f)

        for uid, facts in por_usuario_v.items():
            try:
                u = sb.table("usuarios").select("email,nombre").eq("id", uid).execute()
                if not u.data:
                    continue
                user = u.data[0]
                if get_user_pref(sb, uid, "notify_vencimiento_vencida"):
                    email_facturas_vencidas(user["email"], user["nombre"], facts)
                    enviados_vencidas += 1
            except Exception as e:
                errores.append(f"vencida uid={uid}: {e}")
                logger.error("Error alerta vencida uid=%s: %s", uid, e)

    except Exception as e:
        logger.error("Error crítico en cron_check_vencimientos: %s", e)
        raise HTTPException(500, f"Error procesando vencimientos: {e}")

    return {
        "fecha": hoy.isoformat(),
        "alertas_7dias_enviadas": enviados_7d,
        "alertas_vencidas_enviadas": enviados_vencidas,
        "errores": errores,
    }


# ── CRON: REPORTE MENSUAL ──────────────────────────────────────────────────────

@router.post(
    "/cron/reporte-mensual",
    summary="Cron mensual — reporte de actividad (requiere X-Cron-Key, día 1)",
    include_in_schema=False,
)
async def cron_reporte_mensual(
    x_cron_key: Optional[str] = Header(None, alias="X-Cron-Key"),
):
    _check_cron_key(x_cron_key)

    hoy = date.today()
    if hoy.day != 1:
        return {"ok": True, "mensaje": f"No es día 1 del mes (hoy es {hoy}), omitido"}

    # Rango del mes anterior
    primer_actual = hoy.replace(day=1)
    ultimo_ant = primer_actual - timedelta(days=1)
    primer_ant = ultimo_ant.replace(day=1)
    nombre_mes = MESES_ES[ultimo_ant.month - 1]

    sb = get_sb()
    usuarios = sb.table("usuarios").select("*").eq("activo", True).execute()
    enviados = 0
    errores = []

    for u in (usuarios.data or []):
        try:
            if not get_user_pref(sb, u["id"], "notify_reporte_mensual"):
                continue

            facts = (
                sb.table("facturas")
                .select("id")
                .eq("emisor_id", u["id"])
                .gte("fecha_emision", primer_ant.isoformat())
                .lte("fecha_emision", ultimo_ant.isoformat())
                .execute()
            )
            total_f = len(facts.data or [])
            ids = [f["id"] for f in (facts.data or [])]

            total_ces = 0
            monto_cedido = 0.0
            total_all = 0
            if ids:
                ces_acept = (
                    sb.table("cesiones")
                    .select("valor_cesion")
                    .in_("factura_id", ids)
                    .eq("estado", "ACEPTADA")
                    .execute()
                )
                total_ces = len(ces_acept.data or [])
                monto_cedido = sum(c.get("valor_cesion", 0) for c in (ces_acept.data or []))

                all_ces = (
                    sb.table("cesiones")
                    .select("id", count="exact")
                    .in_("factura_id", ids)
                    .execute()
                )
                total_all = all_ces.count or 0

            tasa = (total_ces / total_all * 100) if total_all > 0 else 0.0

            email_reporte_mensual(
                u["email"], u["nombre"], nombre_mes, ultimo_ant.year,
                total_f, total_ces, monto_cedido, tasa,
            )
            enviados += 1
        except Exception as e:
            errores.append(f"uid={u.get('id')}: {e}")
            logger.error("Error reporte mensual uid=%s: %s", u.get("id"), e)

    return {
        "fecha": hoy.isoformat(),
        "mes": nombre_mes,
        "reportes_enviados": enviados,
        "errores": errores,
    }
