"""
routers/deudor.py
Portal del deudor — notificación legal de cesión (Ley 1231 de 2008).

Endpoints:
  POST /notificar          — notifica al deudor por email con token de confirmación
  GET  /confirmar/{token}  — página pública de confirmación de recepción
  GET  /verificar/{cude}   — página pública de verificación del estado de cesión
  GET  /estado/{cude}      — consulta estado de notificación (para el cedente)
"""
import html
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from supabase_db import get_sb

router = APIRouter()


class NotificarDeudorRequest(BaseModel):
    cude: str
    deudor_email: str


def _generar_token() -> str:
    return secrets.token_urlsafe(32)


# ── NOTIFICAR ─────────────────────────────────────────────────────────────────

@router.post("/notificar", summary="Notificar al deudor de la cesión (Ley 1231/2008)")
async def notificar_deudor(data: NotificarDeudorRequest, request: Request):
    sb = get_sb()

    # Verificar que la cesión existe y fue aceptada
    res = sb.table("cesiones").select("*").eq("cude", data.cude).execute()
    if not res.data:
        raise HTTPException(404, "Cesión no encontrada")
    cesion = res.data[0]

    if cesion["estado"] != "ACEPTADA":
        raise HTTPException(400, "Solo se puede notificar cesiones aceptadas por la DIAN")

    # Verificar que no fue notificado ya
    existe = sb.table("notificaciones_deudor").select("id").eq("cude", data.cude).execute()
    if existe.data:
        raise HTTPException(409, "El deudor ya fue notificado para esta cesión")

    token = _generar_token()
    url_base = str(request.base_url).rstrip("/")
    url_confirmacion = f"{url_base}/api/v1/deudor/confirmar/{token}"
    url_verificar = f"{url_base}/api/v1/deudor/verificar/{data.cude}"

    # Guardar notificación en BD
    sb.table("notificaciones_deudor").insert({
        "cude": data.cude,
        "deudor_nit": cesion["deudor_nit"],
        "deudor_email": data.deudor_email,
        "estado": "ENVIADA",
        "token_confirmacion": token,
        "enviado_en": datetime.utcnow().isoformat(),
    }).execute()

    # Enviar email con Resend
    try:
        from notifications import send_email
        html_body = f"""
        <div style="font-family:-apple-system,Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
          <div style="background:#0B1829;padding:24px;border-radius:10px 10px 0 0">
            <h1 style="color:#fff;margin:0;font-size:18px;font-weight:800">
              <span style="background:#1A4FD6;border-radius:6px;padding:3px 8px;margin-right:8px;font-size:13px">⚡</span>
              FinPro Capital
            </h1>
            <p style="color:rgba(255,255,255,.5);margin:6px 0 0;font-size:12px">Notificación legal de cesión · RADIAN/DIAN</p>
          </div>

          <div style="background:#fff;padding:32px;border:1px solid #E4E9F0;border-top:none">
            <div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;padding:14px 18px;margin-bottom:24px">
              <strong style="color:#92400E">⚠ Aviso legal importante</strong><br>
              <span style="font-size:13px;color:#78350F">Este mensaje constituye notificación formal de cesión conforme a la <strong>Ley 1231 de 2008</strong>.</span>
            </div>

            <p style="color:#374151;font-size:15px">Estimado/a <strong>{html.escape(cesion['deudor_nombre'])}</strong>,</p>
            <p style="color:#374151;font-size:14px;line-height:1.6">
              <strong>{html.escape(cesion['cedente_nombre'])}</strong> ha cedido el derecho económico
              de una factura electrónica a <strong>{html.escape(cesion['cesionario_nombre'])}</strong>
              mediante el sistema RADIAN de la DIAN (Evento 037 — Endoso en Propiedad).
            </p>

            <div style="background:#F8FAFC;border-radius:8px;padding:18px;margin:24px 0">
              <table style="width:100%;border-collapse:collapse">
                <tr>
                  <td style="color:#64748B;font-size:12px;padding:7px 0;border-bottom:1px solid #E2E8F0">Cedente (anterior acreedor)</td>
                  <td style="font-weight:600;font-size:13px;padding:7px 0;border-bottom:1px solid #E2E8F0">{html.escape(cesion['cedente_nombre'])}</td>
                </tr>
                <tr>
                  <td style="color:#64748B;font-size:12px;padding:7px 0;border-bottom:1px solid #E2E8F0">Nuevo acreedor (cesionario)</td>
                  <td style="font-weight:600;font-size:13px;color:#059669;padding:7px 0;border-bottom:1px solid #E2E8F0">{html.escape(cesion['cesionario_nombre'])}</td>
                </tr>
                <tr>
                  <td style="color:#64748B;font-size:12px;padding:7px 0;border-bottom:1px solid #E2E8F0">Valor cedido</td>
                  <td style="font-weight:700;font-size:15px;padding:7px 0;border-bottom:1px solid #E2E8F0">${cesion['valor_cesion']:,.0f} COP</td>
                </tr>
                <tr>
                  <td style="color:#64748B;font-size:12px;padding:7px 0">CUDE RADIAN</td>
                  <td style="font-family:monospace;font-size:11px;padding:7px 0;word-break:break-all">{html.escape(data.cude[:48])}...</td>
                </tr>
              </table>
            </div>

            <p style="color:#374151;font-size:14px;line-height:1.6">
              A partir de la fecha de esta notificación, <strong>los pagos correspondientes a esta
              factura deben realizarse únicamente a {html.escape(cesion['cesionario_nombre'])}</strong>.
              El pago al cedente original no será liberatorio.
            </p>

            <div style="text-align:center;margin:32px 0">
              <a href="{url_confirmacion}" style="background:#1A4FD6;color:#fff;text-decoration:none;padding:14px 32px;border-radius:10px;font-size:14px;font-weight:700;display:inline-block">
                ✓ Confirmar recepción de notificación
              </a>
            </div>

            <p style="font-size:12px;color:#94A3B8;margin-top:24px">
              Verificar en RADIAN: <a href="{url_verificar}" style="color:#1A4FD6">{url_verificar}</a>
            </p>
          </div>

          <div style="background:#F4F6FA;border-radius:0 0 10px 10px;padding:16px;border:1px solid #E4E9F0;border-top:none;text-align:center">
            <p style="margin:0;font-size:11px;color:#94A3B8">FinPro Capital SAS · Colombia · Cumplimiento Ley 1231 de 2008</p>
          </div>
        </div>
        """
        send_email(
            data.deudor_email,
            f"Notificación legal de cesión — {html.escape(cesion['cedente_nombre'])}",
            html_body,
        )
    except Exception as e:
        print(f"[deudor] Error enviando email: {e}")

    return {
        "mensaje": "Notificación legal enviada al deudor",
        "deudor_email": data.deudor_email,
        "cude": data.cude,
        "cumple_ley_1231": True,
        "url_verificacion": url_verificar,
    }


