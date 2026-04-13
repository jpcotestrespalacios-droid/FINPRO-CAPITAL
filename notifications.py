"""
notifications.py
Sistema de notificaciones por email via Resend (resend.com).
Uso: importar las funciones email_* y llamarlas tras los eventos de negocio.
Los errores de envío se loggean pero NO interrumpen el flujo principal.
"""
import html
import logging

try:
    import resend as _resend_lib
    _RESEND_AVAILABLE = True
except ImportError:
    _resend_lib = None
    _RESEND_AVAILABLE = False

from config import settings

logger = logging.getLogger(__name__)

APP_URL = "https://finpro-capital.vercel.app"
FROM_EMAIL = "FinPro Capital <noreply@finprocapital.co>"


# ── CORE SEND ─────────────────────────────────────────────────────────────────

def send_email(to: str, subject: str, html_body: str) -> bool:
    """Envía un email via Resend. Retorna True si fue enviado, False si falló.
    Nunca lanza excepción — los errores se loggean silenciosamente."""
    if not _RESEND_AVAILABLE:
        logger.warning("Resend no instalado — email no enviado a %s: %s", to, subject)
        return False
    api_key = getattr(settings, "RESEND_API_KEY", "")
    if not api_key:
        logger.warning("RESEND_API_KEY no configurado — email no enviado a %s", to)
        return False
    try:
        _resend_lib.api_key = api_key
        _resend_lib.Emails.send({
            "from": FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html_body,
        })
        logger.info("✉ Email enviado a %s: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("✗ Error enviando email a %s (%s): %s", to, subject, exc)
        return False


# ── HTML BASE TEMPLATE ────────────────────────────────────────────────────────

def _base(title: str, preheader: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#F4F6FA;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#0D1B2E">
<span style="display:none;font-size:1px;color:#F4F6FA;max-height:0;overflow:hidden">{preheader}&nbsp;</span>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F6FA;padding:32px 16px">
  <tr><td align="center">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px">

      <!-- HEADER -->
      <tr><td style="background:#0B1829;border-radius:14px 14px 0 0;padding:24px 36px">
        <table cellpadding="0" cellspacing="0">
          <tr>
            <td style="background:#1A4FD6;border-radius:8px;width:32px;height:32px;text-align:center;font-size:16px;line-height:32px;vertical-align:middle">⚡</td>
            <td style="padding-left:10px;font-size:19px;font-weight:800;color:#fff;letter-spacing:-0.5px;vertical-align:middle">FinPro Capital</td>
            <td style="padding-left:8px;vertical-align:middle">
              <span style="background:#1A4FD6;color:#fff;font-size:9px;font-weight:700;padding:2px 8px;border-radius:99px;letter-spacing:0.5px">RADIAN</span>
            </td>
          </tr>
        </table>
      </td></tr>

      <!-- BODY -->
      <tr><td style="background:#fff;padding:36px 36px 28px;border-left:1px solid #E4E9F0;border-right:1px solid #E4E9F0">
        {body}
      </td></tr>

      <!-- FOOTER -->
      <tr><td style="background:#F4F6FA;border-radius:0 0 14px 14px;padding:20px 36px;border:1px solid #E4E9F0;border-top:none;text-align:center">
        <p style="margin:0 0 6px;font-size:12px;color:#9DAEC0">
          <a href="{APP_URL}/app" style="color:#1A4FD6;text-decoration:none;font-weight:600">Abrir plataforma</a>
          &nbsp;&middot;&nbsp;
          <a href="{APP_URL}/app" style="color:#9DAEC0;text-decoration:none">Gestionar notificaciones</a>
        </p>
        <p style="margin:0;font-size:11px;color:#C0CDD8;line-height:1.6">
          FinPro Capital SAS &middot; Colombia &middot; RADIAN API v1.0<br>
          Recibes este correo porque tienes una cuenta activa en FinPro Capital.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


def _btn(text: str, url: str, color: str = "#1A4FD6") -> str:
    return (
        f'<div style="text-align:center;margin:28px 0 4px">'
        f'<a href="{url}" style="background:{color};color:#fff;text-decoration:none;'
        f'padding:13px 30px;border-radius:10px;font-size:14px;font-weight:700;'
        f'display:inline-block;letter-spacing:-0.2px">{text}</a>'
        f'</div>'
    )


def _divider() -> str:
    return '<hr style="border:none;border-top:1px solid #E4E9F0;margin:24px 0"/>'


# ── EMAIL TEMPLATES ───────────────────────────────────────────────────────────

def _primer_nombre(nombre: str) -> str:
    """Extrae el primer nombre de forma segura."""
    stripped = (nombre or "").strip()
    return stripped.split()[0] if stripped else "amigo"


def email_bienvenida(nombre: str, email: str) -> bool:
    """Email de bienvenida tras registro exitoso."""
    primer = _primer_nombre(nombre)
    body = f"""
    <h2 style="margin:0 0 10px;font-size:26px;font-weight:800;color:#0D1B2E;letter-spacing:-0.5px">
      ¡Bienvenido a FinPro Capital, {primer}!
    </h2>
    <p style="margin:0 0 24px;font-size:15px;color:#5A6A7E;line-height:1.65">
      Tu cuenta está lista. Registra facturas electrónicas y cédelas en RADIAN en menos de 1 minuto.
    </p>

    <div style="background:#F4F6FA;border-radius:10px;padding:20px 24px;margin-bottom:24px">
      <p style="margin:0 0 12px;font-size:11px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:1px">Primeros pasos</p>
      <table cellpadding="0" cellspacing="0" width="100%">
        <tr><td style="padding:6px 0;font-size:14px;color:#5A6A7E">
          <span style="color:#1A4FD6;font-weight:700;margin-right:8px">&#9312;</span>
          Registra tu primera factura con el CUFE del XML DIAN
        </td></tr>
        <tr><td style="padding:6px 0;font-size:14px;color:#5A6A7E">
          <span style="color:#1A4FD6;font-weight:700;margin-right:8px">&#9313;</span>
          Habilítala como título valor electrónico
        </td></tr>
        <tr><td style="padding:6px 0;font-size:14px;color:#5A6A7E">
          <span style="color:#1A4FD6;font-weight:700;margin-right:8px">&#9314;</span>
          Cédela en RADIAN &mdash; Evento 037 en &asymp;1 segundo
        </td></tr>
      </table>
    </div>

    {_btn("Ir a la plataforma &rarr;", f"{APP_URL}/app")}
    """
    return send_email(
        email,
        "Bienvenido a FinPro Capital — tu cuenta está lista ✓",
        _base("Bienvenido a FinPro Capital", f"Tu cuenta {email} está lista para operar en RADIAN", body),
    )


def email_cesion_aceptada(
    to: str, nombre: str, cude: str, valor: float,
    cedente: str, cesionario: str, factura_num: str,
) -> bool:
    """Email cuando una cesión es aceptada por la DIAN."""
    primer = _primer_nombre(nombre)
    fmt = f"${valor:,.0f}".replace(",", ".")
    cedente_esc = html.escape(cedente)
    cesionario_esc = html.escape(cesionario)
    factura_esc = html.escape(factura_num)
    body = f"""
    <div style="text-align:center;margin-bottom:28px">
      <div style="background:#ECFDF5;border-radius:50%;width:60px;height:60px;line-height:60px;font-size:28px;margin:0 auto 12px">&#10003;</div>
      <h2 style="margin:0 0 6px;font-size:24px;font-weight:800;color:#059669">Cesión aceptada por la DIAN</h2>
      <p style="margin:0;font-size:14px;color:#5A6A7E">Factura {factura_esc} &middot; {html.escape(primer)}</p>
    </div>

    <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;padding:22px;margin-bottom:24px;text-align:center">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:1px">Valor cedido</p>
      <p style="margin:0;font-size:38px;font-weight:800;color:#0D1B2E;letter-spacing:-1.5px">{fmt} COP</p>
    </div>

    <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:20px">
      <tr><td style="padding:10px 0;border-bottom:1px solid #F0F4F8">
        <span style="font-size:11px;color:#9DAEC0;font-weight:700;text-transform:uppercase;letter-spacing:0.5px">CUDE</span><br>
        <span style="font-size:12px;font-family:monospace;color:#0D1B2E">{html.escape(cude[:40])}&hellip;</span>
      </td></tr>
      <tr><td style="padding:10px 0;border-bottom:1px solid #F0F4F8">
        <span style="font-size:11px;color:#9DAEC0;font-weight:700;text-transform:uppercase;letter-spacing:0.5px">Cedente</span><br>
        <span style="font-size:14px;color:#0D1B2E">{cedente_esc}</span>
      </td></tr>
      <tr><td style="padding:10px 0">
        <span style="font-size:11px;color:#9DAEC0;font-weight:700;text-transform:uppercase;letter-spacing:0.5px">Cesionario</span><br>
        <span style="font-size:14px;color:#0D1B2E">{cesionario_esc}</span>
      </td></tr>
    </table>

    {_btn("Ver cesión en la plataforma &rarr;", f"{APP_URL}/app", "#059669")}
    """
    return send_email(
        to,
        f"✅ Tu cesión fue aceptada — {fmt} COP",
        _base(f"Cesión aceptada — {fmt} COP", f"Tu cesión por {fmt} COP fue aceptada por la DIAN", body),
    )


def email_cesion_rechazada(
    to: str, nombre: str, cude: str, valor: float,
    motivo: str, factura_num: str,
) -> bool:
    """Email cuando una cesión es rechazada por la DIAN."""
    primer = _primer_nombre(nombre)
    fmt = f"${valor:,.0f}".replace(",", ".")
    motivo_txt = html.escape(motivo or "La DIAN no especificó un motivo. Revisa el estado en la plataforma.")
    factura_esc = html.escape(factura_num)
    body = f"""
    <div style="text-align:center;margin-bottom:28px">
      <div style="background:#FEF2F2;border-radius:50%;width:60px;height:60px;line-height:60px;font-size:28px;margin:0 auto 12px">&#10007;</div>
      <h2 style="margin:0 0 6px;font-size:24px;font-weight:800;color:#DC2626">Cesión rechazada por la DIAN</h2>
      <p style="margin:0;font-size:14px;color:#5A6A7E">Hola {html.escape(primer)} &middot; Factura {factura_esc} &middot; {fmt} COP</p>
    </div>

    <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:20px 24px;margin-bottom:22px">
      <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#DC2626;text-transform:uppercase;letter-spacing:0.5px">Motivo del rechazo</p>
      <p style="margin:0;font-size:14px;color:#0D1B2E;line-height:1.55">{motivo_txt}</p>
    </div>

    <div style="background:#F4F6FA;border-radius:10px;padding:18px 22px;margin-bottom:22px">
      <p style="margin:0 0 10px;font-size:13px;font-weight:700;color:#0D1B2E">¿Qué hacer ahora?</p>
      <table cellpadding="0" cellspacing="0" width="100%">
        <tr><td style="padding:4px 0;font-size:13px;color:#5A6A7E"><span style="color:#1A4FD6;margin-right:8px">&rarr;</span> Verifica que los eventos 032 y 033 estén registrados en RADIAN</td></tr>
        <tr><td style="padding:4px 0;font-size:13px;color:#5A6A7E"><span style="color:#1A4FD6;margin-right:8px">&rarr;</span> Confirma que el NIT del cesionario esté habilitado en la plataforma DIAN</td></tr>
        <tr><td style="padding:4px 0;font-size:13px;color:#5A6A7E"><span style="color:#1A4FD6;margin-right:8px">&rarr;</span> Revisa el XML del evento en la plataforma para más detalles técnicos</td></tr>
      </table>
    </div>

    <p style="font-size:12px;color:#9DAEC0;margin:0 0 20px">CUDE: <span style="font-family:monospace">{cude[:40]}&hellip;</span></p>

    {_btn("Revisar en la plataforma &rarr;", f"{APP_URL}/app", "#DC2626")}
    """
    return send_email(
        to,
        f"❌ Tu cesión fue rechazada — {factura_num}",
        _base(f"Cesión rechazada — {factura_num}", f"Tu cesión fue rechazada: {motivo_txt[:80]}", body),
    )


def email_vencimiento_7dias(to: str, nombre: str, facturas: list) -> bool:
    """Email de alerta: facturas que vencen en 7 días."""
    n = len(facturas)
    primer = _primer_nombre(nombre)
    rows = "".join([
        f"""<tr>
          <td style="padding:9px 0;border-bottom:1px solid #F0F4F8;font-size:13px;font-weight:600;color:#0D1B2E">
            {html.escape(f.get('prefijo','FV'))}-{html.escape(str(f.get('numero','')))}
          </td>
          <td style="padding:9px 0;border-bottom:1px solid #F0F4F8;font-size:12px;color:#5A6A7E">
            {html.escape(f.get('adquiriente_nombre','—'))}
          </td>
          <td style="padding:9px 0;border-bottom:1px solid #F0F4F8;font-size:13px;font-weight:700;color:#0D1B2E;text-align:right">
            ${f.get('valor_total', 0):,.0f}
          </td>
          <td style="padding:9px 0;border-bottom:1px solid #F0F4F8;font-size:12px;color:#D97706;text-align:right;white-space:nowrap">
            {html.escape(str(f.get('fecha_vencimiento','')))}
          </td>
        </tr>"""
        for f in facturas[:10]
    ])
    body = f"""
    <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:20px;margin-bottom:26px;text-align:center">
      <div style="font-size:34px;margin-bottom:8px">&#9200;</div>
      <h2 style="margin:0 0 6px;font-size:22px;font-weight:800;color:#D97706">
        {n} factura{'s' if n != 1 else ''} vence{'n' if n != 1 else ''} en 7 días
      </h2>
      <p style="margin:0;font-size:13px;color:#92400E">Hola {primer} — actúa ahora para evitar que venzan sin ceder</p>
    </div>

    <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:22px">
      <thead>
        <tr>
          <th style="text-align:left;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Factura</th>
          <th style="text-align:left;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Adquiriente</th>
          <th style="text-align:right;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Valor</th>
          <th style="text-align:right;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Vence</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    {"<p style='font-size:12px;color:#9DAEC0;margin:0 0 16px'>...y " + str(len(facturas)-10) + " más</p>" if len(facturas) > 10 else ""}

    {_btn("Ceder facturas ahora &rarr;", f"{APP_URL}/app", "#D97706")}
    """
    return send_email(
        to,
        f"⏰ Tienes {n} factura{'s' if n != 1 else ''} venciendo esta semana",
        _base(f"{n} facturas por vencer", f"Tienes {n} factura(s) que vencen en 7 días — actúa ahora", body),
    )


def email_facturas_vencidas(to: str, nombre: str, facturas: list) -> bool:
    """Email de alerta: facturas vencidas en cartera."""
    n = len(facturas)
    primer = _primer_nombre(nombre)
    rows = "".join([
        f"""<tr>
          <td style="padding:9px 0;border-bottom:1px solid #FEE2E2;font-size:13px;font-weight:600;color:#0D1B2E">
            {html.escape(f.get('prefijo','FV'))}-{html.escape(str(f.get('numero','')))}
          </td>
          <td style="padding:9px 0;border-bottom:1px solid #FEE2E2;font-size:12px;color:#5A6A7E">
            {html.escape(f.get('adquiriente_nombre','—'))}
          </td>
          <td style="padding:9px 0;border-bottom:1px solid #FEE2E2;font-size:13px;font-weight:700;color:#DC2626;text-align:right">
            ${f.get('valor_total', 0):,.0f}
          </td>
          <td style="padding:9px 0;border-bottom:1px solid #FEE2E2;font-size:12px;color:#DC2626;text-align:right;white-space:nowrap">
            {html.escape(str(f.get('fecha_vencimiento','')))}
          </td>
        </tr>"""
        for f in facturas[:10]
    ])
    body = f"""
    <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:20px;margin-bottom:26px;text-align:center">
      <div style="font-size:34px;margin-bottom:8px">&#128680;</div>
      <h2 style="margin:0 0 6px;font-size:22px;font-weight:800;color:#DC2626">
        {n} factura{'s' if n != 1 else ''} vencida{'s' if n != 1 else ''} en tu cartera
      </h2>
      <p style="margin:0;font-size:13px;color:#991B1B">Hola {primer} — estas facturas han superado su fecha de vencimiento</p>
    </div>

    <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:22px">
      <thead>
        <tr>
          <th style="text-align:left;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Factura</th>
          <th style="text-align:left;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Adquiriente</th>
          <th style="text-align:right;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Valor</th>
          <th style="text-align:right;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px;padding-bottom:8px">Venció</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>

    {_btn("Ver cartera vencida &rarr;", f"{APP_URL}/app", "#DC2626")}
    """
    return send_email(
        to,
        f"🚨 Alerta: {n} factura{'s' if n != 1 else ''} vencida{'s' if n != 1 else ''} en tu cartera",
        _base(f"Alerta: {n} facturas vencidas", f"Tienes {n} factura(s) vencidas en tu cartera", body),
    )


def email_reporte_mensual(
    to: str, nombre: str, mes: str, anio: int,
    total_facturas: int, total_cesiones: int,
    monto_cedido: float, tasa_aprobacion: float,
) -> bool:
    """Email de reporte mensual (se llama el día 1 de cada mes)."""
    primer = _primer_nombre(nombre)
    fmt_monto = f"${monto_cedido:,.0f}".replace(",", ".")
    tasa_color = "#059669" if tasa_aprobacion >= 85 else "#D97706" if tasa_aprobacion >= 60 else "#DC2626"
    body = f"""
    <h2 style="margin:0 0 6px;font-size:24px;font-weight:800;color:#0D1B2E;letter-spacing:-0.5px">
      Resumen de {mes} {anio}
    </h2>
    <p style="margin:0 0 26px;font-size:14px;color:#5A6A7E">
      Hola {primer}, aquí está tu actividad del mes anterior en FinPro Capital.
    </p>

    <table cellpadding="0" cellspacing="0" width="100%" style="margin-bottom:22px">
      <tr>
        <td width="48%" style="padding-right:8px">
          <div style="background:#EEF3FF;border-radius:12px;padding:18px;text-align:center">
            <p style="margin:0 0 4px;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px">Facturas registradas</p>
            <p style="margin:0;font-size:34px;font-weight:800;color:#1A4FD6">{total_facturas}</p>
          </div>
        </td>
        <td width="48%" style="padding-left:8px">
          <div style="background:#ECFDF5;border-radius:12px;padding:18px;text-align:center">
            <p style="margin:0 0 4px;font-size:10px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px">Cesiones aceptadas</p>
            <p style="margin:0;font-size:34px;font-weight:800;color:#059669">{total_cesiones}</p>
          </div>
        </td>
      </tr>
    </table>

    <div style="background:#F4F6FA;border-radius:12px;padding:22px;margin-bottom:22px;text-align:center">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9DAEC0;text-transform:uppercase;letter-spacing:0.5px">Monto total cedido en {mes}</p>
      <p style="margin:0;font-size:36px;font-weight:800;color:#0D1B2E;letter-spacing:-1.5px">{fmt_monto} COP</p>
      <p style="margin:8px 0 0;font-size:13px;font-weight:700;color:{tasa_color}">
        Tasa de aprobación DIAN: {tasa_aprobacion:.0f}%
      </p>
    </div>

    {_btn("Ver reporte completo &rarr;", f"{APP_URL}/app")}
    """
    return send_email(
        to,
        f"📊 Tu resumen de {mes} {anio} en FinPro Capital",
        _base(f"Reporte {mes} {anio}", f"Tu resumen de actividad de {mes} {anio}", body),
    )
