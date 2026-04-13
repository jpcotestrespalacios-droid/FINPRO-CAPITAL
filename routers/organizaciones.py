"""
routers/organizaciones.py
Multi-tenancy: organizaciones, miembros e invitaciones.

Endpoints:
  POST   /crear               — crear organización (el creador queda como owner)
  GET    /mis-organizaciones   — listar orgs donde soy miembro
  GET    /{org_id}            — detalle de org (solo miembros)
  POST   /{org_id}/invitar    — invitar usuario por email
  POST   /aceptar/{token}     — aceptar invitación
  PUT    /{org_id}/plan       — cambiar plan (solo owner/admin)
  GET    /{org_id}/miembros   — listar miembros
"""
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from supabase_db import get_sb
from routers.autenticacion import get_current_user

router = APIRouter()


# ─── Modelos ─────────────────────────────────────────────────────────────────

class CrearOrgRequest(BaseModel):
    nombre: str
    nit: str
    plan: Optional[str] = "starter"


class InvitarRequest(BaseModel):
    email: str
    rol: Optional[str] = "miembro"


# ─── Helpers ─────────────────────────────────────────────────────────────────

PLAN_LIMITS = {
    "starter":      5,
    "professional": 50,
    "enterprise":   9999,
}


def _get_org_o_403(sb, org_id: str, usuario_id: int, roles_permitidos=None):
    """Devuelve (org, membresia) o lanza 403/404."""
    org_res = sb.table("organizaciones").select("*").eq("id", org_id).execute()
    if not org_res.data:
        raise HTTPException(404, "Organización no encontrada")
    org = org_res.data[0]

    mem_res = sb.table("miembros_org").select("rol,activo").eq(
        "organizacion_id", org_id).eq("usuario_id", usuario_id).execute()
    if not mem_res.data or not mem_res.data[0]["activo"]:
        raise HTTPException(403, "No eres miembro activo de esta organización")

    mem = mem_res.data[0]
    if roles_permitidos and mem["rol"] not in roles_permitidos:
        raise HTTPException(403, f"Se requiere rol: {roles_permitidos}")
    return org, mem


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/crear", summary="Crear una organización")
async def crear_organizacion(data: CrearOrgRequest, current_user: dict = Depends(get_current_user)):
    sb = get_sb()

    # NIT único
    existe = sb.table("organizaciones").select("id").eq("nit", data.nit).execute()
    if existe.data:
        raise HTTPException(409, f"Ya existe una organización con NIT {data.nit}")

    if data.plan not in PLAN_LIMITS:
        raise HTTPException(400, f"Plan inválido. Opciones: {list(PLAN_LIMITS)}")

    org = sb.table("organizaciones").insert({
        "nombre": data.nombre,
        "nit": data.nit,
        "plan": data.plan,
        "max_cesiones": PLAN_LIMITS[data.plan],
        "owner_id": current_user["id"],
    }).execute()
    org_id = org.data[0]["id"]

    # Agregar owner como miembro con rol owner
    sb.table("miembros_org").insert({
        "organizacion_id": org_id,
        "usuario_id": current_user["id"],
        "rol": "owner",
    }).execute()

    return {
        "id": org_id,
        "nombre": data.nombre,
        "nit": data.nit,
        "plan": data.plan,
        "max_cesiones": PLAN_LIMITS[data.plan],
        "mensaje": "Organización creada exitosamente",
    }