# ── CONFIRMAR (página pública) ────────────────────────────────────────────────

@router.get("/confirmar/{token}", response_class=HTMLResponse, include_in_schema=False)
async def confirmar_notificacion(token: str, request: Request):
    sb = get_sb()
    notif = sb.table("notificaciones_deudor").select("*").eq("token_confirmacion", token).execute()
    if not notif.data:
        return HTMLResponse("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
        <title>Token inválido</title></head>
        <body style="font-family:-apple-system,sans-serif;text-align:center;padding:80px;color:#374151">
        <div style="font-size:48px;margin-bottom:16px">❌</div>
        <h2 style="color:#EF4444">Token inválido o ya utilizado</h2>
        <p>Este enlace no es válido o ya fue usado anteriormente.</p>
        </body></html>""", status_code=404)

    n = notif.data[0]
    if n["estado"] == "CONFIRMADA":
        return HTMLResponse("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
        <title>Ya confirmado</title></head>
        <body style="font-family:-apple-system,sans-serif;text-align:center;padding:80px;color:#374151">
        <div style="font-size:48px;margin-bottom:16px">✅</div>
        <h2 style="color:#059669">Ya habías confirmado esta notificación</h2>
        <p>Tu confirmación fue registrada anteriormente.</p>
        </body></html>""")

    client_ip = request.client.host if request.client else "unknown"
    sb.table("notificaciones_deudor").update({
        "estado": "CONFIRMADA",
        "confirmado_en": datetime.utcnow().isoformat(),
        "ip_confirmacion": client_ip,
    }).eq("token_confirmacion", token).execute()

    cude = n["cude"]
    cesion_res = sb.table("cesiones").select("cesionario_nombre,valor_cesion,cedente_nombre").eq("cude", cude).execute()
    c = cesion_res.data[0] if cesion_res.data else {}
    fmt_valor = f"${c.get('valor_cesion', 0):,.0f}".replace(",", ".")

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Notificación confirmada — FinPro Capital</title>
  <style>
    body{{font-family:-apple-system,Arial,sans-serif;background:#F0F4F8;margin:0;padding:20px;color:#374151}}
    .card{{max-width:520px;margin:60px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)}}
    .header{{background:#0B1829;padding:24px;text-align:center}}
    .body{{padding:40px;text-align:center}}
    .check{{font-size:56px;margin-bottom:16px}}
    h1{{color:#059669;font-size:22px;margin:0 0 12px}}
    .detail{{background:#F8FAFC;border-radius:10px;padding:18px;margin:24px 0;text-align:left;font-size:13px;line-height:1.7}}
    .footer{{padding:14px;background:#F8FAFC;border-top:1px solid #E2E8F0;font-size:11px;color:#94A3B8;text-align:center}}
  </style>
</head>
<body>
<div class="card">
  <div class="header">
    <span style="color:#fff;font-size:16px;font-weight:800">⚡ FinPro Capital</span>
    <p style="color:rgba(255,255,255,.5);margin:4px 0 0;font-size:12px">Notificación legal RADIAN</p>
  </div>
  <div class="body">
    <div class="check">✅</div>
    <h1>Notificación confirmada</h1>
    <p style="color:#64748B;font-size:14px">Has confirmado la recepción de la notificación legal de cesión de crédito.</p>
    <div class="detail">
      <strong>Nuevo acreedor:</strong> {html.escape(c.get('cesionario_nombre',''))}<br>
      <strong>Cedente original:</strong> {html.escape(c.get('cedente_nombre',''))}<br>
      <strong>Valor cedido:</strong> {fmt_valor} COP<br>
      <strong>Fecha confirmación:</strong> {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC
    </div>
    <p style="font-size:13px;color:#64748B;line-height:1.6">
      Recuerda realizar todos los pagos futuros directamente a
      <strong>{html.escape(c.get('cesionario_nombre',''))}</strong>.
    </p>
    <p style="font-size:11px;color:#94A3B8;margin-top:24px">FinPro Capital · Ley 1231 de 2008 · Colombia</p>
  </div>
</div>
</body>
</html>""")


# ── VERIFICAR (página pública) ────────────────────────────────────────────────

@router.get("/verificar/{cude}", response_class=HTMLResponse, include_in_schema=False)
async def verificar_cesion_publica(cude: str):
    sb = get_sb()
    res = sb.table("cesiones").select(
        "cude,cedente_nombre,cesionario_nombre,deudor_nombre,valor_cesion,estado,fecha_cesion"
    ).eq("cude", cude).execute()

    if not res.data:
        return HTMLResponse("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
        <title>No encontrada</title></head>
        <body style="font-family:-apple-system,sans-serif;text-align:center;padding:80px">
        <div style="font-size:48px;margin-bottom:16px">❌</div>
        <h2 style="color:#EF4444">Cesión no encontrada</h2>
        <p style="color:#64748B">El CUDE no corresponde a ninguna cesión registrada.</p>
        </body></html>""", status_code=404)

    c = res.data[0]
    aceptada = c["estado"] == "ACEPTADA"
    color_estado = "#059669" if aceptada else "#EF4444"
    badge_txt = "✓ Aceptada DIAN" if aceptada else f"✗ {c['estado']}"
    fmt_valor = f"${c['valor_cesion']:,.0f}".replace(",", ".")

    notif = sb.table("notificaciones_deudor").select(
        "estado,enviado_en,confirmado_en"
    ).eq("cude", cude).execute()

    if notif.data:
        n = notif.data[0]
        notif_color = "#059669" if n["estado"] == "CONFIRMADA" else "#D97706"
        notif_txt = f"{n['estado']} · {str(n['enviado_en'])[:10]}"
        if n["estado"] == "CONFIRMADA" and n.get("confirmado_en"):
            notif_txt += f" · Confirmada {str(n['confirmado_en'])[:10]}"
    else:
        notif_color = "#EF4444"
        notif_txt = "⚠ Pendiente de notificación"

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Verificar Cesión — FinPro Capital</title>
  <style>
    body{{font-family:-apple-system,Arial,sans-serif;background:#F0F4F8;margin:0;padding:20px;color:#374151}}
    .card{{max-width:580px;margin:40px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)}}
    .header{{background:#0B1829;padding:24px}}
    .body{{padding:28px}}
    .badge{{display:inline-block;background:{color_estado}20;color:{color_estado};border:1px solid {color_estado}40;border-radius:20px;padding:5px 16px;font-size:13px;font-weight:700;margin-bottom:20px}}
    table{{width:100%;border-collapse:collapse}}
    td{{padding:10px 0;border-bottom:1px solid #F1F5F9;font-size:13px}}
    td:first-child{{color:#64748B;width:45%}}
    .footer{{padding:14px 28px;background:#F8FAFC;border-top:1px solid #E2E8F0;font-size:11px;color:#94A3B8;text-align:center}}
  </style>
</head>
<body>
<div class="card">
  <div class="header">
    <span style="color:#fff;font-size:16px;font-weight:800">⚡ FinPro Capital</span>
    <p style="color:rgba(255,255,255,.5);margin:6px 0 0;font-size:12px">Verificación de cesión RADIAN/DIAN</p>
  </div>
  <div class="body">
    <div class="badge">{badge_txt}</div>
    <table>
      <tr><td>Cedente</td><td><strong>{html.escape(c['cedente_nombre'])}</strong></td></tr>
      <tr><td>Cesionario (nuevo acreedor)</td><td><strong style="color:#059669">{html.escape(c['cesionario_nombre'])}</strong></td></tr>
      <tr><td>Deudor</td><td>{html.escape(c['deudor_nombre'])}</td></tr>
      <tr><td>Valor cedido</td><td><strong>{fmt_valor} COP</strong></td></tr>
      <tr><td>Fecha cesión</td><td>{str(c['fecha_cesion'])[:10]}</td></tr>
      <tr><td>Notificación deudor</td><td style="color:{notif_color};font-weight:600">{notif_txt}</td></tr>
      <tr style="border-bottom:none"><td>CUDE</td><td style="font-family:monospace;font-size:11px;word-break:break-all">{html.escape(cude)}</td></tr>
    </table>
  </div>
  <div class="footer">Verificado en RADIAN/DIAN · FinPro Capital · Ley 1231 de 2008 · Colombia</div>
</div>
</body>
</html>""")


# ── ESTADO (para el cedente autenticado) ────────────────────────────────────

@router.get("/estado/{cude}", summary="Estado de notificación al deudor")
async def estado_notificacion(cude: str):
    sb = get_sb()
    res = sb.table("notificaciones_deudor").select(
        "estado,deudor_email,deudor_nit,enviado_en,confirmado_en"
    ).eq("cude", cude).execute()

    if not res.data:
        return {
            "notificado": False,
            "riesgo_legal": True,
            "mensaje": "El deudor aún no ha sido notificado. Esto puede implicar riesgo legal (Ley 1231/2008).",
            "accion": "POST /api/v1/deudor/notificar",
        }
    n = res.data[0]
    return {
        "notificado": True,
        "estado": n["estado"],
        "deudor_email": n["deudor_email"],
        "deudor_nit": n["deudor_nit"],
        "confirmado": n["estado"] == "CONFIRMADA",
        "enviado_en": n["enviado_en"],
        "confirmado_en": n.get("confirmado_en"),
        "riesgo_legal": False,
    }