@router.get("/mis-organizaciones", summary="Listar mis organizaciones")
async def mis_organizaciones(current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    miembros = sb.table("miembros_org").select(
        "rol, organizaciones(id, nombre, nit, plan, max_cesiones, activa, created_at)"
    ).eq("usuario_id", current_user["id"]).eq("activo", True).execute()

    return {
        "total": len(miembros.data),
        "organizaciones": [
            {**m["organizaciones"], "mi_rol": m["rol"]}
            for m in miembros.data
            if m.get("organizaciones")
        ],
    }


@router.get("/{org_id}", summary="Detalle de organización")
async def detalle_organizacion(org_id: str, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    org, mem = _get_org_o_403(sb, org_id, current_user["id"])

    # Contar cesiones del mes
    inicio_mes = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0).isoformat()
    ces_count = sb.table("cesiones").select("id", count="exact").eq(
        "organizacion_id", org_id
    ).gte("fecha_cesion", inicio_mes).execute()

    return {
        **org,
        "mi_rol": mem["rol"],
        "cesiones_este_mes": ces_count.count or 0,
    }


@router.post("/{org_id}/invitar", summary="Invitar usuario a la organización")
async def invitar_miembro(org_id: str, data: InvitarRequest, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    _get_org_o_403(sb, org_id, current_user["id"], roles_permitidos=["owner", "admin"])

    if data.rol not in ("admin", "miembro"):
        raise HTTPException(400, "Rol inválido: usa 'admin' o 'miembro'")

    # Verificar si el email ya fue invitado y sigue pendiente
    ya = sb.table("invitaciones").select("id").eq("organizacion_id", org_id).eq(
        "email", data.email).eq("estado", "PENDIENTE").execute()
    if ya.data:
        raise HTTPException(409, "Ya existe una invitación pendiente para ese email")

    token = secrets.token_urlsafe(32)
    sb.table("invitaciones").insert({
        "organizacion_id": org_id,
        "email": data.email,
        "rol": data.rol,
        "token": token,
        "invitado_por": current_user["id"],
    }).execute()

    # Enviar email de invitación (no bloquea)
    try:
        from notifications import send_email
        import html
        org_res = sb.table("organizaciones").select("nombre").eq("id", org_id).execute()
        org_nombre = org_res.data[0]["nombre"] if org_res.data else "tu organización"
        send_email(
            data.email,
            f"Invitación para unirte a {html.escape(org_nombre)} en FinPro Capital",
            f"""<div style="font-family:-apple-system,Arial,sans-serif;max-width:560px;margin:0 auto;padding:20px">
            <div style="background:#0B1829;padding:20px;border-radius:10px 10px 0 0">
              <h2 style="color:#fff;margin:0;font-size:17px">⚡ FinPro Capital — Invitación</h2>
            </div>
            <div style="background:#fff;padding:28px;border:1px solid #E4E9F0;border-top:none">
              <p style="color:#374151"><strong>{html.escape(current_user['nombre'])}</strong>
                te invitó a unirte a <strong>{html.escape(org_nombre)}</strong>
                con rol <strong>{html.escape(data.rol)}</strong>.</p>
              <div style="text-align:center;margin:28px 0">
                <a href="/api/v1/organizaciones/aceptar/{token}"
                   style="background:#1A4FD6;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;display:inline-block">
                  Aceptar invitación
                </a>
              </div>
              <p style="font-size:12px;color:#94A3B8">Este enlace expira en 7 días.</p>
            </div>
            </div>""",
        )
    except Exception as e:
        print(f"[org] Error email invitación: {e}")

    return {"mensaje": f"Invitación enviada a {data.email}", "token": token}


@router.post("/aceptar/{token}", summary="Aceptar invitación a organización")
async def aceptar_invitacion(token: str, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    inv_res = sb.table("invitaciones").select("*").eq("token", token).execute()
    if not inv_res.data:
        raise HTTPException(404, "Invitación no encontrada")
    inv = inv_res.data[0]

    if inv["estado"] != "PENDIENTE":
        raise HTTPException(400, f"Invitación ya fue {inv['estado'].lower()}")

    # Verificar que el email del usuario coincide
    if current_user.get("email") != inv["email"]:
        raise HTTPException(403, "Esta invitación es para otro email")

    # Verificar que la invitación no expiró
    if inv.get("expira_en") and datetime.fromisoformat(inv["expira_en"]) < datetime.now(timezone.utc):
        sb.table("invitaciones").update({"estado": "EXPIRADA"}).eq("id", inv["id"]).execute()
        raise HTTPException(400, "La invitación ha expirado")

    # Agregar como miembro
    ya = sb.table("miembros_org").select("id").eq(
        "organizacion_id", inv["organizacion_id"]).eq("usuario_id", current_user["id"]).execute()
    if ya.data:
        raise HTTPException(409, "Ya eres miembro de esta organización")

    sb.table("miembros_org").insert({
        "organizacion_id": inv["organizacion_id"],
        "usuario_id": current_user["id"],
        "rol": inv["rol"],
    }).execute()
    sb.table("invitaciones").update({"estado": "ACEPTADA"}).eq("id", inv["id"]).execute()

    return {"mensaje": "Te uniste a la organización exitosamente", "organizacion_id": inv["organizacion_id"], "rol": inv["rol"]}


@router.put("/{org_id}/plan", summary="Cambiar plan de la organización")
async def cambiar_plan(org_id: str, plan: str, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    _get_org_o_403(sb, org_id, current_user["id"], roles_permitidos=["owner", "admin"])

    if plan not in PLAN_LIMITS:
        raise HTTPException(400, f"Plan inválido. Opciones: {list(PLAN_LIMITS)}")

    sb.table("organizaciones").update({
        "plan": plan,
        "max_cesiones": PLAN_LIMITS[plan],
    }).eq("id", org_id).execute()

    return {"mensaje": f"Plan actualizado a {plan}", "max_cesiones": PLAN_LIMITS[plan]}


@router.get("/{org_id}/miembros", summary="Listar miembros de la organización")
async def listar_miembros(org_id: str, current_user: dict = Depends(get_current_user)):
    sb = get_sb()
    _get_org_o_403(sb, org_id, current_user["id"])

    mems = sb.table("miembros_org").select(
        "rol, activo, joined_at, usuarios(id, nombre, email, nit)"
    ).eq("organizacion_id", org_id).execute()

    return {
        "total": len(mems.data),
        "miembros": [
            {
                "rol": m["rol"],
                "activo": m["activo"],
                "joined_at": m["joined_at"],
                **(m["usuarios"] or {}),
            }
            for m in mems.data
        ],
    }
