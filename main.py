from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from routers import facturas, cesion, autenticacion, consultas, reportes
from config import settings

app = FastAPI(title="RADIAN API", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
)


# ── CSRF middleware (double-submit cookie) ────────────────────────────────────
# Aplica a todos los endpoints mutantes (/api/v1/**) autenticados por cookie.
# Exento: Bearer token, GET/HEAD/OPTIONS, /auth/token, /auth/registro, /auth/logout
_CSRF_EXEMPT = {"/api/v1/auth/token", "/api/v1/auth/registro", "/api/v1/auth/logout"}

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    if (
        request.method not in ("POST", "PUT", "DELETE", "PATCH")
        or not request.url.path.startswith("/api/v1/")
        or request.url.path in _CSRF_EXEMPT
        or request.headers.get("Authorization", "").startswith("Bearer ")
    ):
        return await call_next(request)

    session_cookie = request.cookies.get("radian_session")
    if not session_cookie:
        return await call_next(request)  # Sin sesión → auth fallará después

    csrf_header = request.headers.get("X-CSRF-Token", "")
    csrf_cookie = request.cookies.get("radian_csrf", "")
    if not csrf_header or not csrf_cookie:
        return JSONResponse(status_code=403, content={"detail": "CSRF token requerido"})
    try:
        import secrets as _s
        valid = _s.compare_digest(csrf_header, csrf_cookie)
    except Exception:
        valid = False
    if not valid:
        return JSONResponse(status_code=403, content={"detail": "CSRF token inválido"})

    return await call_next(request)


app.include_router(autenticacion.router, prefix="/api/v1/auth",     tags=["Autenticacion"])
app.include_router(facturas.router,      prefix="/api/v1/facturas",  tags=["Facturas"])
app.include_router(cesion.router,        prefix="/api/v1/cesion",    tags=["Cesion RADIAN"])
app.include_router(consultas.router,     prefix="/api/v1/consultas", tags=["Consultas DIAN"])
app.include_router(reportes.router,      prefix="/api/v1/reportes",  tags=["Reportes Excel"])

UI = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FINPRO CAPITAL — RADIAN</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#F4F6FA;
  --surface:#FFFFFF;
  --border:#E4E9F0;
  --border-soft:#F0F4F8;
  --text-primary:#0D1B2E;
  --text-secondary:#5A6A7E;
  --text-muted:#9DAEC0;
  --brand:#1A4FD6;
  --brand-dark:#1340B0;
  --brand-light:#EEF3FF;
  --brand-glow:rgba(26,79,214,0.12);
  --teal:#0891B2;
  --green:#059669;
  --green-bg:#ECFDF5;
  --gold:#D97706;
  --gold-bg:#FFFBEB;
  --red:#DC2626;
  --red-bg:#FEF2F2;
  --purple:#7C3AED;
  --purple-bg:#F5F3FF;
  --sidebar:#0B1829;
  --sidebar-hover:rgba(255,255,255,0.06);
  --sidebar-active:rgba(99,152,255,0.15);
  --sidebar-text:rgba(255,255,255,0.55);
  --radius:10px;
  --radius-lg:14px;
  --radius-sm:6px;
  --shadow:0 1px 3px rgba(13,27,46,0.06),0 4px 16px rgba(13,27,46,0.04);
  --shadow-md:0 4px 16px rgba(13,27,46,0.1),0 1px 4px rgba(13,27,46,0.06);
  --shadow-lg:0 12px 40px rgba(13,27,46,0.15),0 2px 8px rgba(13,27,46,0.08);
  --font:'Inter',system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--text-primary);min-height:100vh;-webkit-font-smoothing:antialiased}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:99px}
::-webkit-scrollbar-thumb:hover{background:var(--text-muted)}

/* ─── AUTH SCREEN ─── */
#auth-screen{display:flex;min-height:100vh}
.auth-left{flex:1;background:linear-gradient(145deg,#071120 0%,#0F2554 40%,#1A4FD6 100%);display:flex;flex-direction:column;justify-content:center;align-items:center;padding:60px;position:relative;overflow:hidden}
.auth-left::before{content:'';position:absolute;inset:0;background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23FFFFFF' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")}
.auth-left-content{position:relative;z-index:1;max-width:400px;width:100%}
.auth-brand{font-size:32px;font-weight:900;color:#fff;letter-spacing:-1px;margin-bottom:6px}
.auth-brand em{font-style:normal;color:#5EAEFF}
.auth-tagline{font-size:14px;color:rgba(255,255,255,0.45);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:48px}
.auth-feature{display:flex;gap:14px;align-items:flex-start;margin-bottom:24px}
.auth-feature-icon{width:36px;height:36px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);border-radius:9px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.auth-feature-title{font-size:14px;font-weight:600;color:#fff;margin-bottom:2px}
.auth-feature-desc{font-size:12px;color:rgba(255,255,255,0.4);line-height:1.5}

.auth-right{width:480px;background:#fff;display:flex;align-items:center;justify-content:center;padding:48px 56px;overflow-y:auto}
.auth-form-wrap{width:100%}
.auth-form-brand{font-size:22px;font-weight:900;color:var(--text-primary);letter-spacing:-0.5px;margin-bottom:4px}
.auth-form-brand em{font-style:normal;color:var(--brand)}
.auth-form-sub{font-size:12px;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:36px}
.auth-title{font-size:22px;font-weight:800;color:var(--text-primary);margin-bottom:4px;letter-spacing:-0.3px}
.auth-desc{font-size:13px;color:var(--text-secondary);margin-bottom:28px;line-height:1.5}

.fg{display:flex;flex-direction:column;gap:5px;margin-bottom:14px}
.fg label{font-size:11px;font-weight:700;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.6px}
.fg input,.fg select,.fg textarea{padding:11px 14px;border:1.5px solid var(--border);border-radius:var(--radius);font-size:14px;font-family:var(--font);color:var(--text-primary);background:var(--bg);outline:none;transition:.18s;width:100%}
.fg input:focus,.fg select:focus,.fg textarea:focus{border-color:var(--brand);background:#fff;box-shadow:0 0 0 4px var(--brand-glow)}
.fg input::placeholder{color:var(--text-muted)}
.fg .hint{font-size:11px;color:var(--text-muted);margin-top:2px}

.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.form-row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}

.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 18px;border-radius:var(--radius);font-size:13px;font-weight:600;cursor:pointer;border:none;font-family:var(--font);transition:.18s;white-space:nowrap;text-decoration:none}
.btn:active{transform:scale(0.98)}
.btn-primary{background:var(--brand);color:#fff}
.btn-primary:hover{background:var(--brand-dark)}
.btn-ghost{background:transparent;border:1.5px solid var(--border);color:var(--text-secondary)}
.btn-ghost:hover{border-color:var(--brand);color:var(--brand);background:var(--brand-light)}
.btn-success{background:var(--green);color:#fff}
.btn-success:hover{background:#047857}
.btn-danger{background:var(--red-bg);border:1.5px solid #FECACA;color:var(--red)}
.btn-danger:hover{background:#FEE2E2}
.btn-sm{padding:6px 13px;font-size:12px;border-radius:var(--radius-sm)}
.btn-lg{padding:14px 24px;font-size:15px;border-radius:var(--radius)}
.btn-block{width:100%}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none!important}

.auth-submit{width:100%;padding:14px;background:linear-gradient(135deg,var(--brand),var(--teal));color:#fff;border:none;border-radius:var(--radius);font-size:15px;font-weight:700;cursor:pointer;font-family:var(--font);margin-top:8px;transition:.18s;letter-spacing:-0.2px}
.auth-submit:hover{box-shadow:0 6px 20px rgba(26,79,214,0.35);transform:translateY(-1px)}
.auth-submit:active{transform:translateY(0)}
.auth-submit:disabled{opacity:.6;cursor:not-allowed;transform:none;box-shadow:none}

.auth-toggle{text-align:center;margin-top:22px;font-size:13px;color:var(--text-muted)}
.auth-toggle a{color:var(--brand);font-weight:600;cursor:pointer;text-decoration:none}
.auth-toggle a:hover{text-decoration:underline}

.err-box{background:var(--red-bg);color:var(--red);border:1px solid #FECACA;border-radius:var(--radius-sm);padding:10px 14px;font-size:13px;margin-bottom:16px;display:none;align-items:center;gap:8px}
.err-box.show{display:flex}

/* ─── APP LAYOUT ─── */
#app-screen{display:none;min-height:100vh}
.layout{display:flex;min-height:100vh}
.sidebar{width:248px;background:var(--sidebar);display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:100;transition:.25s}
.sidebar-header{padding:20px 16px 14px}
.s-brand{font-size:19px;font-weight:900;color:#fff;letter-spacing:-0.5px;line-height:1}
.s-brand em{font-style:normal;color:#5EAEFF}
.s-version{font-size:10px;color:rgba(255,255,255,0.25);margin-top:3px;text-transform:uppercase;letter-spacing:1.5px}
.s-status{margin:0 10px 12px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);border-radius:8px;padding:9px 12px;display:flex;align-items:center;gap:9px}
.s-dot{width:7px;height:7px;border-radius:50%;background:#10B981;flex-shrink:0;animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.4)}50%{box-shadow:0 0 0 5px rgba(16,185,129,0)}}
.s-dot-text{font-size:11px;color:#34D399;font-weight:600}

.nav-section{padding:14px 16px 5px;font-size:10px;color:rgba(255,255,255,0.2);text-transform:uppercase;letter-spacing:2px;font-weight:700}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;margin:1px 8px;cursor:pointer;font-size:13px;font-weight:500;color:var(--sidebar-text);transition:.15s;border:1px solid transparent;text-decoration:none;user-select:none}
.nav-item:hover{background:var(--sidebar-hover);color:rgba(255,255,255,0.85)}
.nav-item.active{background:var(--sidebar-active);border-color:rgba(99,152,255,0.2);color:#fff}
.nav-item.active svg{opacity:1}
.nav-item svg{width:16px;height:16px;flex-shrink:0;opacity:.5;transition:.15s}
.nav-item:hover svg,.nav-item.active svg{opacity:1}
.nav-label{flex:1}
.nav-badge{background:var(--brand);color:#fff;font-size:9px;font-weight:800;padding:2px 6px;border-radius:99px;min-width:18px;text-align:center}

.sidebar-footer{margin-top:auto;padding:14px 10px}
.user-card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:12px}
.user-card-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.avatar{width:36px;height:36px;background:linear-gradient(135deg,var(--brand),var(--teal));border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;color:#fff;flex-shrink:0}
.user-name{font-size:13px;font-weight:600;color:rgba(255,255,255,0.9);line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.user-nit{font-size:10px;color:rgba(255,255,255,0.3);margin-top:2px}
.logout-btn{width:100%;padding:8px;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);color:#F87171;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;font-family:var(--font);transition:.15s;display:flex;align-items:center;justify-content:center;gap:6px}
.logout-btn:hover{background:rgba(239,68,68,0.15)}

/* ─── MAIN CONTENT ─── */
.main{margin-left:248px;flex:1;display:flex;flex-direction:column;min-height:100vh}
.topbar{background:var(--surface);border-bottom:1px solid var(--border);padding:0 28px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:50}
.topbar-left{display:flex;flex-direction:column}
.page-title{font-size:16px;font-weight:700;letter-spacing:-0.3px;color:var(--text-primary)}
.page-subtitle{font-size:12px;color:var(--text-muted);margin-top:1px}
.topbar-right{display:flex;gap:8px;align-items:center}

.content{padding:28px 28px;flex:1}

/* ─── CARDS ─── */
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow);overflow:hidden}
.card-head{padding:16px 20px;border-bottom:1px solid var(--border-soft);display:flex;align-items:center;justify-content:space-between}
.card-title{font-size:14px;font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:8px}
.card-title svg{width:16px;height:16px;color:var(--brand)}
.card-subtitle{font-size:12px;color:var(--text-muted);font-weight:400;margin-top:2px}
.card-body{padding:20px}
.card-link{font-size:12px;color:var(--brand);font-weight:600;cursor:pointer;display:flex;align-items:center;gap:4px}
.card-link:hover{text-decoration:underline}

/* ─── STATS ─── */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px 22px;box-shadow:var(--shadow);position:relative;overflow:hidden;transition:.18s}
.stat-card:hover{box-shadow:var(--shadow-md);transform:translateY(-1px)}
.stat-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;margin-bottom:14px}
.stat-icon svg{width:20px;height:20px}
.si-blue{background:#EEF3FF;color:var(--brand)}
.si-green{background:var(--green-bg);color:var(--green)}
.si-gold{background:var(--gold-bg);color:var(--gold)}
.si-purple{background:var(--purple-bg);color:var(--purple)}
.stat-value{font-size:32px;font-weight:800;color:var(--text-primary);letter-spacing:-1px;line-height:1}
.stat-label{font-size:12px;color:var(--text-secondary);margin-top:5px;font-weight:500}
.stat-trend{font-size:11px;color:var(--text-muted);margin-top:4px}
.stat-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;border-radius:0 0 2px 2px}
.stat-card.c1::after{background:linear-gradient(90deg,var(--brand),var(--teal))}
.stat-card.c2::after{background:linear-gradient(90deg,var(--green),#34D399)}
.stat-card.c3::after{background:linear-gradient(90deg,var(--gold),#FCD34D)}
.stat-card.c4::after{background:linear-gradient(90deg,var(--purple),#A78BFA)}

/* ─── GRID LAYOUTS ─── */
.grid-2{display:grid;grid-template-columns:1.5fr 1fr;gap:20px}
.grid-2-eq{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.grid-col{display:flex;flex-direction:column;gap:20px}
.mb-20{margin-bottom:20px}

/* ─── TABLE ─── */
.tbl{width:100%;border-collapse:collapse}
.tbl th{padding:10px 16px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);border-bottom:1px solid var(--border);font-weight:700;background:var(--border-soft)}
.tbl td{padding:13px 16px;font-size:13px;border-bottom:1px solid var(--border-soft);vertical-align:middle;color:var(--text-secondary)}
.tbl tbody tr:last-child td{border-bottom:none}
.tbl tbody tr{transition:.12s}
.tbl tbody tr:hover td{background:#FAFBFD}
.td-primary{font-size:13px;font-weight:600;color:var(--text-primary);margin-bottom:2px}
.td-mono{font-size:11px;color:var(--text-muted);font-family:monospace}
.td-amount{font-size:14px;font-weight:700;color:var(--text-primary);font-variant-numeric:tabular-nums}
.empty-state{text-align:center;padding:48px 20px;color:var(--text-muted)}
.empty-icon{font-size:40px;margin-bottom:12px;opacity:.4}
.empty-text{font-size:14px;font-weight:500;color:var(--text-secondary);margin-bottom:6px}
.empty-sub{font-size:12px}

/* ─── ONBOARDING WIZARD ─── */
.wiz-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:none;align-items:center;justify-content:center;backdrop-filter:blur(4px);padding:20px}
.wiz-overlay.show{display:flex}
.wiz-box{background:#fff;border-radius:20px;width:100%;max-width:580px;overflow:hidden;box-shadow:0 32px 80px rgba(0,0,0,.25);animation:wiz-in .3s ease}
@keyframes wiz-in{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
.wiz-prog-bar{height:5px;background:var(--border-soft)}
.wiz-prog-fill{height:5px;background:linear-gradient(90deg,var(--brand),#0891B2);transition:width .4s ease}
.wiz-body{padding:36px 36px 24px}
.wiz-step-tag{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--brand);margin-bottom:10px}
.wiz-title{font-size:22px;font-weight:800;color:var(--text-primary);letter-spacing:-.5px;line-height:1.25;margin-bottom:10px}
.wiz-sub{font-size:14px;color:var(--text-secondary);line-height:1.7;margin-bottom:24px}
.wiz-visual{background:linear-gradient(135deg,#F0F5FF,#EEF3FF);border-radius:14px;padding:20px 22px;margin-bottom:22px;display:flex;flex-direction:column;gap:16px}
.wiz-vstep{display:flex;align-items:flex-start;gap:14px}
.wiz-vstep-num{width:34px;height:34px;border-radius:50%;background:var(--brand);color:#fff;font-size:13px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.wiz-vstep-name{font-size:13px;font-weight:700;color:var(--text-primary);margin-bottom:2px}
.wiz-vstep-desc{font-size:12px;color:var(--text-secondary);line-height:1.55}
.wiz-footer{display:flex;align-items:center;justify-content:space-between;padding:0 36px 28px;gap:12px}
.wiz-dots{display:flex;gap:6px}
.wiz-dot{width:8px;height:8px;border-radius:50%;background:var(--border);transition:.25s}
.wiz-dot.active{background:var(--brand);width:22px;border-radius:4px}
.wiz-form .wfg{margin-bottom:14px}
.wiz-form .wfg label{font-size:12px;font-weight:600;color:var(--text-primary);display:flex;align-items:center;gap:6px;margin-bottom:5px}
.wiz-form .wfg input{width:100%;padding:9px 12px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;font-family:var(--font);outline:none;transition:.15s}
.wiz-form .wfg input:focus{border-color:var(--brand);box-shadow:0 0 0 3px rgba(26,79,214,.08)}
.wiz-form .wfg .whint{font-size:11px;color:var(--text-muted);margin-top:4px}
.wiz-checklist{display:flex;flex-direction:column;gap:10px}
.wiz-ci{display:flex;align-items:center;gap:14px;background:#F0FDF4;border:1px solid #A7F3D0;border-radius:12px;padding:14px 16px}
.wiz-ci-icon{width:34px;height:34px;background:#D1FAE5;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#059669;font-size:16px}
.wiz-ci-label{font-size:13px;font-weight:600;color:var(--text-primary)}
.wiz-ci-sub{font-size:11px;color:var(--text-secondary);margin-top:2px}
.wiz-skip{font-size:12px;color:var(--text-muted);cursor:pointer;text-decoration:underline;padding:4px}
.wiz-skip:hover{color:var(--text-secondary)}

/* ─── CHECKLIST WIDGET ─── */
.obw{background:#fff;border:1.5px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:20px}
.obw-header{padding:14px 18px 10px;display:flex;align-items:center;justify-content:space-between}
.obw-title{font-size:13px;font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:8px}
.obw-pct{font-size:12px;font-weight:700;color:var(--brand)}
.obw-bar-wrap{height:4px;background:var(--border-soft);margin:0 18px 12px;border-radius:99px}
.obw-bar{height:4px;background:linear-gradient(90deg,var(--brand),#0891B2);border-radius:99px;transition:width .5s ease}
.obw-items{padding:0 18px 14px;display:flex;flex-direction:column;gap:6px}
.obw-item{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;cursor:pointer;transition:.12s;text-decoration:none}
.obw-item:hover{background:var(--bg-light)}
.obw-item.done .obw-cb{background:var(--green);border-color:var(--green)}
.obw-item.done .obw-lbl{text-decoration:line-through;color:var(--text-muted)}
.obw-cb{width:18px;height:18px;border:2px solid var(--border);border-radius:5px;flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:.2s}
.obw-cb-check{display:none;width:9px;height:9px}
.obw-item.done .obw-cb-check{display:block}
.obw-lbl{font-size:12px;color:var(--text-secondary);font-weight:500}
.obw-dismiss{text-align:center;padding:0 18px 12px}
.obw-dismiss a{font-size:11px;color:var(--text-muted);cursor:pointer;text-decoration:underline}

/* ─── TOOLTIPS ─── */
.tip{position:relative;display:inline-flex;margin-left:5px;vertical-align:middle}
.tip-btn{width:15px;height:15px;border-radius:50%;background:var(--brand-light);color:var(--brand);font-size:9px;font-weight:900;display:inline-flex;align-items:center;justify-content:center;cursor:default;border:none;font-family:var(--font);line-height:1}
.tip-box{position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);background:#0D1B2E;color:#fff;font-size:12px;line-height:1.6;padding:10px 14px;border-radius:10px;width:250px;pointer-events:none;opacity:0;transition:.15s;z-index:200;font-weight:400;white-space:normal}
.tip-box::after{content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);border:6px solid transparent;border-top-color:#0D1B2E}
.tip:hover .tip-box,.tip:focus-within .tip-box{opacity:1}

/* ─── EMPTY STATES MEJORADOS ─── */
.empty-hero{text-align:center;padding:56px 32px}
.empty-hero-icon{width:64px;height:64px;background:var(--brand-light);border-radius:16px;display:flex;align-items:center;justify-content:center;margin:0 auto 18px}
.empty-hero-title{font-size:17px;font-weight:700;color:var(--text-primary);margin-bottom:8px}
.empty-hero-sub{font-size:13px;color:var(--text-secondary);max-width:360px;margin:0 auto 22px;line-height:1.65}

/* ─── BADGES ─── */
.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:99px;font-size:10px;font-weight:700;letter-spacing:0.3px;white-space:nowrap}
.badge::before{content:'';width:5px;height:5px;border-radius:50%;background:currentColor;flex-shrink:0}
.b-green{background:var(--green-bg);color:var(--green)}
.b-blue{background:var(--brand-light);color:var(--brand)}
.b-gold{background:var(--gold-bg);color:var(--gold)}
.b-red{background:var(--red-bg);color:var(--red)}
.b-purple{background:var(--purple-bg);color:var(--purple)}
.b-gray{background:var(--border-soft);color:var(--text-secondary)}
.b-teal{background:#F0FDFF;color:var(--teal)}

/* ─── PROCESS STEPS ─── */
.steps{display:flex;flex-direction:column;gap:0}
.step{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid var(--border-soft)}
.step:last-child{border:none;padding-bottom:0}
.step-circle{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0;margin-top:1px}
.sc-done{background:var(--green-bg);color:var(--green);border:1.5px solid #A7F3D0}
.sc-active{background:var(--brand-light);color:var(--brand);border:1.5px solid #BFDBFE}
.sc-pending{background:var(--border-soft);color:var(--text-muted);border:1.5px solid var(--border)}
.step-title{font-size:13px;font-weight:600;color:var(--text-primary)}
.step-desc{font-size:11px;color:var(--text-muted);margin-top:2px;line-height:1.5}

/* ─── FILTER BAR ─── */
.filter-bar{display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap}
.filter-btn{padding:7px 16px;border-radius:99px;font-size:12px;font-weight:600;border:1.5px solid var(--border);background:var(--surface);cursor:pointer;transition:.15s;font-family:var(--font);color:var(--text-secondary)}
.filter-btn:hover{border-color:var(--brand);color:var(--brand)}
.filter-btn.active{background:var(--brand);color:#fff;border-color:var(--brand)}

/* ─── RESPONSE BOX ─── */
.resp-box{background:#0D1117;border-radius:var(--radius);padding:16px;font-family:'SFMono-Regular',Consolas,monospace;font-size:12px;line-height:1.7;margin-top:14px;display:none;max-height:280px;overflow-y:auto;border:1px solid rgba(255,255,255,0.05)}
.resp-box.show{display:block}
.resp-ok{color:#34D399;font-weight:700;margin-bottom:6px;font-size:13px}
.resp-err{color:#F87171;font-weight:700}
.resp-data{color:#93C5FD;margin-top:6px;white-space:pre-wrap;word-break:break-all}

/* ─── STATUS ITEMS ─── */
.status-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border-soft);font-size:13px}
.status-row:last-child{border:none;padding-bottom:0}
.status-label{color:var(--text-secondary);font-weight:500}

/* ─── TABS ─── */
.tab-content{display:none}
.tab-content.active{display:block}

/* ─── SPINNER ─── */
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin .65s linear infinite;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}

/* ─── TOAST ─── */
#toast{position:fixed;bottom:24px;right:24px;padding:13px 20px;border-radius:10px;font-size:13px;font-weight:600;color:#fff;z-index:9999;transform:translateY(80px) scale(0.95);opacity:0;transition:.25s cubic-bezier(.34,1.56,.64,1);pointer-events:none;display:flex;align-items:center;gap:9px;box-shadow:var(--shadow-lg)}
#toast.show{transform:translateY(0) scale(1);opacity:1}
#toast.ok{background:#059669}
#toast.err{background:#DC2626}
#toast.info{background:var(--brand)}

/* ─── MODAL ─── */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:1000;display:none;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
.modal-overlay.show{display:flex}
.modal{background:#fff;border-radius:var(--radius-lg);box-shadow:var(--shadow-lg);width:640px;max-width:calc(100vw - 40px);max-height:80vh;overflow-y:auto}
.modal-head{padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:#fff;z-index:1}
.modal-title{font-size:15px;font-weight:700;color:var(--text-primary)}
.modal-close{width:30px;height:30px;border-radius:var(--radius-sm);background:var(--border-soft);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;color:var(--text-secondary);font-size:16px;transition:.15s}
.modal-close:hover{background:var(--border);color:var(--text-primary)}
.modal-body{padding:24px}
.detail-row{display:flex;gap:8px;padding:10px 0;border-bottom:1px solid var(--border-soft)}
.detail-row:last-child{border:none}
.detail-key{font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;width:160px;flex-shrink:0;padding-top:1px}
.detail-val{font-size:13px;color:var(--text-primary);word-break:break-all;font-weight:500}
.detail-val.mono{font-family:monospace;font-size:12px;background:var(--border-soft);padding:3px 8px;border-radius:4px;color:var(--text-secondary)}

/* ─── DIVIDER ─── */
.divider{height:1px;background:var(--border-soft);margin:20px 0}

/* ─── API EXPLORER ─── */
.ep-list{display:flex;flex-direction:column}
.ep-item{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-soft)}
.ep-item:last-child{border:none}
.method{padding:3px 8px;border-radius:5px;font-size:10px;font-weight:800;min-width:44px;text-align:center;font-family:monospace;letter-spacing:0.3px}
.m-post{background:#ECFDF5;color:#059669}
.m-get{background:var(--brand-light);color:var(--brand)}
.m-put{background:var(--gold-bg);color:var(--gold)}
.ep-info{flex:1}
.ep-path{font-family:monospace;font-size:12px;color:var(--text-primary);font-weight:600}
.ep-desc{font-size:11px;color:var(--text-muted);margin-top:1px}

/* ─── DIVIDER LABEL ─── */
.section-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--text-muted);margin-bottom:14px}

/* ─── ACCOUNTING / CONTABILIDAD ─── */
.puc-code{font-family:monospace;font-size:11px;background:var(--border-soft);padding:2px 8px;border-radius:4px;color:var(--brand);font-weight:700;white-space:nowrap}
.journal-debit{color:var(--text-primary);font-weight:600}
.journal-credit{color:var(--text-secondary);padding-left:20px}
.journal-row-debit td{background:#FAFBFF}
.journal-row-credit td{background:#FEFEFE}
.journal-ref{font-family:monospace;font-size:10px;color:var(--text-muted)}
.amount-debit{font-variant-numeric:tabular-nums;font-weight:700;color:var(--text-primary);font-size:13px}
.amount-credit{font-variant-numeric:tabular-nums;font-weight:700;color:var(--text-secondary);font-size:13px}
.balance-ok{color:var(--green);font-weight:700}
.balance-err{color:var(--red);font-weight:700}

/* ─── CARTERA / AGING ─── */
.aging-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}
.aging-card{border-radius:var(--radius);padding:16px 18px;border:1px solid var(--border);background:var(--surface);text-align:center;position:relative;overflow:hidden}
.aging-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px}
.aging-0::after{background:var(--green)}
.aging-30::after{background:var(--gold)}
.aging-60::after{background:#F97316}
.aging-90::after{background:var(--red)}
.aging-over::after{background:#7F1D1D}
.aging-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin-bottom:8px}
.aging-amount{font-size:20px;font-weight:800;letter-spacing:-0.5px;line-height:1}
.aging-count{font-size:11px;color:var(--text-muted);margin-top:4px}
.aging-bar-row{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.aging-bar-label{font-size:11px;color:var(--text-secondary);width:90px;flex-shrink:0;font-weight:500}
.aging-bar-track{flex:1;height:8px;background:var(--border-soft);border-radius:99px;overflow:hidden}
.aging-bar-fill{height:100%;border-radius:99px;transition:.6s ease}
.aging-bar-val{font-size:11px;font-weight:700;color:var(--text-primary);width:80px;text-align:right;flex-shrink:0}

/* ─── SVG CHARTS ─── */
.chart-wrap{position:relative;width:100%}
.chart-wrap svg{width:100%;display:block}
.chart-legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px;padding:0 4px}
.legend-item{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text-secondary)}
.legend-dot{width:10px;height:10px;border-radius:3px;flex-shrink:0}

/* ─── FLUJO DE CAJA ─── */
.cashflow-month{display:flex;gap:14px;align-items:center;padding:12px 0;border-bottom:1px solid var(--border-soft)}
.cashflow-month:last-child{border:none}
.cashflow-month-label{font-size:12px;font-weight:700;color:var(--text-primary);width:80px;flex-shrink:0}
.cashflow-bar-track{flex:1;height:10px;background:var(--border-soft);border-radius:99px;overflow:hidden}
.cashflow-bar-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--brand),var(--teal));transition:.5s ease}
.cashflow-amount{font-size:12px;font-weight:700;color:var(--text-primary);width:100px;text-align:right;flex-shrink:0}
.cashflow-count{font-size:10px;color:var(--text-muted);width:60px;text-align:right;flex-shrink:0}

/* ─── P&L / ESTADO RESULTADOS ─── */
.pnl-section{margin-bottom:20px}
.pnl-section-title{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:2px;color:var(--text-muted);padding:10px 0 6px;border-bottom:2px solid var(--border)}
.pnl-row{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--border-soft);font-size:13px}
.pnl-row:last-child{border:none}
.pnl-row-total{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-top:2px solid var(--border);font-size:15px;font-weight:800;color:var(--text-primary)}
.pnl-label{color:var(--text-secondary);font-weight:500}
.pnl-val{font-weight:700;font-variant-numeric:tabular-nums}
.pnl-positive{color:var(--green)}
.pnl-negative{color:var(--red)}
.pnl-neutral{color:var(--text-primary)}
.kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;text-align:center}
.kpi-val{font-size:28px;font-weight:800;letter-spacing:-1px;color:var(--text-primary)}
.kpi-label{font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-top:4px;font-weight:600}
.kpi-sub{font-size:12px;color:var(--text-secondary);margin-top:6px}

/* ─── CESIONES LIST ─── */
.ces-estado-chip{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:99px;font-size:10px;font-weight:700}

/* ─── HAMBURGER BUTTON (hidden on desktop) ─── */
.mob-hamburger{display:none;align-items:center;justify-content:center;width:36px;height:36px;border:1.5px solid var(--border);border-radius:var(--radius-sm);background:transparent;cursor:pointer;flex-shrink:0;margin-right:12px;transition:.15s}
.mob-hamburger:hover{background:var(--bg);border-color:var(--brand)}
.mob-hamburger span{display:block;width:18px;height:1.5px;background:var(--text-secondary);border-radius:2px;margin:3px auto;transition:.25s}

/* ─── DRAWER OVERLAY ─── */
.drawer-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:250;backdrop-filter:blur(2px)}
.drawer-overlay.show{display:block}

/* ─── BOTTOM NAV (hidden on desktop) ─── */
.bottom-nav{display:none;position:fixed;bottom:0;left:0;right:0;height:58px;background:var(--surface);border-top:1px solid var(--border);z-index:200;box-shadow:0 -4px 20px rgba(13,27,46,.07)}
.bn-item{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--text-muted);cursor:pointer;transition:.15s;border:none;background:transparent;font-family:var(--font);padding:6px 2px;text-decoration:none;-webkit-tap-highlight-color:transparent}
.bn-item svg{width:20px;height:20px;flex-shrink:0;transition:.15s}
.bn-item.active,.bn-item:hover{color:var(--brand)}
.bn-item.active svg,.bn-item:hover svg{color:var(--brand)}

/* ─── TABLE → CARD RESPONSIVE ─── */
.tbl-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}

/* ─── CUFE TEXTAREA ─── */
.cufe-ta{font-family:monospace;font-size:12px;resize:vertical;min-height:52px;line-height:1.5;word-break:break-all}

/* ─── RESPONSIVE: ≤1024px tablet ─── */
@media(max-width:1024px){
  .sidebar{width:220px}
  .main{margin-left:220px}
  .stats-grid{grid-template-columns:1fr 1fr}
  .form-row-3{grid-template-columns:1fr 1fr}
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
}

/* ─── RESPONSIVE: ≤768px mobile/tablet ─── */
@media(max-width:768px){
  /* ── Auth ── */
  .auth-left{display:none}
  .auth-right{width:100%;padding:32px 24px;min-height:100vh}

  /* ── Sidebar → drawer ── */
  .sidebar{transform:translateX(-260px);width:260px;transition:.28s cubic-bezier(.4,0,.2,1);z-index:300;box-shadow:none}
  .sidebar.drawer-open{transform:translateX(0);box-shadow:8px 0 60px rgba(0,0,0,.35)}
  .main{margin-left:0}
  .topbar{padding:0 14px;position:sticky;top:0;z-index:100}
  .mob-hamburger{display:flex!important}

  /* ── Bottom nav visible ── */
  .bottom-nav{display:flex!important}
  .content{padding:16px 14px 74px}/* leave room for bottom nav */

  /* ── Layouts ── */
  .stats-grid{grid-template-columns:1fr 1fr}
  .grid-2,.grid-2-eq{grid-template-columns:1fr}
  .form-row,.form-row-3{grid-template-columns:1fr!important}
  .aging-grid{grid-template-columns:1fr 1fr}
  .kpi-grid{grid-template-columns:1fr 1fr}
  .grid-col{gap:14px}

  /* ── Cards ── */
  .card-body{padding:14px}
  .card-head{padding:12px 14px}

  /* ── Topbar right buttons ── */
  .topbar-right .btn span,.topbar-right .btn-ghost{display:none}
  .topbar-right .btn-primary{padding:8px 14px;font-size:12px}

  /* ── Tables → cards on mobile ── */
  table.tbl-mobile{display:block}
  table.tbl-mobile thead{display:none}
  table.tbl-mobile tbody{display:flex;flex-direction:column;gap:10px}
  table.tbl-mobile tbody tr{
    display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;
    background:var(--surface);border-radius:var(--radius-lg);
    border:1px solid var(--border);padding:14px 16px;
    box-shadow:var(--shadow);cursor:pointer
  }
  table.tbl-mobile tbody td{
    display:flex;flex-direction:column;padding:0;
    border:none!important;font-size:13px;vertical-align:top
  }
  table.tbl-mobile tbody td::before{
    content:attr(data-label);font-size:9px;font-weight:700;
    text-transform:uppercase;letter-spacing:.8px;
    color:var(--text-muted);margin-bottom:3px;display:block
  }
  table.tbl-mobile tbody td[data-full]{grid-column:1/-1}
  table.tbl-mobile tbody td[data-full]::before{display:none}
  /* action cells full-width, no label, row direction */
  table.tbl-mobile tbody td.td-actions{
    grid-column:1/-1;flex-direction:row;gap:8px;
    align-items:center;padding-top:8px;
    border-top:1px solid var(--border-soft)!important;margin-top:4px
  }
  table.tbl-mobile tbody td.td-actions::before{display:none}

  /* ── iOS zoom prevention ── */
  input,select,textarea{font-size:16px!important}
  .fg input,.fg select,.fg textarea{font-size:16px!important}
}

/* ─── RESPONSIVE: ≤480px small mobile ─── */
@media(max-width:480px){
  .stats-grid{grid-template-columns:1fr}
  .auth-right{padding:24px 16px}
  .kpi-grid{grid-template-columns:1fr}
  .aging-grid{grid-template-columns:1fr}
  table.tbl-mobile tbody tr{grid-template-columns:1fr}
  table.tbl-mobile tbody td[data-full]{grid-column:1}
  .wiz-box{max-height:95vh;overflow-y:auto}
  .topbar-right .btn-primary{display:none}/* only hamburger + title on tiny screens */
}
</style>
</head>
<body>

<!-- ═══ AUTH ═══ -->
<div id="auth-screen">
  <div class="auth-left">
    <div class="auth-left-content">
      <div class="auth-brand">FINPRO<em>CAPITAL</em></div>
      <div class="auth-tagline">Plataforma RADIAN · Endoso de Facturas</div>
      <div class="auth-feature">
        <div class="auth-feature-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:rgba(255,255,255,0.7)"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
        </div>
        <div>
          <div class="auth-feature-title">Evento 037 — RADIAN</div>
          <div class="auth-feature-desc">Cesión de facturas electrónicas firmada digitalmente y registrada en la plataforma DIAN en tiempo real.</div>
        </div>
      </div>
      <div class="auth-feature">
        <div class="auth-feature-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:rgba(255,255,255,0.7)"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        </div>
        <div>
          <div class="auth-feature-title">Respuesta instantánea</div>
          <div class="auth-feature-desc">Validación y confirmación de la DIAN en menos de 2 segundos. XML UBL 2.1 con SHA-384.</div>
        </div>
      </div>
      <div class="auth-feature">
        <div class="auth-feature-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:rgba(255,255,255,0.7)"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
        </div>
        <div>
          <div class="auth-feature-title">Trazabilidad completa</div>
          <div class="auth-feature-desc">Historial de cesiones, XMLs descargables y seguimiento de estado por CUDE.</div>
        </div>
      </div>
    </div>
  </div>
  <div class="auth-right">
    <div class="auth-form-wrap">
      <div class="auth-form-brand">FINPRO<em>CAPITAL</em></div>
      <div class="auth-form-sub">Sistema RADIAN · Colombia</div>

      <!-- LOGIN -->
      <div id="login-panel">
        <div class="auth-title">Bienvenido</div>
        <div class="auth-desc">Ingresa tus credenciales para acceder al sistema</div>
        <div class="err-box" id="login-err">
          <svg viewBox="0 0 20 20" fill="currentColor" style="width:16px;flex-shrink:0"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
          <span id="login-err-text"></span>
        </div>
        <div class="fg"><label>Correo electrónico</label><input id="l-email" type="email" placeholder="empresa@correo.com" autocomplete="email"/></div>
        <div class="fg"><label>Contraseña</label><input id="l-pass" type="password" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()" autocomplete="current-password"/></div>
        <button class="auth-submit" onclick="doLogin()" id="login-btn">Iniciar sesión</button>
        <div class="auth-toggle">¿No tienes cuenta? <a onclick="showPanel('register')">Crear empresa</a></div>
      </div>

      <!-- REGISTER -->
      <div id="register-panel" style="display:none">
        <div class="auth-title">Crear empresa</div>
        <div class="auth-desc">Registra tu empresa para acceder al sistema RADIAN</div>
        <div class="err-box" id="reg-err">
          <svg viewBox="0 0 20 20" fill="currentColor" style="width:16px;flex-shrink:0"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
          <span id="reg-err-text"></span>
        </div>
        <div class="form-row">
          <div class="fg"><label>Nombre empresa</label><input id="r-nombre" placeholder="MI EMPRESA SAS"/></div>
          <div class="fg"><label>NIT</label><input id="r-nit" placeholder="900.123.456-1"/></div>
        </div>
        <div class="form-row">
          <div class="fg"><label>Correo electrónico</label><input id="r-email" type="email" placeholder="empresa@correo.com"/></div>
          <div class="fg"><label>Teléfono de contacto</label><input id="r-tel" type="tel" placeholder="+57 300 000 0000"/></div>
        </div>
        <div class="fg"><label>Contraseña</label><input id="r-pass" type="password" placeholder="Mínimo 8 caracteres"/><div class="hint">Usa una combinación de letras, números y símbolos</div></div>
        <button class="auth-submit" onclick="doRegister()" id="reg-btn">Crear cuenta</button>
        <div class="auth-toggle">¿Ya tienes cuenta? <a onclick="showPanel('login')">Iniciar sesión</a></div>
      </div>
    </div>
  </div>
</div>

<!-- ═══ APP ═══ -->
<div id="app-screen">
<div class="layout">

<!-- SIDEBAR -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <div class="s-brand">FINPRO<em>CAPITAL</em></div>
    <div class="s-version">RADIAN · v1.0</div>
  </div>
  <div class="s-status">
    <div class="s-dot"></div>
    <span class="s-dot-text">DIAN Habilitación activa</span>
  </div>
  <div class="nav-section">Principal</div>
  <a class="nav-item active" id="nav-dashboard" onclick="showPage('dashboard')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
    <span class="nav-label">Dashboard</span>
  </a>
  <a class="nav-item" id="nav-facturas" onclick="showPage('facturas')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
    <span class="nav-label">Facturas</span>
  </a>
  <a class="nav-item" id="nav-registrar" onclick="showPage('registrar')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4v16m8-8H4"/></svg>
    <span class="nav-label">Registrar Factura</span>
  </a>
  <a class="nav-item" id="nav-cesion" onclick="showPage('cesion')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
    <span class="nav-label">Nueva Cesión</span>
  </a>
  <a class="nav-item" id="nav-cesiones" onclick="showPage('cesiones')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
    <span class="nav-label">Mis Cesiones</span>
  </a>
  <div class="nav-section">Contabilidad</div>
  <a class="nav-item" id="nav-cartera" onclick="showPage('cartera')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10h18M3 14h18M10 18H3M10 6H3m7 0h11M17 18h4"/></svg>
    <span class="nav-label">Cartera</span>
  </a>
  <a class="nav-item" id="nav-flujo" onclick="showPage('flujo')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
    <span class="nav-label">Flujo de Caja</span>
  </a>
  <a class="nav-item" id="nav-contabilidad" onclick="showPage('contabilidad')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
    <span class="nav-label">Libro Diario</span>
  </a>
  <a class="nav-item" id="nav-resultados" onclick="showPage('resultados')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
    <span class="nav-label">Estado de Resultados</span>
  </a>
  <a class="nav-item" id="nav-reportes" onclick="showPage('reportes')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
    <span class="nav-label">Reportes Excel</span>
  </a>
  <div class="nav-section">Herramientas</div>
  <a class="nav-item" id="nav-consultar" onclick="showPage('consultar')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <span class="nav-label">Consultar DIAN</span>
  </a>
  <a class="nav-item" id="nav-api" onclick="showPage('api')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
    <span class="nav-label">API Explorer</span>
  </a>
  <a class="nav-item" href="/openapi.json" target="_blank">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
    <span class="nav-label">OpenAPI JSON</span>
  </a>
  <div class="sidebar-footer">
    <div class="user-card">
      <div class="user-card-row">
        <div class="avatar" id="user-avatar">FP</div>
        <div style="overflow:hidden;flex:1">
          <div class="user-name" id="user-name">Cargando...</div>
          <div class="user-nit" id="user-nit">NIT —</div>
        </div>
      </div>
      <button class="logout-btn" onclick="doLogout()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
        Cerrar sesión
      </button>
    </div>
  </div>
</nav>

<!-- MAIN -->
<div class="main">
  <!-- DRAWER OVERLAY -->
  <div class="drawer-overlay" id="drawer-overlay" onclick="closeDrawer()"></div>

  <div class="topbar">
    <div class="topbar-left" style="display:flex;align-items:center">
      <button class="mob-hamburger" onclick="openDrawer()" aria-label="Menú">
        <span></span><span></span><span></span>
      </button>
      <div>
        <div class="page-title" id="page-title">Dashboard</div>
        <div class="page-subtitle" id="page-sub">Resumen general</div>
      </div>
    </div>
    <div class="topbar-right">
      <button class="btn btn-ghost btn-sm" onclick="showPage('registrar')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M12 4v16m8-8H4"/></svg>
        Registrar Factura
      </button>
      <button class="btn btn-primary btn-sm" onclick="showPage('cesion')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        Nueva Cesión
      </button>
    </div>
  </div>

  <div class="content">

    <!-- ══ DASHBOARD ══ -->
    <div id="page-dashboard" class="tab-content active">
      <div style="background:linear-gradient(135deg,#0F2554,#1A4FD6);border-radius:var(--radius-lg);padding:16px 24px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
        <div style="display:flex;align-items:center;gap:14px">
          <div style="width:40px;height:40px;background:rgba(255,255,255,0.12);border-radius:10px;display:flex;align-items:center;justify-content:center">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" style="width:20px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          </div>
          <div>
            <div style="font-size:13px;font-weight:700;color:#fff">Módulo Contabilidad activo</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.55);margin-top:2px" id="dash-ces-total">Cargando resumen financiero...</div>
          </div>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-sm" style="background:rgba(255,255,255,0.12);color:#fff;border:1px solid rgba(255,255,255,0.2)" onclick="showPage('cartera')">Ver Cartera</button>
          <button class="btn btn-sm" style="background:rgba(255,255,255,0.15);color:#fff;border:1px solid rgba(255,255,255,0.25)" onclick="showPage('resultados')">Estado de Resultados</button>
        </div>
      </div>
      <div class="stats-grid">
        <div class="stat-card c1">
          <div class="stat-icon si-blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          </div>
          <div class="stat-value" id="st-total">—</div>
          <div class="stat-label">Total Facturas</div>
          <div class="stat-trend">Registradas en el sistema</div>
        </div>
        <div class="stat-card c2">
          <div class="stat-icon si-green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div class="stat-value" id="st-cedidas">—</div>
          <div class="stat-label">Cedidas</div>
          <div class="stat-trend">Cesiones completadas</div>
        </div>
        <div class="stat-card c3">
          <div class="stat-icon si-gold">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg>
          </div>
          <div class="stat-value" id="st-titulos">—</div>
          <div class="stat-label">Títulos Valor</div>
          <div class="stat-trend">Habilitadas para ceder</div>
        </div>
        <div class="stat-card c4">
          <div class="stat-icon si-purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          </div>
          <div class="stat-value" id="st-proceso">—</div>
          <div class="stat-label">En Proceso</div>
          <div class="stat-trend">Enviadas a RADIAN</div>
        </div>
      </div>
      <!-- ONBOARDING CHECKLIST WIDGET -->
      <div class="obw" id="obw-widget">
        <div class="obw-header">
          <div class="obw-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px;color:var(--brand)"><path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg>
            Primeros pasos
          </div>
          <div class="obw-pct" id="obw-pct">0%</div>
        </div>
        <div class="obw-bar-wrap"><div class="obw-bar" id="obw-bar" style="width:0%"></div></div>
        <div class="obw-items">
          <div class="obw-item" id="ob-0" onclick="showPage('registrar')">
            <div class="obw-cb"><svg class="obw-cb-check" viewBox="0 0 12 12" fill="none" stroke="white" stroke-width="2.5"><polyline points="2,6 5,9 10,3"/></svg></div>
            <span class="obw-lbl">Registrar primera factura real</span>
          </div>
          <div class="obw-item" id="ob-1" onclick="showPage('facturas')">
            <div class="obw-cb"><svg class="obw-cb-check" viewBox="0 0 12 12" fill="none" stroke="white" stroke-width="2.5"><polyline points="2,6 5,9 10,3"/></svg></div>
            <span class="obw-lbl">Habilitar factura como título valor</span>
          </div>
          <div class="obw-item" id="ob-2" onclick="showPage('cesion')">
            <div class="obw-cb"><svg class="obw-cb-check" viewBox="0 0 12 12" fill="none" stroke="white" stroke-width="2.5"><polyline points="2,6 5,9 10,3"/></svg></div>
            <span class="obw-lbl">Crear primera cesión RADIAN</span>
          </div>
          <div class="obw-item" id="ob-3" onclick="showPage('reportes')">
            <div class="obw-cb"><svg class="obw-cb-check" viewBox="0 0 12 12" fill="none" stroke="white" stroke-width="2.5"><polyline points="2,6 5,9 10,3"/></svg></div>
            <span class="obw-lbl">Descargar primer reporte Excel</span>
          </div>
        </div>
        <div class="obw-dismiss"><a onclick="dismissChecklist()">Ocultar lista de inicio</a></div>
      </div>

      <div class="grid-2 mb-20">
        <div class="card">
          <div class="card-head">
            <div>
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                Últimas Facturas
              </div>
            </div>
            <a class="card-link" onclick="showPage('facturas')">
              Ver todas
              <svg viewBox="0 0 20 20" fill="currentColor" style="width:12px"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/></svg>
            </a>
          </div>
          <table class="tbl">
            <thead><tr><th>Factura</th><th>Adquiriente</th><th>Valor</th><th>Estado</th></tr></thead>
            <tbody id="dash-facturas"><tr><td colspan="4"><div class="empty-state" style="padding:24px"><div class="empty-text">Cargando datos...</div></div></td></tr></tbody>
          </table>
        </div>
        <div class="grid-col">
          <div class="card">
            <div class="card-head">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                Proceso de Cesión
              </div>
            </div>
            <div class="card-body">
              <div class="steps">
                <div class="step"><div class="step-circle sc-done">✓</div><div><div class="step-title">Factura validada DIAN</div><div class="step-desc">CUFE emitido y activo en la plataforma</div></div></div>
                <div class="step"><div class="step-circle sc-done">✓</div><div><div class="step-title">Eventos 032 y 033</div><div class="step-desc">Recibo mercantil y aceptación del adquiriente</div></div></div>
                <div class="step"><div class="step-circle sc-active">3</div><div><div class="step-title">Habilitar título valor</div><div class="step-desc">Marcar la factura como endosable</div></div></div>
                <div class="step"><div class="step-circle sc-pending">4</div><div><div class="step-title">Ceder en RADIAN</div><div class="step-desc">Evento 037 enviado a DIAN (≈1 seg)</div></div></div>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-head">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                Estado del sistema
              </div>
            </div>
            <div class="card-body">
              <div class="status-row"><span class="status-label">API RADIAN</span><span class="badge b-green" id="status-api">Verificando</span></div>
              <div class="status-row"><span class="status-label">DIAN Habilitación</span><span class="badge b-gold" id="status-dian">Sin certificado</span></div>
              <div class="status-row"><span class="status-label">Base de datos</span><span class="badge b-green" id="status-db">Conectada</span></div>
              <div class="status-row"><span class="status-label">Ambiente</span><span class="badge b-blue">Habilitación</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ FACTURAS ══ -->
    <div id="page-facturas" class="tab-content">
      <div class="filter-bar">
        <button class="filter-btn active" onclick="filterFacturas(this,'')">Todas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'EMITIDA')">Emitidas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'VALIDADA_DIAN')">Validadas DIAN</button>
        <button class="filter-btn" onclick="filterFacturas(this,'CEDIDA')">Cedidas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'EN_CESION')">En Cesión</button>
        <button class="filter-btn" onclick="filterFacturas(this,'PAGADA')">Pagadas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'RECHAZADA')">Rechazadas</button>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              Facturas electrónicas <span id="fact-count" style="font-size:12px;color:var(--text-muted);font-weight:500"></span>
            </div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="showPage('registrar')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px"><path d="M12 4v16m8-8H4"/></svg>
            Registrar nueva
          </button>
        </div>
        <div class="tbl-scroll">
        <table class="tbl tbl-mobile">
          <thead><tr><th>Número / CUFE</th><th>Adquiriente</th><th>Valor Total</th><th>Vencimiento</th><th>Estado</th><th style="text-align:center">Acciones</th></tr></thead>
          <tbody id="facturas-body"><tr><td colspan="6"><div class="empty-state" style="padding:32px"><div class="empty-text">Cargando facturas...</div></div></td></tr></tbody>
        </table>
        </div>
      </div>
    </div>

    <!-- ══ REGISTRAR FACTURA ══ -->
    <div id="page-registrar" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-head">
            <div>
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4v16m8-8H4"/></svg>
                Registrar factura electrónica
              </div>
              <div class="card-subtitle">Ingresa los datos de la factura emitida por la DIAN</div>
            </div>
          </div>
          <div class="card-body">
            <div class="section-label">Identificación</div>
            <div class="fg"><label>CUFE <span style="color:var(--red)">*</span><span class="tip"><button class="tip-btn" tabindex="-1">?</button><span class="tip-box">El CUFE es el código único de 96 caracteres hexadecimales que identifica tu factura electrónica. Lo encuentras en el PDF de tu factura o en el portal de tu proveedor de facturación electrónica (campo &lt;cbc:UUID&gt; en el XML).</span></span></label><textarea id="reg-cufe" class="cufe-ta" placeholder="Pega aquí el CUFE de 96 caracteres hexadecimales" rows="2"></textarea></div>
            <div class="form-row">
              <div class="fg"><label>Número de factura <span style="color:var(--red)">*</span></label><input id="reg-numero" placeholder="00001"/></div>
              <div class="fg"><label>Prefijo</label><input id="reg-prefijo" placeholder="FV" value="FV"/></div>
            </div>
            <div class="divider"></div>
            <div class="section-label">Emisor</div>
            <div class="form-row">
              <div class="fg"><label>NIT Emisor <span style="color:var(--red)">*</span></label><input id="reg-emisor-nit" placeholder="900.123.456-1"/></div>
              <div class="fg"><label>Nombre Emisor <span style="color:var(--red)">*</span></label><input id="reg-emisor-nombre" placeholder="MI EMPRESA SAS"/></div>
            </div>
            <div class="divider"></div>
            <div class="section-label">Adquiriente</div>
            <div class="form-row">
              <div class="fg"><label>NIT Adquiriente <span style="color:var(--red)">*</span></label><input id="reg-adq-nit" placeholder="800.000.000-1"/></div>
              <div class="fg"><label>Nombre Adquiriente <span style="color:var(--red)">*</span></label><input id="reg-adq-nombre" placeholder="CLIENTE SAS"/></div>
            </div>
            <div class="divider"></div>
            <div class="section-label">Valores (COP)</div>
            <div class="form-row-3">
              <div class="fg"><label>Base gravable <span style="color:var(--red)">*</span></label><input id="reg-base" type="number" placeholder="100000000"/></div>
              <div class="fg"><label>IVA</label><input id="reg-iva" type="number" placeholder="19000000"/></div>
              <div class="fg"><label>Total <span style="color:var(--red)">*</span></label><input id="reg-total" type="number" placeholder="119000000"/></div>
            </div>
            <div class="divider"></div>
            <div class="section-label">Fechas</div>
            <div class="form-row">
              <div class="fg"><label>Fecha de emisión <span style="color:var(--red)">*</span></label><input id="reg-fecha-em" type="datetime-local"/></div>
              <div class="fg"><label>Fecha de vencimiento <span style="color:var(--red)">*</span></label><input id="reg-fecha-venc" type="datetime-local"/></div>
            </div>
            <button class="btn btn-primary btn-lg btn-block" onclick="registrarFactura()" id="btn-reg-fact" style="margin-top:8px">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px"><path d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/></svg>
              <span id="btn-reg-fact-text">Registrar factura</span>
            </button>
            <div class="resp-box" id="resp-reg-fact"></div>
          </div>
        </div>
        <div class="grid-col">
          <div class="card">
            <div class="card-head">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
                ¿Qué es el CUFE?
              </div>
            </div>
            <div class="card-body">
              <p style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:12px">El <strong>CUFE</strong> (Código Único de Factura Electrónica) es el identificador único de 96 caracteres hexadecimales que la DIAN asigna a cada factura electrónica válida.</p>
              <p style="font-size:13px;color:var(--text-secondary);line-height:1.6">Lo encuentras en el XML de la factura electrónica o en el PDF que entregó el proveedor de software.</p>
            </div>
          </div>
          <div class="card">
            <div class="card-head">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                Habilitar título valor
                <span class="tip"><button class="tip-btn" tabindex="-1">?</button><span class="tip-box">Habilitar como título valor inscribe la factura en RADIAN, convirtiéndola en un instrumento negociable. Este paso es obligatorio antes de ceder. Solo se puede hacer una vez por factura.</span></span>
              </div>
              <div class="card-subtitle">Habilita una factura ya registrada</div>
            </div>
            <div class="card-body">
              <div class="fg"><label>CUFE de la factura</label><input id="f-cufe-hab" placeholder="Pega aquí el CUFE a habilitar"/></div>
              <button class="btn btn-success btn-block" onclick="habilitarTitulo()" style="margin-bottom:0">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                Habilitar como título valor
              </button>
              <div class="resp-box" id="resp-habilitar"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ NUEVA CESIÓN ══ -->
    <div id="page-cesion" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-head">
            <div>
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                Nueva Cesión — Evento 037 RADIAN
              </div>
              <div class="card-subtitle">Transfiere el derecho de cobro de una factura electrónica</div>
            </div>
          </div>
          <div class="card-body">
            <div class="section-label">Factura a ceder</div>
            <div class="fg"><label>CUFE de la factura <span style="color:var(--red)">*</span><span class="tip"><button class="tip-btn" tabindex="-1">?</button><span class="tip-box">Ingresa el CUFE de la factura que deseas ceder. Debe estar previamente habilitada como título valor desde la sección "Registrar Factura".</span></span></label><input id="f-cufe" placeholder="Código único de la factura electrónica" style="font-family:monospace;font-size:12px"/><div class="hint">La factura debe estar habilitada como título valor</div></div>
            <div class="divider"></div>
            <div class="section-label">Cesionario (quien recibe)</div>
            <div class="form-row">
              <div class="fg"><label>NIT Cesionario <span style="color:var(--red)">*</span><span class="tip"><button class="tip-btn" tabindex="-1">?</button><span class="tip-box">El cesionario es quien recibirá el derecho de cobro de la factura (ej: un banco o fondo de inversión). El NIT debe estar registrado ante la DIAN.</span></span></label><input id="f-nit-ces" placeholder="900.123.456-1"/></div>
              <div class="fg"><label>Nombre Cesionario <span style="color:var(--red)">*</span></label><input id="f-nombre-ces" placeholder="BANCO EJEMPLO SAS"/></div>
            </div>
            <div class="divider"></div>
            <div class="section-label">Valor</div>
            <div class="fg"><label>Valor a ceder (COP) <span style="color:var(--red)">*</span></label><input id="f-valor" type="number" placeholder="120000000"/><div class="hint">Puede ser igual o menor al valor total de la factura</div></div>
            <button class="btn btn-primary btn-lg btn-block" onclick="ceder()" id="btn-ceder" style="margin-top:8px">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              <span id="btn-ceder-text">Enviar a DIAN RADIAN</span>
            </button>
            <div class="resp-box" id="resp-cesion"></div>
          </div>
        </div>
        <div class="grid-col">
          <div class="card">
            <div class="card-head">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                Requisitos previos
              </div>
            </div>
            <div class="card-body">
              <div class="steps">
                <div class="step"><div class="step-circle sc-done">✓</div><div><div class="step-title">Factura habilitada como título valor</div><div class="step-desc">Estado VALIDADA_DIAN con es_titulo_valor = true</div></div></div>
                <div class="step"><div class="step-circle sc-done">✓</div><div><div class="step-title">XML UBL 2.1 construido</div><div class="step-desc">Evento 037 con hash SHA-384 (CUDE)</div></div></div>
                <div class="step"><div class="step-circle sc-done">✓</div><div><div class="step-title">Firma digital aplicada</div><div class="step-desc">Certificado Certicámara o Andes SCD</div></div></div>
                <div class="step"><div class="step-circle sc-active">4</div><div><div class="step-title">Respuesta DIAN en tiempo real</div><div class="step-desc">Procesado en el ambiente de habilitación</div></div></div>
              </div>
            </div>
          </div>
          <div class="card" style="background:linear-gradient(135deg,#EEF3FF,#F0FDFF);border-color:#BFDBFE">
            <div class="card-body" style="padding:18px">
              <div style="font-size:13px;font-weight:700;color:var(--brand);margin-bottom:6px">¿No tienes el CUFE a la mano?</div>
              <div style="font-size:12px;color:var(--text-secondary);line-height:1.6;margin-bottom:14px">Ve a la sección de Facturas, busca la que quieres ceder y haz clic en "Ceder" — el CUFE se completará automáticamente.</div>
              <button class="btn btn-ghost btn-sm btn-block" onclick="showPage('facturas')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                Ver facturas disponibles
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ REPORTES EXCEL ══ -->
    <div id="page-reportes" class="tab-content">
      <div style="background:linear-gradient(135deg,#0F2554,#059669);border-radius:var(--radius-lg);padding:20px 28px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div>
          <div style="font-size:17px;font-weight:800;color:#fff;letter-spacing:-0.3px">Reportes Contables Excel</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.6);margin-top:4px">Descarga reportes profesionales con formato contable, gráficas y PUC colombiano</div>
        </div>
        <button class="btn btn-lg" style="background:rgba(255,255,255,0.15);color:#fff;border:1.5px solid rgba(255,255,255,0.3)" onclick="descargarReporte('consolidado')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
          Descargar Reporte Consolidado
        </button>
      </div>
      <div class="stats-grid">
        <div class="stat-card c1" style="cursor:pointer" onclick="descargarReporte('libro-diario')">
          <div class="stat-icon si-blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
          </div>
          <div class="stat-value" style="font-size:20px">Libro Diario</div>
          <div class="stat-label">Asientos PUC automáticos</div>
          <div class="stat-trend" style="margin-top:10px">
            <span class="badge b-blue">Débitos · Créditos · Balance</span>
          </div>
          <div style="margin-top:14px">
            <button class="btn btn-primary btn-sm btn-block" onclick="event.stopPropagation();descargarReporte('libro-diario')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
              Descargar .xlsx
            </button>
          </div>
        </div>
        <div class="stat-card c2" style="cursor:pointer" onclick="descargarReporte('cartera')">
          <div class="stat-icon si-green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10h18M3 14h18M10 18H3M10 6H3m7 0h11M17 18h4"/></svg>
          </div>
          <div class="stat-value" style="font-size:20px">Cartera</div>
          <div class="stat-label">Análisis de antigüedad</div>
          <div class="stat-trend" style="margin-top:10px">
            <span class="badge b-green">Aging · Semáforos · Gráfica</span>
          </div>
          <div style="margin-top:14px">
            <button class="btn btn-success btn-sm btn-block" onclick="event.stopPropagation();descargarReporte('cartera')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
              Descargar .xlsx
            </button>
          </div>
        </div>
        <div class="stat-card c3" style="cursor:pointer" onclick="descargarReporte('estado-resultados')">
          <div class="stat-icon si-gold">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          </div>
          <div class="stat-value" style="font-size:20px">P&amp;L</div>
          <div class="stat-label">Estado de Resultados</div>
          <div class="stat-trend" style="margin-top:10px">
            <span class="badge b-gold">Ingresos · Gastos · Utilidad</span>
          </div>
          <div style="margin-top:14px">
            <button class="btn btn-sm btn-block" style="background:var(--gold);color:#fff" onclick="event.stopPropagation();descargarReporte('estado-resultados')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
              Descargar .xlsx
            </button>
          </div>
        </div>
        <div class="stat-card c4" style="cursor:pointer" onclick="descargarReporte('flujo-caja')">
          <div class="stat-icon si-purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <div class="stat-value" style="font-size:20px">Flujo de Caja</div>
          <div class="stat-label">Proyección de cobros</div>
          <div class="stat-trend" style="margin-top:10px">
            <span class="badge b-purple">6 meses · Calendario</span>
          </div>
          <div style="margin-top:14px">
            <button class="btn btn-sm btn-block" style="background:var(--purple);color:#fff" onclick="event.stopPropagation();descargarReporte('flujo-caja')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
              Descargar .xlsx
            </button>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-head">
          <div class="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            Contenido de cada reporte
          </div>
        </div>
        <div class="card-body" style="padding:0 20px">
          <div class="ep-list">
            <div class="ep-item"><span class="method m-get">XLSX</span><div class="ep-info"><div class="ep-path">Libro Diario</div><div class="ep-desc">2 hojas: asientos diarios PUC 1305/4135 + resumen saldos por cuenta. Balance automático Debe=Haber.</div></div></div>
            <div class="ep-item"><span class="method m-get">XLSX</span><div class="ep-info"><div class="ep-path">Cartera</div><div class="ep-desc">2 hojas: resumen aging con gráfica de barras + detalle por factura con semáforo de mora y colores condicionales.</div></div></div>
            <div class="ep-item"><span class="method m-get">XLSX</span><div class="ep-info"><div class="ep-path">Estado de Resultados</div><div class="ep-desc">3 hojas: P&L completo (ingresos/gastos/utilidad) + detalle mensual + detalle de cesiones aceptadas.</div></div></div>
            <div class="ep-item"><span class="method m-get">XLSX</span><div class="ep-info"><div class="ep-path">Flujo de Caja</div><div class="ep-desc">2 hojas: proyección 6 meses por fecha de vencimiento + calendario completo con estado (vencido/este mes/proyectado).</div></div></div>
            <div class="ep-item"><span class="method m-post">XLSX</span><div class="ep-info"><div class="ep-path">Consolidado ⭐</div><div class="ep-desc">6 hojas en un solo archivo: Dashboard KPIs + Libro Diario + Cartera + Flujo + Estado de Resultados. Listo para auditoría.</div></div></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ CONSULTAR DIAN ══ -->
    <div id="page-consultar" class="tab-content">
      <div class="grid-2-eq">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
              Consultar cesión por CUDE
            </div>
          </div>
          <div class="card-body">
            <div class="fg"><label>CUDE del evento</label><input id="f-cude" placeholder="d8f3a1b2c3...sha384"/><div class="hint">El CUDE es el identificador del evento de cesión, devuelto por RADIAN al momento de ceder</div></div>
            <button class="btn btn-primary btn-block" onclick="consultarDian()">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
              Consultar estado en DIAN
            </button>
            <div class="resp-box" id="resp-dian"></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
              Verificar conexión DIAN
            </div>
          </div>
          <div class="card-body">
            <p style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:16px">Verifica la conectividad con el webservice SOAP de la DIAN en el ambiente de <strong>habilitación</strong>. Útil para diagnosticar problemas de integración.</p>
            <div style="background:var(--border-soft);border-radius:var(--radius-sm);padding:12px 14px;font-size:12px;font-family:monospace;color:var(--text-secondary);margin-bottom:16px;word-break:break-all">GET /api/v1/consultas/ping-dian</div>
            <button class="btn btn-block" style="background:linear-gradient(135deg,var(--purple),var(--brand));color:#fff" onclick="pingDian()">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
              Verificar conexión DIAN
            </button>
            <div class="resp-box" id="resp-ping"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ API EXPLORER ══ -->
    <div id="page-api" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              Endpoints de la API
            </div>
          </div>
          <div class="card-body" style="padding:0 20px">
            <div class="ep-list">
              <div class="ep-item"><span class="method m-post">POST</span><div class="ep-info"><div class="ep-path">/api/v1/auth/registro</div><div class="ep-desc">Registrar nueva empresa</div></div></div>
              <div class="ep-item"><span class="method m-post">POST</span><div class="ep-info"><div class="ep-path">/api/v1/auth/token</div><div class="ep-desc">Obtener token JWT</div></div></div>
              <div class="ep-item"><span class="method m-get">GET</span><div class="ep-info"><div class="ep-path">/api/v1/auth/me</div><div class="ep-desc">Datos del usuario actual</div></div></div>
              <div class="ep-item"><span class="method m-post">POST</span><div class="ep-info"><div class="ep-path">/api/v1/facturas/registrar</div><div class="ep-desc">Registrar factura electrónica</div></div></div>
              <div class="ep-item"><span class="method m-get">GET</span><div class="ep-info"><div class="ep-path">/api/v1/facturas/</div><div class="ep-desc">Listar facturas del usuario</div></div></div>
              <div class="ep-item"><span class="method m-get">GET</span><div class="ep-info"><div class="ep-path">/api/v1/facturas/{cufe}</div><div class="ep-desc">Consultar factura por CUFE</div></div></div>
              <div class="ep-item"><span class="method m-put">PUT</span><div class="ep-info"><div class="ep-path">/api/v1/facturas/{cufe}/habilitar-cesion</div><div class="ep-desc">Habilitar como título valor</div></div></div>
              <div class="ep-item"><span class="method m-post">POST</span><div class="ep-info"><div class="ep-path">/api/v1/cesion/crear</div><div class="ep-desc">⚡ Ceder factura en RADIAN (evento 037)</div></div></div>
              <div class="ep-item"><span class="method m-get">GET</span><div class="ep-info"><div class="ep-path">/api/v1/cesion/{cude}/estado</div><div class="ep-desc">Estado de cesión en DIAN</div></div></div>
              <div class="ep-item"><span class="method m-get">GET</span><div class="ep-info"><div class="ep-path">/api/v1/cesion/factura/{cufe}</div><div class="ep-desc">Cesiones de una factura</div></div></div>
              <div class="ep-item"><span class="method m-get">GET</span><div class="ep-info"><div class="ep-path">/api/v1/consultas/ping-dian</div><div class="ep-desc">Verificar conexión DIAN</div></div></div>
              <div class="ep-item"><span class="method m-get">GET</span><div class="ep-info"><div class="ep-path">/health</div><div class="ep-desc">Estado de la API</div></div></div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3l14 9-14 9V3z"/></svg>
              Probar endpoint
            </div>
          </div>
          <div class="card-body">
            <div class="fg"><label>Selecciona un endpoint</label>
              <select id="ep-sel">
                <option value="/health">GET /health</option>
                <option value="/api/v1/auth/me">GET /auth/me (requiere auth)</option>
                <option value="/api/v1/facturas/">GET /facturas (requiere auth)</option>
                <option value="/api/v1/consultas/ping-dian">GET /ping-dian (requiere auth)</option>
              </select>
            </div>
            <button class="btn btn-primary btn-block" onclick="probarEndpoint()" style="margin-bottom:14px">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M5 3l14 9-14 9V3z"/></svg>
              Ejecutar
            </button>
            <div class="resp-box show" id="resp-api" style="min-height:120px">
              <span style="color:#4B5563;font-size:12px">// Selecciona un endpoint y haz clic en Ejecutar</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ MIS CESIONES ══ -->
    <div id="page-cesiones" class="tab-content">
      <div class="filter-bar">
        <button class="filter-btn active" onclick="filterCesiones(this,'')">Todas</button>
        <button class="filter-btn" onclick="filterCesiones(this,'ACEPTADA')">Aceptadas</button>
        <button class="filter-btn" onclick="filterCesiones(this,'RECHAZADA')">Rechazadas</button>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
              Historial de Cesiones <span id="ces-count" style="font-size:12px;color:var(--text-muted);font-weight:400"></span>
            </div>
            <div class="card-subtitle">Todos los eventos 037 registrados en RADIAN</div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="showPage('cesion')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:13px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            Nueva cesión
          </button>
        </div>
        <div class="tbl-scroll">
        <table class="tbl tbl-mobile">
          <thead>
            <tr>
              <th>Número / CUDE</th>
              <th>Factura (CUFE)</th>
              <th>Cedente</th>
              <th>Cesionario</th>
              <th>Valor</th>
              <th>Fecha</th>
              <th>Estado</th>
              <th style="text-align:center">XML</th>
            </tr>
          </thead>
          <tbody id="cesiones-body">
            <tr><td colspan="8"><div class="empty-state" style="padding:32px"><div class="empty-text">Cargando cesiones...</div></div></td></tr>
          </tbody>
        </table>
        </div>
      </div>
    </div>

    <!-- ══ CARTERA ══ -->
    <div id="page-cartera" class="tab-content">
      <div class="aging-grid" id="aging-cards">
        <div class="aging-card aging-0"><div class="aging-label">Al día</div><div class="aging-amount" id="ag-0">—</div><div class="aging-count" id="ag-0-n">0 facturas</div></div>
        <div class="aging-card aging-30"><div class="aging-label">1 – 30 días</div><div class="aging-amount" id="ag-30">—</div><div class="aging-count" id="ag-30-n">0 facturas</div></div>
        <div class="aging-card aging-60"><div class="aging-label">31 – 60 días</div><div class="aging-amount" id="ag-60">—</div><div class="aging-count" id="ag-60-n">0 facturas</div></div>
        <div class="aging-card aging-90"><div class="aging-label">61 – 90 días</div><div class="aging-amount" id="ag-90">—</div><div class="aging-count" id="ag-90-n">0 facturas</div></div>
        <div class="aging-card aging-over"><div class="aging-label">+90 días</div><div class="aging-amount" id="ag-over">—</div><div class="aging-count" id="ag-over-n">0 facturas</div></div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
              Distribución de Cartera
            </div>
          </div>
          <div class="card-body" id="aging-bars">
            <div class="empty-state"><div class="empty-text">Cargando...</div></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              Alertas de Vencimiento
            </div>
          </div>
          <div class="card-body" style="padding:0">
            <table class="tbl">
              <thead><tr><th>Factura</th><th>Cliente</th><th>Valor</th><th>Vencimiento</th><th>Días</th></tr></thead>
              <tbody id="vencidas-body"><tr><td colspan="5"><div class="empty-state" style="padding:24px"><div class="empty-text">Cargando...</div></div></td></tr></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ FLUJO DE CAJA ══ -->
    <div id="page-flujo" class="tab-content">
      <div class="stats-grid" style="grid-template-columns:repeat(3,1fr)">
        <div class="stat-card c1">
          <div class="stat-icon si-blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg></div>
          <div class="stat-value" id="flujo-total">—</div>
          <div class="stat-label">Flujo Proyectado Total</div>
          <div class="stat-trend">Suma de facturas vigentes</div>
        </div>
        <div class="stat-card c3">
          <div class="stat-icon si-gold"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
          <div class="stat-value" id="flujo-mes">—</div>
          <div class="stat-label">Este mes</div>
          <div class="stat-trend">Vencimientos mes actual</div>
        </div>
        <div class="stat-card c4">
          <div class="stat-icon si-purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
          <div class="stat-value" id="flujo-prox">—</div>
          <div class="stat-label">Próximos 30 días</div>
          <div class="stat-trend">Cobros esperados</div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              Proyección por Mes
            </div>
            <span class="badge b-blue">Próximos 6 meses</span>
          </div>
          <div class="card-body" id="flujo-chart-wrap">
            <div class="empty-state"><div class="empty-text">Cargando proyección...</div></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              Calendario de Vencimientos
            </div>
          </div>
          <div class="card-body" style="padding:0">
            <table class="tbl">
              <thead><tr><th>Factura</th><th>Cliente</th><th>Valor</th><th>Vence</th></tr></thead>
              <tbody id="flujo-tabla"><tr><td colspan="4"><div class="empty-state" style="padding:24px"><div class="empty-text">Cargando...</div></div></td></tr></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ══ LIBRO DIARIO ══ -->
    <div id="page-contabilidad" class="tab-content">
      <div class="stats-grid" style="grid-template-columns:repeat(4,1fr)">
        <div class="stat-card c1">
          <div class="stat-icon si-blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg></div>
          <div class="stat-value" id="cont-asientos">—</div>
          <div class="stat-label">Total Asientos</div>
          <div class="stat-trend">Pares débito/crédito</div>
        </div>
        <div class="stat-card c2">
          <div class="stat-icon si-green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg></div>
          <div class="stat-value" id="cont-debito">—</div>
          <div class="stat-label">Total Débitos</div>
          <div class="stat-trend">COP acumulado</div>
        </div>
        <div class="stat-card c3">
          <div class="stat-icon si-gold"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg></div>
          <div class="stat-value" id="cont-credito">—</div>
          <div class="stat-label">Total Créditos</div>
          <div class="stat-trend">COP acumulado</div>
        </div>
        <div class="stat-card c4">
          <div class="stat-icon si-purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg></div>
          <div class="stat-value" id="cont-balance" class="balance-ok">—</div>
          <div class="stat-label">Balance</div>
          <div class="stat-trend">Debe = Haber</div>
        </div>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              Libro Diario — PUC Colombia
            </div>
            <div class="card-subtitle">Asientos contables generados automáticamente por cada cesión</div>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <select id="cont-periodo" onchange="loadContabilidad()" style="padding:7px 12px;border:1.5px solid var(--border);border-radius:var(--radius-sm);font-size:12px;font-family:var(--font);background:var(--surface);color:var(--text-primary)">
              <option value="">Todo el período</option>
              <option value="2025">2025</option>
              <option value="2026">2026</option>
            </select>
          </div>
        </div>
        <div style="overflow-x:auto">
          <table class="tbl">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Cód. PUC</th>
                <th>Cuenta Contable</th>
                <th>Referencia</th>
                <th style="text-align:right">Débito</th>
                <th style="text-align:right">Crédito</th>
              </tr>
            </thead>
            <tbody id="cont-tbody">
              <tr><td colspan="6"><div class="empty-state" style="padding:32px"><div class="empty-text">Cargando libro diario...</div></div></td></tr>
            </tbody>
            <tfoot id="cont-tfoot"></tfoot>
          </table>
        </div>
      </div>
    </div>

    <!-- ══ ESTADO DE RESULTADOS ══ -->
    <div id="page-resultados" class="tab-content">
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-val pnl-positive" id="pnl-ingresos">—</div>
          <div class="kpi-label">Ingresos Totales</div>
          <div class="kpi-sub">Por cesiones de cartera</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val pnl-neutral" id="pnl-cesiones-n">—</div>
          <div class="kpi-label">Cesiones Aceptadas</div>
          <div class="kpi-sub">Eventos RADIAN aprobados</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-val pnl-positive" id="pnl-promedio">—</div>
          <div class="kpi-label">Valor Promedio / Cesión</div>
          <div class="kpi-sub">COP por operación</div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              Volumen por Mes
            </div>
          </div>
          <div class="card-body" id="resultados-chart">
            <div class="empty-state"><div class="empty-text">Cargando gráfica...</div></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
              Estado de Resultados
            </div>
            <span class="badge b-green">Acumulado</span>
          </div>
          <div class="card-body" id="pnl-body">
            <div class="empty-state"><div class="empty-text">Cargando P&amp;L...</div></div>
          </div>
        </div>
      </div>
    </div>

  </div><!-- end content -->
</div><!-- end main -->
</div><!-- end layout -->
</div><!-- end app-screen -->

<!-- ══ BOTTOM NAV (mobile) ══ -->
<nav class="bottom-nav" id="bottom-nav">
  <a class="bn-item active" id="bn-dashboard" onclick="showPage('dashboard')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
    Dashboard
  </a>
  <a class="bn-item" id="bn-facturas" onclick="showPage('facturas')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
    Facturas
  </a>
  <a class="bn-item" id="bn-cesion" onclick="showPage('cesion')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
    Ceder
  </a>
  <a class="bn-item" id="bn-cartera" onclick="showPage('cartera')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10h18M3 14h18M10 18H3M10 6H3"/></svg>
    Cartera
  </a>
  <a class="bn-item" id="bn-reportes" onclick="showPage('reportes')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
    Reportes
  </a>
</nav>

<!-- ══ WIZARD ONBOARDING ══ -->
<div class="wiz-overlay" id="wiz-overlay">
  <div class="wiz-box" id="wiz-box">
    <div class="wiz-prog-bar"><div class="wiz-prog-fill" id="wiz-fill" style="width:25%"></div></div>
    <div class="wiz-body" id="wiz-body">

      <!-- PASO 1 -->
      <div id="wiz-1">
        <div class="wiz-step-tag">Paso 1 de 4</div>
        <div class="wiz-title">Bienvenido a FinPro Capital 👋</div>
        <div class="wiz-sub">FinPro Capital te permite <strong>ceder facturas electrónicas ante la DIAN</strong> a través del sistema RADIAN, convirtiendo tus cuentas por cobrar en liquidez inmediata.<br><br>La plataforma automatiza todo el proceso: desde el registro del CUFE hasta la contabilidad automática en el PUC colombiano.</div>
        <div class="wiz-visual" style="flex-direction:row;gap:20px;flex-wrap:wrap">
          <div style="flex:1;min-width:120px;text-align:center;padding:10px">
            <div style="font-size:28px;margin-bottom:6px">📄</div>
            <div style="font-size:12px;font-weight:700;color:var(--text-primary)">Registra</div>
            <div style="font-size:11px;color:var(--text-secondary)">Tus facturas con CUFE</div>
          </div>
          <div style="flex:0;display:flex;align-items:center;color:var(--brand);font-size:20px">→</div>
          <div style="flex:1;min-width:120px;text-align:center;padding:10px">
            <div style="font-size:28px;margin-bottom:6px">🏦</div>
            <div style="font-size:12px;font-weight:700;color:var(--text-primary)">Cede</div>
            <div style="font-size:11px;color:var(--text-secondary)">Via RADIAN Evento 037</div>
          </div>
          <div style="flex:0;display:flex;align-items:center;color:var(--brand);font-size:20px">→</div>
          <div style="flex:1;min-width:120px;text-align:center;padding:10px">
            <div style="font-size:28px;margin-bottom:6px">📊</div>
            <div style="font-size:12px;font-weight:700;color:var(--text-primary)">Contabiliza</div>
            <div style="font-size:11px;color:var(--text-secondary)">Automático con PUC</div>
          </div>
        </div>
      </div>

      <!-- PASO 2 -->
      <div id="wiz-2" style="display:none">
        <div class="wiz-step-tag">Paso 2 de 4</div>
        <div class="wiz-title">¿Qué es una cesión RADIAN?</div>
        <div class="wiz-sub">RADIAN es el sistema de la DIAN que permite convertir facturas electrónicas en <strong>títulos valores negociables</strong> para cederlos a bancos o fondos de inversión.</div>
        <div class="wiz-visual">
          <div class="wiz-vstep">
            <div class="wiz-vstep-num">1</div>
            <div>
              <div class="wiz-vstep-name">Registra la factura con su CUFE</div>
              <div class="wiz-vstep-desc">El CUFE es el código único de 96 caracteres que la DIAN asigna a cada factura electrónica válida. Lo encuentras en el PDF o XML de tu factura.</div>
            </div>
          </div>
          <div class="wiz-vstep">
            <div class="wiz-vstep-num">2</div>
            <div>
              <div class="wiz-vstep-name">Habilítala como título valor</div>
              <div class="wiz-vstep-desc">Este paso inscribe la factura en RADIAN como un instrumento negociable. Solo puede hacerse una vez por factura y requiere que esté validada por la DIAN.</div>
            </div>
          </div>
          <div class="wiz-vstep">
            <div class="wiz-vstep-num" style="background:#059669">3</div>
            <div>
              <div class="wiz-vstep-name">Cede el crédito — Evento 037</div>
              <div class="wiz-vstep-desc">La plataforma genera el XML UBL 2.1, lo firma con SHA-384 y lo envía a RADIAN. La DIAN responde en menos de 2 segundos y la contabilidad se genera automáticamente.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- PASO 3 -->
      <div id="wiz-3" style="display:none">
        <div class="wiz-step-tag">Paso 3 de 4</div>
        <div class="wiz-title">Registra tu primera factura</div>
        <div class="wiz-sub">Crea una factura de ejemplo para explorar la plataforma. Puedes usar datos ficticios — no se envía nada a la DIAN en este momento.</div>
        <div class="wiz-form">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="wfg">
              <label>CUFE
                <span class="tip"><button class="tip-btn" tabindex="-1">?</button><span class="tip-box">Código Único de Factura Electrónica: 96 caracteres hexadecimales que la DIAN asigna a cada factura. En demo puedes poner cualquier texto de 96 caracteres.</span></span>
              </label>
              <input id="wiz-cufe" placeholder="ej: a1b2c3…(96 chars)" style="font-family:monospace;font-size:11px"/>
              <div class="whint">En producción lo encuentras en el XML o PDF de tu factura</div>
            </div>
            <div class="wfg">
              <label>Número de factura</label>
              <input id="wiz-numero" placeholder="ej: 00001" value="00001"/>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="wfg">
              <label>NIT Emisor
                <span class="tip"><button class="tip-btn" tabindex="-1">?</button><span class="tip-box">NIT de tu empresa (quien emite la factura). Formato: 900.123.456-1</span></span>
              </label>
              <input id="wiz-emisor-nit" placeholder="900.123.456-1"/>
            </div>
            <div class="wfg">
              <label>Nombre Emisor</label>
              <input id="wiz-emisor-nombre" placeholder="MI EMPRESA SAS"/>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="wfg">
              <label>NIT Adquiriente
                <span class="tip"><button class="tip-btn" tabindex="-1">?</button><span class="tip-box">NIT de quien compró el bien o servicio (tu cliente). Es quien debe pagar la factura.</span></span>
              </label>
              <input id="wiz-adq-nit" placeholder="800.000.000-1"/>
            </div>
            <div class="wfg">
              <label>Valor total (COP)</label>
              <input id="wiz-valor" type="number" placeholder="120000000" value="120000000"/>
            </div>
          </div>
          <div class="resp-box" id="wiz-resp" style="margin-top:4px"></div>
        </div>
      </div>

      <!-- PASO 4 -->
      <div id="wiz-4" style="display:none">
        <div class="wiz-step-tag">Paso 4 de 4</div>
        <div class="wiz-title">¡Tu cuenta está lista! 🎉</div>
        <div class="wiz-sub">Ya tienes todo configurado. Estos son tus próximos pasos para completar tu primera cesión real:</div>
        <div class="wiz-checklist">
          <div class="wiz-ci">
            <div class="wiz-ci-icon">📄</div>
            <div>
              <div class="wiz-ci-label">Registrar una factura real con su CUFE</div>
              <div class="wiz-ci-sub">Ve a Registrar Factura en el menú lateral</div>
            </div>
          </div>
          <div class="wiz-ci">
            <div class="wiz-ci-icon">🏅</div>
            <div>
              <div class="wiz-ci-label">Habilitarla como título valor</div>
              <div class="wiz-ci-sub">Un clic desde la tabla de facturas</div>
            </div>
          </div>
          <div class="wiz-ci">
            <div class="wiz-ci-icon">⚡</div>
            <div>
              <div class="wiz-ci-label">Crear tu primera cesión RADIAN</div>
              <div class="wiz-ci-sub">Ve a Nueva Cesión e ingresa el NIT del cesionario</div>
            </div>
          </div>
          <div class="wiz-ci">
            <div class="wiz-ci-icon">📊</div>
            <div>
              <div class="wiz-ci-label">Descargar tu primer reporte Excel</div>
              <div class="wiz-ci-sub">Libro diario, cartera y estado de resultados</div>
            </div>
          </div>
        </div>
      </div>

    </div><!-- end wiz-body -->
    <div class="wiz-footer">
      <div class="wiz-dots">
        <div class="wiz-dot active" id="wd-0"></div>
        <div class="wiz-dot" id="wd-1"></div>
        <div class="wiz-dot" id="wd-2"></div>
        <div class="wiz-dot" id="wd-3"></div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <span class="wiz-skip" id="wiz-skip-btn" onclick="wizSkip()">Saltar tutorial</span>
        <button class="btn btn-ghost btn-sm" id="wiz-back-btn" onclick="wizBack()" style="display:none">← Atrás</button>
        <button class="btn btn-primary btn-sm" id="wiz-next-btn" onclick="wizNext()">Empezar →</button>
      </div>
    </div>
  </div>
</div>

<!-- ══ MODAL DETALLE FACTURA ══ -->
<div class="modal-overlay" id="modal-detalle">
  <div class="modal">
    <div class="modal-head">
      <div class="modal-title" id="modal-detalle-title">Detalle de factura</div>
      <button class="modal-close" onclick="closeModal('modal-detalle')">✕</button>
    </div>
    <div class="modal-body" id="modal-detalle-body"></div>
  </div>
</div>

<div id="toast"></div>

<script>
const API = '';
// ── TOKEN ya NO se guarda en sessionStorage (XSS-safe httpOnly cookie) ──
// El JWT vive en la cookie radian_session (httpOnly, no accesible por JS).
// Solo guardamos el CSRF token (leído de la cookie radian_csrf) y los datos
// de usuario (no sensibles) en memoria de sesión.
let USER_DATA = null;

// ═══════════════════════════════════════════════════════════
// ONBOARDING SYSTEM
// ═══════════════════════════════════════════════════════════
let OB_PROGRESS = { fact:false, titulo:false, cesion:false, reporte:false };
let WIZ_STEP = 1;
const WIZ_LABELS = ['Empezar →','Entendido, continuar →','Registrar factura demo','Ir al dashboard'];
const WIZ_PCT   = ['25%','50%','75%','100%'];

// ── WIZARD ──────────────────────────────────────────────────
function wizShow() {
  document.getElementById('wiz-overlay').classList.add('show');
  wizGoto(1);
}
function wizHide() {
  document.getElementById('wiz-overlay').classList.remove('show');
}
function wizSkip() {
  wizHide();
  saveOnboarding({is_new_user: false});
}
function wizGoto(n) {
  WIZ_STEP = n;
  [1,2,3,4].forEach(i => {
    const el = document.getElementById('wiz-'+i);
    if(el) el.style.display = i===n ? '' : 'none';
  });
  [0,1,2,3].forEach(i => {
    const d = document.getElementById('wd-'+i);
    if(d) d.className = 'wiz-dot'+(i===n-1?' active':'');
  });
  document.getElementById('wiz-fill').style.width = WIZ_PCT[n-1];
  document.getElementById('wiz-next-btn').textContent = WIZ_LABELS[n-1];
  const back = document.getElementById('wiz-back-btn');
  if(back) back.style.display = n>1 ? '' : 'none';
  const skip = document.getElementById('wiz-skip-btn');
  if(skip) skip.style.display = n===4 ? 'none' : '';
  saveOnboarding({onboarding_step: n});
}
function wizBack() { if(WIZ_STEP > 1) wizGoto(WIZ_STEP-1); }
async function wizNext() {
  if(WIZ_STEP === 3) {
    await wizRegisterDemo();
    return;
  }
  if(WIZ_STEP === 4) {
    wizHide();
    saveOnboarding({is_new_user: false, onboarding_step: 4});
    refreshChecklist();
    return;
  }
  wizGoto(WIZ_STEP+1);
}
async function wizRegisterDemo() {
  const cufe = document.getElementById('wiz-cufe').value.trim();
  const numero = document.getElementById('wiz-numero').value.trim()||'00001';
  const emisorNit = document.getElementById('wiz-emisor-nit').value.trim();
  const emisorNom = document.getElementById('wiz-emisor-nombre').value.trim();
  const adqNit = document.getElementById('wiz-adq-nit').value.trim();
  const valor = parseFloat(document.getElementById('wiz-valor').value)||120000000;
  const resp = document.getElementById('wiz-resp');

  // Generar CUFE demo si está vacío
  const cufeFinal = cufe || ('demo'+Array.from({length:90},()=>'0123456789abcdef'[Math.floor(Math.random()*16)]).join(''));

  const btn = document.getElementById('wiz-next-btn');
  btn.disabled = true; btn.textContent = 'Registrando...';
  resp.className = 'resp-box'; resp.innerHTML = '';

  const now = new Date(); const future = new Date(now.getTime()+30*24*3600000);
  const fmtDT = d => d.toISOString().slice(0,16);
  try {
    const body = {
      cufe: cufeFinal, numero, prefijo:'FV-DEMO',
      emisor_nit: emisorNit||'900.000.001-0', emisor_nombre: emisorNom||'MI EMPRESA DEMO SAS',
      adquiriente_nit: adqNit||'800.000.001-0', adquiriente_nombre: 'CLIENTE DEMO SAS',
      valor_base: Math.round(valor/1.19), valor_iva: valor - Math.round(valor/1.19), valor_total: valor,
      fecha_emision: fmtDT(now), fecha_vencimiento: fmtDT(future),
    };
    const r = await apiFetch('/api/v1/facturas/registrar', {method:'POST', body:JSON.stringify(body)});
    const d = await r.json();
    if(r.ok) {
      resp.className = 'resp-box show';
      resp.innerHTML = '<div class="resp-ok">✅ Factura demo creada correctamente</div>';
      OB_PROGRESS.fact = true;
      refreshChecklist();
      setTimeout(() => wizGoto(4), 1200);
    } else {
      resp.className = 'resp-box show';
      resp.innerHTML = '<div class="resp-err">⚠ '+(d.detail||'Error al registrar')+'</div>';
      btn.disabled=false; btn.textContent='Registrar factura demo';
    }
  } catch(e) {
    resp.className='resp-box show'; resp.innerHTML='<div class="resp-err">❌ Error de conexión</div>';
    btn.disabled=false; btn.textContent='Registrar factura demo';
  }
}

// ── CHECKLIST ───────────────────────────────────────────────
function refreshChecklist() {
  const keys = ['fact','titulo','cesion','reporte'];
  const done = keys.filter(k=>OB_PROGRESS[k]).length;
  const pct = Math.round(done/keys.length*100);
  document.getElementById('obw-pct').textContent = pct+'%';
  document.getElementById('obw-bar').style.width = pct+'%';
  keys.forEach((k,i) => {
    const el = document.getElementById('ob-'+i);
    if(el) el.classList.toggle('done', !!OB_PROGRESS[k]);
  });
  // Ocultar widget si 100%
  if(pct === 100) {
    setTimeout(()=>{ const w=document.getElementById('obw-widget'); if(w) w.style.display='none'; }, 1500);
  }
}
function dismissChecklist() {
  const w = document.getElementById('obw-widget');
  if(w) w.style.display = 'none';
  saveOnboarding({onboarding_progress: -1});
}
async function loadOnboardingProgress() {
  // Derive from existing API data
  try {
    const [rf, rc] = await Promise.all([
      apiFetch('/api/v1/facturas/?limit=5').then(r=>r.json()).catch(()=>({facturas:[]})),
      apiFetch('/api/v1/cesion/?limit=5').then(r=>r.json()).catch(()=>({cesiones:[]})),
    ]);
    const fs = rf.facturas||[];
    const cs = rc.cesiones||[];
    OB_PROGRESS.fact    = fs.length > 0;
    OB_PROGRESS.titulo  = fs.some(f=>f.es_titulo_valor);
    OB_PROGRESS.cesion  = cs.length > 0;
    // reporte: check from user data
    OB_PROGRESS.reporte = USER_DATA?.onboarding_progress >= 75 || false;
    refreshChecklist();
    // Show/hide widget based on user flag
    const isNew = USER_DATA?.is_new_user !== false;
    const prog  = USER_DATA?.onboarding_progress;
    const w = document.getElementById('obw-widget');
    if(w && (prog===-1)) w.style.display='none';
  } catch(e) {}
}

// ── SAVE ONBOARDING TO BACKEND ──────────────────────────────
async function saveOnboarding(data) {
  try {
    await apiFetch('/api/v1/auth/onboarding', {method:'PUT', body:JSON.stringify(data)});
  } catch(e) {}
}

// ── INIT ONBOARDING ─────────────────────────────────────────
async function initOnboarding() {
  await loadUserInfo();
  await loadOnboardingProgress();
  const isNew = USER_DATA?.is_new_user;
  // Show wizard if new user (is_new_user is true or undefined/null from old accounts)
  if(isNew === true || isNew === undefined || isNew === null) {
    const savedStep = USER_DATA?.onboarding_step;
    // Small delay so app loads first
    setTimeout(() => { wizShow(); if(savedStep>1) wizGoto(savedStep); }, 600);
  }
}

function getCsrfToken() {
  // Lee la cookie radian_csrf (no httpOnly, accesible por JS para double-submit)
  const match = document.cookie.match(/(?:^|;\s*)radian_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

function hasSesionActiva() {
  // No podemos leer radian_session (httpOnly), pero sí radian_csrf.
  // Si existe radian_csrf asumimos que hay sesión activa.
  return !!getCsrfToken();
}

// ── INIT ──
window.onload = () => {
  if(hasSesionActiva()) { showApp(); return; }
  const params = new URLSearchParams(window.location.search);
  if(params.get('register')==='1') showPanel('register');
};

function showPanel(p) {
  document.getElementById('login-panel').style.display = p==='login' ? '' : 'none';
  document.getElementById('register-panel').style.display = p==='register' ? '' : 'none';
  document.getElementById('login-err').classList.remove('show');
  document.getElementById('reg-err').classList.remove('show');
}

// ── AUTH ──
async function doLogin() {
  const email = document.getElementById('l-email').value.trim();
  const pass = document.getElementById('l-pass').value;
  const errEl = document.getElementById('login-err');
  const errTxt = document.getElementById('login-err-text');
  const btn = document.getElementById('login-btn');
  if(!email||!pass){ showErr(errEl, errTxt, 'Completa todos los campos'); return; }
  btn.innerHTML='<span class="spinner"></span> Ingresando...'; btn.disabled=true;
  try {
    const fd = new FormData();
    fd.append('username', email); fd.append('password', pass);
    // credentials:'include' → el navegador guarda las cookies httpOnly automáticamente
    const r = await fetch(API+'/api/v1/auth/token', {method:'POST', body:fd, credentials:'include'});
    const d = await r.json();
    if(!r.ok){
      const msg = r.status===429 ? (d.detail||'Demasiados intentos. Espera 1 minuto.')
                                 : (d.detail||'Credenciales incorrectas');
      showErr(errEl, errTxt, msg); return;
    }
    // Token NO se guarda en JS — vive en httpOnly cookie
    showApp();
  } catch(e){ showErr(errEl, errTxt, 'Error de conexión con el servidor'); }
  finally{ btn.textContent='Iniciar sesión'; btn.disabled=false; }
}

async function doRegister() {
  const nombre=document.getElementById('r-nombre').value.trim();
  const nit=document.getElementById('r-nit').value.trim();
  const email=document.getElementById('r-email').value.trim();
  const tel=document.getElementById('r-tel').value.trim();
  const pass=document.getElementById('r-pass').value;
  const errEl=document.getElementById('reg-err');
  const errTxt=document.getElementById('reg-err-text');
  const btn=document.getElementById('reg-btn');
  if(!nombre||!nit||!email||!pass){ showErr(errEl, errTxt, 'Completa los campos obligatorios'); return; }
  btn.innerHTML='<span class="spinner"></span> Creando cuenta...'; btn.disabled=true;
  try {
    const r=await fetch(API+'/api/v1/auth/registro',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email,nombre,nit,telefono:tel||null,password:pass}),
      credentials:'include',
    });
    const d=await r.json();
    if(!r.ok){
      const msg = r.status===429 ? (d.detail||'Demasiados intentos. Espera 5 minutos.')
                                 : (d.detail||'Error al registrar');
      showErr(errEl, errTxt, msg); return;
    }
    toast('Cuenta creada. Ahora inicia sesión.', 'ok');
    showPanel('login');
    document.getElementById('l-email').value=email;
  }catch(e){ showErr(errEl, errTxt, 'Error de conexión'); }
  finally{ btn.textContent='Crear cuenta'; btn.disabled=false; }
}

async function doLogout() {
  USER_DATA=null;
  try {
    // Llama al backend para expirar las cookies httpOnly
    await fetch(API+'/api/v1/auth/logout', {
      method:'POST',
      credentials:'include',
      headers: authH(),
    });
  } catch(e){}
  document.getElementById('app-screen').style.display='none';
  document.getElementById('auth-screen').style.display='flex';
}

function showErr(el, txtEl, msg){ if(txtEl) txtEl.textContent=msg; el.classList.add('show'); }

// ── APP ──
function showApp() {
  document.getElementById('auth-screen').style.display='none';
  document.getElementById('app-screen').style.display='block';
  initOnboarding();
  loadDashboard();
}

// authH() devuelve headers con CSRF token (para mutaciones).
// credentials:'include' debe pasarse en cada fetch por separado.
function authH(withCsrf=false) {
  const h = {'Content-Type':'application/json'};
  if(withCsrf) { const csrf=getCsrfToken(); if(csrf) h['X-CSRF-Token']=csrf; }
  return h;
}

// Wrapper central para todos los fetch autenticados.
// - Siempre incluye credentials:'include' (envía cookies).
// - Inyecta X-CSRF-Token en métodos mutantes.
// - Redirige al login en 401 (sesión expirada).
async function apiFetch(url, opts={}) {
  const method = (opts.method||'GET').toUpperCase();
  const isMutant = ['POST','PUT','DELETE','PATCH'].includes(method);
  const headers = {
    ...(opts.headers||{}),
    ...(isMutant ? {'X-CSRF-Token': getCsrfToken()} : {}),
  };
  // No forzar Content-Type en FormData
  if(opts.body && !(opts.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const r = await fetch(API+url, {...opts, headers, credentials:'include'});
  if(r.status === 401) { doLogout(); throw new Error('401'); }
  return r;
}

async function loadUserInfo() {
  try {
    const r=await apiFetch('/api/v1/auth/me');
    if(r.ok){ const d=await r.json(); USER_DATA=d; }
  }catch(e){}
  if(USER_DATA){
    const n=USER_DATA.nombre||USER_DATA.email;
    document.getElementById('user-name').textContent=n;
    document.getElementById('user-nit').textContent='NIT '+USER_DATA.nit;
    document.getElementById('user-avatar').textContent=n.substring(0,2).toUpperCase();
  }
}

async function loadDashboard() {
  checkApiStatus();
  // Load cesiones KPIs for dashboard
  apiFetch('/api/v1/cesion/?limit=500').then(r=>r.json()).then(d=>{
    const ces=(d.cesiones||[]).filter(c=>c.estado==='ACEPTADA');
    const tot=ces.reduce((s,c)=>s+(c.valor_cesion||0),0);
    const el=document.getElementById('dash-ces-total');
    if(el) el.textContent='$'+fmtNum(tot)+' en '+ces.length+' cesión'+(ces.length!==1?'es':'');
  }).catch(()=>{});
  try {
    const r=await apiFetch('/api/v1/facturas/?limit=100');
    if(!r.ok) throw new Error();
    const d=await r.json();
    const fs=d.facturas||[];
    document.getElementById('st-total').textContent=d.total||0;
    document.getElementById('st-cedidas').textContent=fs.filter(f=>f.estado==='CEDIDA').length;
    document.getElementById('st-titulos').textContent=fs.filter(f=>f.es_titulo_valor&&f.estado!=='CEDIDA').length;
    document.getElementById('st-proceso').textContent=fs.filter(f=>f.estado==='EN_CESION').length;
    const tbody=document.getElementById('dash-facturas');
    if(!fs.length){
      tbody.innerHTML='<tr><td colspan="4"><div class="empty-hero"><div class="empty-hero-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:28px;color:var(--brand)"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div><div class="empty-hero-title">No has registrado facturas aún</div><div class="empty-hero-sub">Comienza ingresando el CUFE de tu primera factura electrónica emitida por la DIAN</div><button class="btn btn-primary btn-sm" onclick="showPage(\'registrar\')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:13px"><path d="M12 4v16m8-8H4"/></svg>Registrar primera factura</button></div></td></tr>';
      return;
    }
    tbody.innerHTML=fs.slice(0,6).map(f=>`
      <tr onclick="verDetalle('${f.cufe}')" style="cursor:pointer">
        <td><div class="td-primary">${f.prefijo||'FV'}-${f.numero}</div><div class="td-mono">${(f.cufe||'').substring(0,18)}…</div></td>
        <td style="font-size:12px;color:var(--text-secondary)">${f.adquiriente_nombre||'—'}</td>
        <td><div class="td-amount">$${fmtNum(f.valor_total)}</div></td>
        <td>${badgeEstado(f.estado)}</td>
      </tr>`).join('');
  }catch(e){
    document.getElementById('dash-facturas').innerHTML='<tr><td colspan="4"><div class="empty-state" style="padding:20px"><div class="empty-text" style="color:var(--red)">Error cargando facturas</div></div></td></tr>';
  }
}

async function loadFacturas(estado='') {
  const tbody=document.getElementById('facturas-body');
  tbody.innerHTML='<tr><td colspan="6"><div class="empty-state" style="padding:32px"><div class="empty-text">Cargando...</div></div></td></tr>';
  try {
    const url='/api/v1/facturas/?limit=100'+(estado?'&estado='+estado:'');
    const r=await apiFetch(url);
    if(!r.ok) throw new Error();
    const d=await r.json();
    const fs=d.facturas||[];
    document.getElementById('fact-count').textContent='('+d.total+')';
    if(!fs.length){
      tbody.innerHTML=`<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">No hay facturas con este filtro</div><div class="empty-sub"><a style="color:var(--brand);cursor:pointer" onclick="showPage('registrar')">Registrar factura nueva</a></div></div></td></tr>`;
      return;
    }
    tbody.innerHTML=fs.map(f=>`
      <tr>
        <td data-label="Factura"><div class="td-primary">${f.prefijo||'FV'}-${f.numero}</div><div class="td-mono" style="display:flex;align-items:center;gap:4px">${(f.cufe||'').substring(0,16)}… <button onclick="event.stopPropagation();navigator.clipboard.writeText('${f.cufe||''}');toast('CUFE copiado','ok')" style="background:none;border:none;cursor:pointer;color:var(--brand);font-size:10px;padding:1px 4px" title="Copiar CUFE">⧉</button></div></td>
        <td data-label="Adquiriente" style="font-size:12px">${f.adquiriente_nombre||'—'}<div class="td-mono">${f.adquiriente_nit||''}</div></td>
        <td data-label="Valor"><div class="td-amount">$${fmtNum(f.valor_total)}</div></td>
        <td data-label="Vencimiento" style="font-size:12px;color:var(--text-muted)">${fmtDate(f.fecha_vencimiento)}</td>
        <td data-label="Estado">${badgeEstado(f.estado)}</td>
        <td class="td-actions">
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <button class="btn btn-ghost btn-sm" onclick="verDetalle('${f.cufe}')">Ver</button>
            ${f.es_titulo_valor&&f.estado!=='CEDIDA'?`<button class="btn btn-primary btn-sm" onclick="irCeder('${f.cufe}')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:11px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>Ceder</button>`:''}
            ${!f.es_titulo_valor?`<button class="btn btn-success btn-sm" onclick="quickHabilitar('${f.cufe}')">Habilitar</button>`:''}
          </div>
        </td>
      </tr>`).join('');
  }catch(e){ tbody.innerHTML='<tr><td colspan="6"><div class="empty-state"><div class="empty-text" style="color:var(--red)">Error cargando datos</div></div></td></tr>'; }
}

function filterFacturas(btn, estado){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  loadFacturas(estado);
}

function irCeder(cufe){ document.getElementById('f-cufe').value=cufe; showPage('cesion'); }
function irDetalle(cufe){ toast('CUFE copiado: '+cufe.substring(0,16)+'…','info'); }

async function verDetalle(cufe) {
  const modal=document.getElementById('modal-detalle');
  const body=document.getElementById('modal-detalle-body');
  body.innerHTML='<div class="empty-state" style="padding:20px"><div class="empty-text">Cargando...</div></div>';
  modal.classList.add('show');
  try {
    const r=await apiFetch('/api/v1/facturas/'+cufe);
    if(!r.ok) throw new Error();
    const f=await r.json();
    document.getElementById('modal-detalle-title').textContent=`Factura ${f.prefijo||'FV'}-${f.numero}`;
    body.innerHTML=`
      <div class="detail-row"><div class="detail-key">CUFE</div><div class="detail-val mono">${f.cufe||'—'}</div></div>
      <div class="detail-row"><div class="detail-key">Número</div><div class="detail-val">${f.prefijo||'FV'}-${f.numero}</div></div>
      <div class="detail-row"><div class="detail-key">Estado</div><div class="detail-val">${badgeEstado(f.estado)}</div></div>
      <div class="detail-row"><div class="detail-key">Título valor</div><div class="detail-val">${f.es_titulo_valor?'<span class="badge b-green">Sí</span>':'<span class="badge b-gray">No</span>'}</div></div>
      <div class="detail-row"><div class="detail-key">Emisor</div><div class="detail-val">${f.emisor_nombre||'—'}<div class="td-mono" style="margin-top:2px">${f.emisor_nit||''}</div></div></div>
      <div class="detail-row"><div class="detail-key">Adquiriente</div><div class="detail-val">${f.adquiriente_nombre||'—'}<div class="td-mono" style="margin-top:2px">${f.adquiriente_nit||''}</div></div></div>
      <div class="detail-row"><div class="detail-key">Base gravable</div><div class="detail-val td-amount">$${fmtNum(f.valor_base)}</div></div>
      <div class="detail-row"><div class="detail-key">IVA</div><div class="detail-val td-amount">$${fmtNum(f.valor_iva)}</div></div>
      <div class="detail-row"><div class="detail-key">Total</div><div class="detail-val td-amount" style="font-size:15px;color:var(--brand)">$${fmtNum(f.valor_total)}</div></div>
      <div class="detail-row"><div class="detail-key">Fecha emisión</div><div class="detail-val">${fmtDate(f.fecha_emision)}</div></div>
      <div class="detail-row"><div class="detail-key">Vencimiento</div><div class="detail-val">${fmtDate(f.fecha_vencimiento)}</div></div>
      <div style="margin-top:20px;display:flex;gap:10px">
        ${f.es_titulo_valor&&f.estado!=='CEDIDA'?`<button class="btn btn-primary" onclick="irCeder('${f.cufe}');closeModal('modal-detalle')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>Ceder ahora</button>`:''}
        ${!f.es_titulo_valor?`<button class="btn btn-success" onclick="quickHabilitar('${f.cufe}')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Habilitar como título valor</button>`:''}
        <button class="btn btn-ghost" onclick="closeModal('modal-detalle')">Cerrar</button>
      </div>`;
  }catch(e){ body.innerHTML='<div class="empty-state"><div class="empty-text" style="color:var(--red)">Error cargando detalle</div></div>'; }
}

function closeModal(id){ document.getElementById(id).classList.remove('show'); }
document.getElementById('modal-detalle').addEventListener('click', function(e){ if(e.target===this) closeModal('modal-detalle'); });

async function quickHabilitar(cufe) {
  try {
    const r=await apiFetch('/api/v1/facturas/'+cufe+'/habilitar-cesion',{method:'PUT'});
    const d=await r.json();
    if(r.ok){ toast('Factura habilitada como título valor','ok'); loadFacturas(); closeModal('modal-detalle'); OB_PROGRESS.titulo=true; refreshChecklist(); }
    else toast(d.detail||'Error al habilitar','err');
  }catch(e){ toast('Error de conexión','err'); }
}

async function registrarFactura() {
  const fields={cufe:'reg-cufe',numero:'reg-numero',prefijo:'reg-prefijo','emisor_nit':'reg-emisor-nit','emisor_nombre':'reg-emisor-nombre','adquiriente_nit':'reg-adq-nit','adquiriente_nombre':'reg-adq-nombre','valor_base':'reg-base','valor_iva':'reg-iva','valor_total':'reg-total','fecha_emision':'reg-fecha-em','fecha_vencimiento':'reg-fecha-venc'};
  const body={};
  for(const[k,id] of Object.entries(fields)){
    const v=document.getElementById(id).value.trim();
    if(['valor_base','valor_iva','valor_total'].includes(k)) body[k]=parseFloat(v)||0;
    else body[k]=v||undefined;
  }
  if(!body.cufe||!body.numero||!body.emisor_nit||!body.adquiriente_nit||!body.valor_total||!body.fecha_emision||!body.fecha_vencimiento){
    const box=document.getElementById('resp-reg-fact');
    box.className='resp-box show'; box.innerHTML='<div class="resp-err">⚠ Completa todos los campos requeridos (*)</div>'; return;
  }
  const btn=document.getElementById('btn-reg-fact');
  const txt=document.getElementById('btn-reg-fact-text');
  btn.disabled=true; txt.innerHTML='<span class="spinner"></span> Registrando...';
  const box=document.getElementById('resp-reg-fact');
  try {
    const r=await apiFetch('/api/v1/facturas/registrar',{method:'POST',body:JSON.stringify(body)});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok){
      box.innerHTML='<div class="resp-ok">✅ '+d.mensaje+'</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>';
      toast('Factura registrada exitosamente','ok'); OB_PROGRESS.fact=true; refreshChecklist();
    } else {
      box.innerHTML='<div class="resp-err">❌ '+(d.detail||JSON.stringify(d))+'</div>';
    }
  }catch(e){ box.className='resp-box show'; box.innerHTML='<div class="resp-err">❌ Error de conexión</div>'; }
  finally{ btn.disabled=false; txt.textContent='Registrar factura'; }
}

async function habilitarTitulo() {
  const cufe=document.getElementById('f-cufe-hab').value.trim();
  const box=document.getElementById('resp-habilitar');
  if(!cufe){ box.className='resp-box show'; box.innerHTML='<div class="resp-err">Ingresa el CUFE</div>'; return; }
  try {
    const r=await apiFetch('/api/v1/facturas/'+cufe+'/habilitar-cesion',{method:'PUT'});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok){ box.innerHTML='<div class="resp-ok">✅ '+d.mensaje+'</div>'; toast('Factura habilitada','ok'); }
    else box.innerHTML='<div class="resp-err">❌ '+(d.detail||JSON.stringify(d))+'</div>';
  }catch(e){ box.className='resp-box show'; box.innerHTML='<div class="resp-err">❌ Error de conexión</div>'; }
}

async function ceder() {
  const cufe=document.getElementById('f-cufe').value.trim();
  const nit=document.getElementById('f-nit-ces').value.trim();
  const nombre=document.getElementById('f-nombre-ces').value.trim();
  const valor=parseFloat(document.getElementById('f-valor').value);
  const box=document.getElementById('resp-cesion');
  const btn=document.getElementById('btn-ceder');
  const txt=document.getElementById('btn-ceder-text');
  if(!cufe||!nit||!nombre||!valor){
    box.className='resp-box show'; box.innerHTML='<div class="resp-err">⚠ Completa los campos requeridos</div>'; return;
  }
  btn.disabled=true; txt.innerHTML='<span class="spinner"></span> Enviando a DIAN...';
  try {
    const r=await apiFetch('/api/v1/cesion/crear',{method:'POST',body:JSON.stringify({cufe_factura:cufe,cesionario_nit:nit,cesionario_nombre:nombre,valor_cesion:valor})});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok){
      box.innerHTML='<div class="resp-ok">✅ '+d.mensaje+'</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>';
      toast('Cesión registrada en RADIAN','ok'); OB_PROGRESS.cesion=true; refreshChecklist();
    } else {
      box.innerHTML='<div class="resp-err">❌ '+(d.detail||JSON.stringify(d))+'</div>';
    }
  }catch(e){ box.className='resp-box show'; box.innerHTML='<div class="resp-err">❌ Error de conexión</div>'; }
  finally{ btn.disabled=false; txt.textContent='Enviar a DIAN RADIAN'; }
}

async function consultarDian() {
  const cude=document.getElementById('f-cude').value.trim();
  const box=document.getElementById('resp-dian');
  if(!cude){ box.className='resp-box show'; box.innerHTML='<div class="resp-err">Ingresa el CUDE</div>'; return; }
  box.className='resp-box show'; box.innerHTML='<div style="color:#9CA3AF">Consultando DIAN...</div>';
  try {
    const r=await apiFetch('/api/v1/cesion/'+cude+'/estado');
    const d=await r.json();
    box.innerHTML=r.ok?'<div class="resp-ok">✅ Respuesta DIAN</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>':'<div class="resp-err">❌ '+(d.detail||JSON.stringify(d))+'</div>';
  }catch(e){ box.innerHTML='<div class="resp-err">❌ Error de conexión</div>'; }
}

async function pingDian() {
  const box=document.getElementById('resp-ping');
  box.className='resp-box show'; box.innerHTML='<div style="color:#9CA3AF">Verificando conexión DIAN...</div>';
  try {
    const r=await apiFetch('/api/v1/consultas/ping-dian');
    const d=await r.json();
    box.innerHTML=r.ok?'<div class="resp-ok">✅ Conexión exitosa</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>':'<div class="resp-err">❌ '+JSON.stringify(d)+'</div>';
  }catch(e){ box.innerHTML='<div class="resp-err">❌ No se pudo conectar a DIAN</div>'; }
}

async function probarEndpoint() {
  const ep=document.getElementById('ep-sel').value;
  const box=document.getElementById('resp-api');
  box.innerHTML='<div style="color:#9CA3AF">Ejecutando...</div>';
  try {
    const r = ep.startsWith('/api') ? await apiFetch(ep) : await fetch(ep);
    const d=await r.json();
    box.innerHTML='<div class="resp-ok">'+r.status+' OK</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>';
  }catch(e){ box.innerHTML='<div class="resp-err">Error de conexión</div>'; }
}

async function checkApiStatus() {
  try {
    const r=await fetch(API+'/health');
    const el=document.getElementById('status-api');
    el.className='badge '+(r.ok?'b-green':'b-red');
    el.textContent=r.ok?'Activa':'Error';
  }catch(e){
    const el=document.getElementById('status-api');
    el.className='badge b-red'; el.textContent='Sin conexión';
  }
}

// ── MIS CESIONES ──
let _cesionesCache = [];
async function loadCesiones(filtro='') {
  const tbody = document.getElementById('cesiones-body');
  tbody.innerHTML='<tr><td colspan="8"><div class="empty-state" style="padding:32px"><div class="empty-text">Cargando cesiones...</div></div></td></tr>';
  try {
    const r = await apiFetch('/api/v1/cesion/?limit=200');
    if(!r.ok) throw new Error();
    const d = await r.json();
    _cesionesCache = d.cesiones || [];
    renderCesiones(filtro);
  } catch(e) {
    tbody.innerHTML='<tr><td colspan="8"><div class="empty-state"><div class="empty-text" style="color:var(--red)">Error cargando cesiones</div></div></td></tr>';
  }
}
function renderCesiones(filtro='') {
  const ces = filtro ? _cesionesCache.filter(c=>c.estado===filtro) : _cesionesCache;
  document.getElementById('ces-count').textContent = '('+ces.length+')';
  const tbody = document.getElementById('cesiones-body');
  if(!ces.length) {
    tbody.innerHTML='<tr><td colspan="8"><div class="empty-hero"><div class="empty-hero-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:28px;color:var(--brand)"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg></div><div class="empty-hero-title">No has creado cesiones aún</div><div class="empty-hero-sub">Una cesión transfiere el derecho de cobro de una factura a un banco o fondo de inversión via RADIAN Evento 037. La factura debe estar habilitada como título valor primero.</div><button class="btn btn-primary btn-sm" onclick="showPage(\'cesion\')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:13px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>Crear mi primera cesión</button></div></td></tr>';
    return;
  }
  tbody.innerHTML = ces.map(c => `
    <tr>
      <td data-label="Cesión"><div class="td-primary" style="font-size:12px">${c.numero_cesion||'—'}</div><div class="td-mono">${(c.cude||'').substring(0,14)}…</div></td>
      <td data-label="Factura CUFE"><div class="td-mono">${(c.cufe_factura||'').substring(0,16)}…</div></td>
      <td data-label="Cedente" style="font-size:12px">${c.cedente_nombre||'—'}<div class="td-mono">${c.cedente_nit||''}</div></td>
      <td data-label="Cesionario" style="font-size:12px">${c.cesionario_nombre||'—'}<div class="td-mono">${c.cesionario_nit||''}</div></td>
      <td data-label="Valor"><div class="td-amount">$${fmtNum(c.valor_cesion)}</div></td>
      <td data-label="Fecha" style="font-size:12px;color:var(--text-muted)">${fmtDate(c.fecha_cesion)}</td>
      <td data-label="Estado">${badgeCesion(c.estado)}</td>
      <td class="td-actions"><button class="btn btn-ghost btn-sm" onclick="descargarXml('${c.cude}')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
        XML</button></td>
    </tr>`).join('');
}
function filterCesiones(btn, filtro) {
  document.querySelectorAll('#page-cesiones .filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderCesiones(filtro);
}
function descargarXml(cude) {
  window.open(API+'/api/v1/cesion/xml/'+cude, '_blank');
}

// ── REPORTES EXCEL ──
function descargarReporte(tipo) {
  const btn = event && event.target ? event.target.closest('button') : null;
  if(btn){ const orig=btn.innerHTML; btn.innerHTML='<span class="spinner"></span> Generando...'; btn.disabled=true; setTimeout(()=>{btn.innerHTML=orig;btn.disabled=false;},4000); }
  toast('Generando reporte Excel...', 'info'); OB_PROGRESS.reporte=true; refreshChecklist(); saveOnboarding({onboarding_progress:75});
  const url = API+'/api/v1/reportes/'+tipo;
  const a = document.createElement('a');
  a.href = url;
  // Add auth header via fetch + blob
  apiFetch('/api/v1/reportes/'+tipo)
    .then(r => {
      if(!r.ok) throw new Error('Error '+r.status);
      return r.blob();
    })
    .then(blob => {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = tipo+'_'+new Date().toISOString().slice(0,10)+'.xlsx';
      link.click();
      toast('Reporte descargado exitosamente', 'ok');
    })
    .catch(e => toast('Error generando reporte: '+e.message, 'err'));
}
function badgeCesion(e) {
  const m = {'ACEPTADA':'b-green','RECHAZADA':'b-red','PENDIENTE':'b-gold'};
  return `<span class="badge ${m[e]||'b-gray'}">${e||'—'}</span>`;
}

// ── CARTERA ──
async function loadCartera() {
  try {
    const r = await apiFetch('/api/v1/facturas/?limit=200');
    if(!r.ok) throw new Error();
    const d = await r.json();
    const fs = (d.facturas||[]).filter(f=>f.estado!=='CEDIDA'&&f.estado!=='PAGADA');
    const hoy = new Date();
    const buckets = [{min:-Infinity,max:0,id:'0',label:'Al día',color:'var(--green)'},
      {min:1,max:30,id:'30',label:'1–30 días',color:'var(--gold)'},
      {min:31,max:60,id:'60',label:'31–60 días',color:'#F97316'},
      {min:61,max:90,id:'90',label:'61–90 días',color:'var(--red)'},
      {min:91,max:Infinity,id:'over',label:'+90 días',color:'#7F1D1D'}];
    const data = buckets.map(b=>({...b, items:[], total:0}));
    const vencidas = [];
    fs.forEach(f => {
      const venc = new Date(f.fecha_vencimiento);
      const dias = Math.floor((hoy - venc) / 86400000);
      const b = data.find(b=>dias>=b.min&&dias<=b.max) || data[data.length-1];
      b.items.push(f); b.total += f.valor_total||0;
      if(dias > 0) vencidas.push({...f, dias});
    });
    const totalAll = data.reduce((s,b)=>s+b.total, 0) || 1;
    data.forEach(b => {
      document.getElementById('ag-'+b.id).textContent = '$'+fmtNum(b.total);
      document.getElementById('ag-'+b.id+'-n').textContent = b.items.length+' factura'+(b.items.length!==1?'s':'');
    });
    document.getElementById('aging-bars').innerHTML = data.map(b=>`
      <div class="aging-bar-row">
        <div class="aging-bar-label">${b.label}</div>
        <div class="aging-bar-track"><div class="aging-bar-fill" style="width:${(b.total/totalAll*100).toFixed(1)}%;background:${b.color}"></div></div>
        <div class="aging-bar-val">$${fmtNum(b.total)}</div>
      </div>`).join('');
    vencidas.sort((a,b)=>b.dias-a.dias);
    const vbody = document.getElementById('vencidas-body');
    vbody.innerHTML = vencidas.length ? vencidas.slice(0,15).map(f=>`
      <tr>
        <td><div class="td-primary">${f.prefijo||'FV'}-${f.numero}</div></td>
        <td style="font-size:12px">${f.adquiriente_nombre||'—'}</td>
        <td><div class="td-amount">$${fmtNum(f.valor_total)}</div></td>
        <td style="font-size:12px">${fmtDate(f.fecha_vencimiento)}</td>
        <td><span class="badge ${f.dias>90?'b-red':f.dias>60?'b-red':f.dias>30?'b-gold':'b-gold'}">${f.dias}d</span></td>
      </tr>`).join('')
    : '<tr><td colspan="5"><div class="empty-state" style="padding:20px"><div class="empty-text" style="color:var(--green)">✓ Sin facturas vencidas</div></div></td></tr>';
  } catch(e) {
    document.getElementById('vencidas-body').innerHTML='<tr><td colspan="5"><div class="empty-state"><div class="empty-text" style="color:var(--red)">Error cargando datos</div></div></td></tr>';
  }
}

// ── FLUJO DE CAJA ──
async function loadFlujo() {
  try {
    const r = await apiFetch('/api/v1/facturas/?limit=200');
    if(!r.ok) throw new Error();
    const d = await r.json();
    const fs = (d.facturas||[]).filter(f=>f.estado!=='PAGADA');
    const hoy = new Date();
    const months = [];
    for(let i=0;i<6;i++){
      const m = new Date(hoy.getFullYear(), hoy.getMonth()+i, 1);
      months.push({year:m.getFullYear(), month:m.getMonth(), label:m.toLocaleDateString('es-CO',{month:'short',year:'2-digit'}), total:0, count:0});
    }
    let totalFlujo=0, mesActual=0, prox30=0;
    const tabla = [];
    fs.forEach(f => {
      const venc = new Date(f.fecha_vencimiento);
      const dias = Math.floor((venc - hoy) / 86400000);
      totalFlujo += f.valor_total||0;
      if(dias >= 0 && dias <= 30) prox30 += f.valor_total||0;
      const mb = months.find(m=>m.year===venc.getFullYear()&&m.month===venc.getMonth());
      if(mb){ mb.total+=f.valor_total||0; mb.count++; }
      if(venc>=hoy) tabla.push(f);
    });
    const mesH = months[0];
    mesActual = mesH ? mesH.total : 0;
    document.getElementById('flujo-total').textContent = '$'+fmtNum(totalFlujo);
    document.getElementById('flujo-mes').textContent = '$'+fmtNum(mesActual);
    document.getElementById('flujo-prox').textContent = '$'+fmtNum(prox30);
    const maxM = Math.max(...months.map(m=>m.total)) || 1;
    document.getElementById('flujo-chart-wrap').innerHTML = `
      <div>${months.map(m=>`
        <div class="cashflow-month">
          <div class="cashflow-month-label">${m.label}</div>
          <div class="cashflow-bar-track"><div class="cashflow-bar-fill" style="width:${(m.total/maxM*100).toFixed(1)}%"></div></div>
          <div class="cashflow-amount">$${fmtNum(m.total)}</div>
          <div class="cashflow-count">${m.count} fact.</div>
        </div>`).join('')}</div>`;
    tabla.sort((a,b)=>new Date(a.fecha_vencimiento)-new Date(b.fecha_vencimiento));
    document.getElementById('flujo-tabla').innerHTML = tabla.slice(0,20).map(f=>`
      <tr>
        <td><div class="td-primary">${f.prefijo||'FV'}-${f.numero}</div></td>
        <td style="font-size:12px">${f.adquiriente_nombre||'—'}</td>
        <td><div class="td-amount">$${fmtNum(f.valor_total)}</div></td>
        <td style="font-size:12px">${fmtDate(f.fecha_vencimiento)}</td>
      </tr>`).join('') || '<tr><td colspan="4"><div class="empty-state" style="padding:20px"><div class="empty-text">No hay facturas vigentes</div></div></td></tr>';
  } catch(e) {
    document.getElementById('flujo-chart-wrap').innerHTML='<div class="empty-state"><div class="empty-text" style="color:var(--red)">Error cargando flujo</div></div>';
  }
}

// ── LIBRO DIARIO / CONTABILIDAD ──
const PUC = {
  '1305':'Deudores Comerciales — Clientes Nacionales',
  '4135':'Ingresos Financieros — Cesión de Cartera',
  '1310':'Cuentas por Cobrar — Cesiones',
  '2205':'Proveedores Nacionales',
  '1110':'Bancos — Cuenta Corriente',
};
async function loadContabilidad() {
  const periodo = document.getElementById('cont-periodo').value;
  try {
    const r = await apiFetch('/api/v1/cesion/?limit=500');
    if(!r.ok) throw new Error();
    const d = await r.json();
    let ces = (d.cesiones||[]).filter(c=>c.estado==='ACEPTADA');
    if(periodo) ces = ces.filter(c=>(c.fecha_cesion||'').startsWith(periodo));
    const rows = [];
    let totalD=0, totalC=0;
    ces.forEach(c => {
      const val = c.valor_cesion||0;
      const fecha = fmtDate(c.fecha_cesion);
      const ref = c.numero_cesion||c.cude?.substring(0,12)||'—';
      rows.push({fecha, codigo:'1305', cuenta:PUC['1305'], ref, debito:val, credito:0, tipo:'debit'});
      rows.push({fecha, codigo:'4135', cuenta:PUC['4135'], ref, debito:0, credito:val, tipo:'credit'});
      totalD+=val; totalC+=val;
    });
    document.getElementById('cont-asientos').textContent = ces.length;
    document.getElementById('cont-debito').textContent = '$'+fmtNum(totalD);
    document.getElementById('cont-credito').textContent = '$'+fmtNum(totalC);
    const bal = document.getElementById('cont-balance');
    const diff = Math.abs(totalD - totalC);
    bal.textContent = diff < 0.01 ? '✓ Balanceado' : '⚠ $'+fmtNum(diff);
    bal.className = 'stat-value '+(diff<0.01?'balance-ok':'balance-err');
    const tbody = document.getElementById('cont-tbody');
    if(!rows.length){
      tbody.innerHTML='<tr><td colspan="6"><div class="empty-state" style="padding:32px"><div class="empty-icon">📒</div><div class="empty-text">No hay asientos en este período</div><div class="empty-sub">Los asientos se generan automáticamente al crear cesiones</div></div></td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(r=>`
      <tr class="journal-row-${r.tipo}">
        <td style="font-size:12px;color:var(--text-muted);white-space:nowrap">${r.fecha}</td>
        <td><span class="puc-code">${r.codigo}</span></td>
        <td class="${r.tipo==='debit'?'journal-debit':'journal-credit'}" style="font-size:13px">${r.cuenta}</td>
        <td class="journal-ref">${r.ref}</td>
        <td style="text-align:right" class="amount-debit">${r.debito?'$'+fmtNum(r.debito):''}</td>
        <td style="text-align:right" class="amount-credit">${r.credito?'$'+fmtNum(r.credito):''}</td>
      </tr>`).join('');
    document.getElementById('cont-tfoot').innerHTML = `
      <tr style="background:var(--border-soft)">
        <td colspan="4" style="font-size:12px;font-weight:700;padding:12px 16px;color:var(--text-secondary)">TOTALES</td>
        <td style="text-align:right;font-weight:800;padding:12px 16px;color:var(--text-primary)">$${fmtNum(totalD)}</td>
        <td style="text-align:right;font-weight:800;padding:12px 16px;color:var(--text-primary)">$${fmtNum(totalC)}</td>
      </tr>`;
  } catch(e) {
    document.getElementById('cont-tbody').innerHTML='<tr><td colspan="6"><div class="empty-state"><div class="empty-text" style="color:var(--red)">Error cargando libro diario</div></div></td></tr>';
  }
}

// ── ESTADO DE RESULTADOS ──
async function loadResultados() {
  try {
    const r = await apiFetch('/api/v1/cesion/?limit=500');
    if(!r.ok) throw new Error();
    const d = await r.json();
    const ces = (d.cesiones||[]).filter(c=>c.estado==='ACEPTADA');
    const totalIngresos = ces.reduce((s,c)=>s+(c.valor_cesion||0), 0);
    const promedio = ces.length ? totalIngresos/ces.length : 0;
    document.getElementById('pnl-ingresos').textContent = '$'+fmtNum(totalIngresos);
    document.getElementById('pnl-cesiones-n').textContent = ces.length;
    document.getElementById('pnl-promedio').textContent = '$'+fmtNum(promedio);
    // Monthly grouping for bar chart
    const byMonth = {};
    ces.forEach(c => {
      const key = (c.fecha_cesion||'').substring(0,7);
      if(!byMonth[key]) byMonth[key] = {label:key, total:0, count:0};
      byMonth[key].total += c.valor_cesion||0;
      byMonth[key].count++;
    });
    const meses = Object.values(byMonth).sort((a,b)=>a.label.localeCompare(b.label)).slice(-8);
    const maxV = Math.max(...meses.map(m=>m.total)) || 1;
    const bw = 100/Math.max(meses.length,1);
    const chartH = 180;
    const svgBars = meses.map((m,i)=>{
      const h = Math.max((m.total/maxV)*(chartH-40), 4);
      const x = i*bw + bw*0.1;
      const w = bw*0.8;
      const y = chartH - 30 - h;
      const lbl = m.label.substring(5)+'/'+m.label.substring(2,4);
      return `<rect x="${x}%" y="${y}" width="${w}%" height="${h}" rx="3" fill="url(#bg)" opacity="0.9"/>
        <text x="${x+w/2}%" y="${chartH-14}" text-anchor="middle" font-size="9" fill="#9DAEC0">${lbl}</text>
        <text x="${x+w/2}%" y="${y-4}" text-anchor="middle" font-size="9" fill="var(--text-primary)" font-weight="600">${fmtNum(m.total)}</text>`;
    }).join('');
    document.getElementById('resultados-chart').innerHTML = `
      <div class="chart-wrap">
        <svg viewBox="0 0 100 ${chartH}" preserveAspectRatio="none" style="height:${chartH}px">
          <defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1A4FD6"/><stop offset="100%" stop-color="#0891B2"/></linearGradient></defs>
          ${svgBars}
        </svg>
      </div>`;
    // P&L table
    const gastos = totalIngresos * 0.005;
    const utilidad = totalIngresos - gastos;
    document.getElementById('pnl-body').innerHTML = `
      <div class="pnl-section">
        <div class="pnl-section-title">Ingresos Operacionales</div>
        <div class="pnl-row"><span class="pnl-label">4135 — Ingresos por cesión de cartera</span><span class="pnl-val pnl-positive">$${fmtNum(totalIngresos)}</span></div>
        <div class="pnl-row-total"><span>Total Ingresos</span><span class="pnl-positive">$${fmtNum(totalIngresos)}</span></div>
      </div>
      <div class="pnl-section">
        <div class="pnl-section-title">Gastos Operacionales</div>
        <div class="pnl-row"><span class="pnl-label">5105 — Gastos financieros DIAN (0.5%)</span><span class="pnl-val pnl-negative">-$${fmtNum(gastos)}</span></div>
        <div class="pnl-row-total"><span>Total Gastos</span><span class="pnl-negative">-$${fmtNum(gastos)}</span></div>
      </div>
      <div class="pnl-section">
        <div class="pnl-section-title">Resultado</div>
        <div class="pnl-row-total" style="font-size:18px;border-top:2px solid var(--brand)"><span>Utilidad Neta</span><span class="${utilidad>=0?'pnl-positive':'pnl-negative'}">$${fmtNum(utilidad)}</span></div>
      </div>`;
  } catch(e) {
    document.getElementById('pnl-body').innerHTML='<div class="empty-state"><div class="empty-text" style="color:var(--red)">Error cargando resultados</div></div>';
  }
}

// ── MOBILE DRAWER ──────────────────────────────────────────
function openDrawer() {
  document.getElementById('sidebar').classList.add('drawer-open');
  document.getElementById('drawer-overlay').classList.add('show');
  document.body.style.overflow = 'hidden';
}
function closeDrawer() {
  document.getElementById('sidebar').classList.remove('drawer-open');
  document.getElementById('drawer-overlay').classList.remove('show');
  document.body.style.overflow = '';
}

// ── BOTTOM NAV SYNC ─────────────────────────────────────────
const BN_PAGES = ['dashboard','facturas','cesion','cartera','reportes'];
function syncBottomNav(p) {
  BN_PAGES.forEach(pg => {
    const el = document.getElementById('bn-'+pg);
    if(el) el.classList.toggle('active', pg===p);
  });
}

function showPage(p) {
  closeDrawer();
  document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(e=>e.classList.remove('active'));
  const el=document.getElementById('page-'+p); if(el) el.classList.add('active');
  const nav=document.getElementById('nav-'+p); if(nav) nav.classList.add('active');
  syncBottomNav(p);
  const titles={
    dashboard:['Dashboard','Resumen general del sistema RADIAN'],
    facturas:['Facturas','Gestión de facturas electrónicas endosables'],
    registrar:['Registrar Factura','Ingresa una nueva factura electrónica al sistema'],
    cesion:['Nueva Cesión','Enviar evento 037 a RADIAN · DIAN'],
    cesiones:['Mis Cesiones','Historial de cesiones registradas en RADIAN'],
    cartera:['Cartera','Análisis de antigüedad y alertas de vencimiento'],
    flujo:['Flujo de Caja','Proyección de cobros por fechas de vencimiento'],
    contabilidad:['Libro Diario','Asientos contables PUC — generados automáticamente'],
    resultados:['Estado de Resultados','P&L acumulado del período'],
    reportes:['Reportes Excel','Descarga reportes contables profesionales en .xlsx'],
    consultar:['Consultar DIAN','Verificar estado de eventos en RADIAN'],
    api:['API Explorer','Prueba los endpoints directamente']
  };
  const t=titles[p]||[p,''];
  document.getElementById('page-title').textContent=t[0];
  document.getElementById('page-sub').textContent=t[1];
  if(p==='facturas') loadFacturas();
  if(p==='cesiones') loadCesiones();
  if(p==='cartera') loadCartera();
  if(p==='flujo') loadFlujo();
  if(p==='contabilidad') loadContabilidad();
  if(p==='resultados') loadResultados();
}

// ── UTILS ──
function fmtNum(n){
  if(!n&&n!==0) return '—';
  if(n>=1e9) return(n/1e9).toFixed(2)+'B';
  if(n>=1e6) return(n/1e6).toFixed(2)+'M';
  if(n>=1e3) return(n/1e3).toFixed(0)+'K';
  return n.toLocaleString('es-CO');
}
function fmtDate(d){
  if(!d) return '—';
  try{ return new Date(d).toLocaleDateString('es-CO',{day:'2-digit',month:'short',year:'numeric'}); }catch{ return d; }
}
function badgeEstado(e){
  const m={'EMITIDA':'b-gray','VALIDADA_DIAN':'b-blue','EN_CESION':'b-gold','CEDIDA':'b-green','PAGADA':'b-teal','RECHAZADA':'b-red'};
  return `<span class="badge ${m[e]||'b-gray'}">${e||'—'}</span>`;
}
function toast(msg, type){
  const t=document.getElementById('toast');
  const icons={ok:'✓',err:'✕',info:'ℹ'};
  t.innerHTML=`<span style="font-size:14px">${icons[type]||'•'}</span>${msg}`;
  t.className='show '+type;
  clearTimeout(t._t); t._t=setTimeout(()=>t.className='',3500);
}
</script>
</body>
</html>"""

LANDING = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FinPro Capital — Cesión de Facturas Electrónicas RADIAN</title>
<meta name="description" content="Plataforma colombiana para ceder facturas electrónicas ante la DIAN usando RADIAN. Contabilidad automática PUC, reportes Excel y API REST."/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{
  --brand:#1A4FD6;--brand-dark:#1340B0;--brand-light:#EEF3FF;--brand-glow:rgba(26,79,214,.12);
  --teal:#0891B2;--green:#059669;--gold:#D97706;--red:#DC2626;--purple:#7C3AED;
  --bg:#F4F6FA;--surface:#fff;--border:#E4E9F0;--text:#0D1B2E;--text2:#5A6A7E;--text3:#9DAEC0;
  --sidebar:#0B1829;--radius:10px;--radius-lg:14px;--radius-xl:20px;
  --shadow:0 1px 3px rgba(13,27,46,.06),0 4px 16px rgba(13,27,46,.04);
  --shadow-md:0 4px 24px rgba(13,27,46,.1),0 1px 4px rgba(13,27,46,.06);
  --shadow-lg:0 16px 48px rgba(13,27,46,.15),0 2px 8px rgba(13,27,46,.08);
  --font:'Inter',system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:#fff;color:var(--text);-webkit-font-smoothing:antialiased;overflow-x:hidden}

/* ── NAVBAR ── */
.navbar{position:fixed;top:0;left:0;right:0;z-index:1000;height:64px;display:flex;align-items:center;padding:0 5%;border-bottom:1px solid transparent;transition:.3s}
.navbar.scrolled{background:rgba(255,255,255,.92);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-color:var(--border);box-shadow:0 1px 12px rgba(13,27,46,.06)}
.nav-logo{font-size:18px;font-weight:900;color:var(--text);letter-spacing:-.5px;text-decoration:none;display:flex;align-items:center;gap:8px}
.nav-logo em{font-style:normal;color:var(--brand)}
.nav-logo-icon{width:32px;height:32px;background:linear-gradient(135deg,var(--brand),var(--teal));border-radius:8px;display:flex;align-items:center;justify-content:center}
.nav-links{display:flex;align-items:center;gap:6px;margin:0 auto;list-style:none}
.nav-links a{font-size:14px;font-weight:500;color:var(--text2);text-decoration:none;padding:7px 14px;border-radius:8px;transition:.15s}
.nav-links a:hover{color:var(--brand);background:var(--brand-light)}
.nav-actions{display:flex;align-items:center;gap:10px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 20px;border-radius:var(--radius);font-size:14px;font-weight:600;cursor:pointer;border:none;font-family:var(--font);transition:.18s;text-decoration:none;white-space:nowrap}
.btn:active{transform:scale(.97)}
.btn-ghost{background:transparent;border:1.5px solid var(--border);color:var(--text2)}
.btn-ghost:hover{border-color:var(--brand);color:var(--brand);background:var(--brand-light)}
.btn-primary{background:var(--brand);color:#fff}
.btn-primary:hover{background:var(--brand-dark);box-shadow:0 4px 16px rgba(26,79,214,.3)}
.btn-lg{padding:14px 28px;font-size:15px;border-radius:var(--radius-lg)}
.btn-outline-white{background:transparent;border:2px solid rgba(255,255,255,.4);color:#fff}
.btn-outline-white:hover{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.7)}
.hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer;padding:6px;border:none;background:transparent}
.hamburger span{width:22px;height:2px;background:var(--text);border-radius:2px;transition:.25s}
.mobile-menu{display:none}
@media(max-width:768px){
  .nav-links,.nav-actions .btn-ghost{display:none}
  .hamburger{display:flex}
  .mobile-menu{position:fixed;top:64px;left:0;right:0;background:#fff;border-bottom:1px solid var(--border);padding:20px 5%;box-shadow:var(--shadow-md);z-index:999}
  .mobile-menu.open{display:block}
  .mobile-menu a{display:block;padding:12px 0;font-size:15px;font-weight:500;color:var(--text2);text-decoration:none;border-bottom:1px solid var(--border)}
  .mobile-menu a:last-child{border:none}
}

/* ── HERO ── */
.hero{min-height:100vh;background:linear-gradient(145deg,#050E1F 0%,#0A1E45 45%,#0F2E6E 75%,#1A4FD6 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:120px 5% 80px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;inset:0;background:url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23FFFFFF' fill-opacity='0.025'%3E%3Cpath d='M40 40m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0'/%3E%3C/g%3E%3C/svg%3E")}
.hero-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:99px;padding:6px 16px;font-size:12px;font-weight:600;color:rgba(255,255,255,.75);margin-bottom:28px;letter-spacing:.5px}
.hero-badge span{width:6px;height:6px;background:#34D399;border-radius:50%;animation:pulse-green 2s infinite}
@keyframes pulse-green{0%,100%{box-shadow:0 0 0 0 rgba(52,211,153,.4)}50%{box-shadow:0 0 0 6px rgba(52,211,153,0)}}
.hero h1{font-size:clamp(32px,5vw,64px);font-weight:900;color:#fff;line-height:1.1;letter-spacing:-2px;max-width:820px;margin-bottom:24px}
.hero h1 em{font-style:normal;background:linear-gradient(90deg,#5EAEFF,#34D399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{font-size:clamp(16px,2vw,20px);color:rgba(255,255,255,.65);max-width:620px;line-height:1.65;margin-bottom:40px;font-weight:400}
.hero-ctas{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-bottom:48px}
.hero-trust{display:flex;align-items:center;gap:6px;font-size:12px;color:rgba(255,255,255,.4);letter-spacing:.5px}
.hero-trust svg{width:14px;opacity:.4}
.hero-trust-dot{width:3px;height:3px;border-radius:50%;background:rgba(255,255,255,.25)}
/* Floating cards removed */

/* ── STATS BAR ── */
.stats-bar{background:#fff;border-bottom:1px solid var(--border);padding:40px 5%}
.stats-inner{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:repeat(3,1fr);gap:0}
.stat-item{text-align:center;padding:0 30px;position:relative}
.stat-item+.stat-item::before{content:'';position:absolute;left:0;top:20%;bottom:20%;width:1px;background:var(--border)}
.stat-num{font-size:clamp(36px,4vw,54px);font-weight:900;color:var(--text);letter-spacing:-2px;line-height:1}
.stat-num span{color:var(--brand)}
.stat-label{font-size:14px;color:var(--text2);margin-top:8px;font-weight:500}
.stat-sub{font-size:12px;color:var(--text3);margin-top:4px}
@media(max-width:600px){.stats-inner{grid-template-columns:1fr}.stat-item+.stat-item::before{display:none}.stat-item{padding:20px 0;border-top:1px solid var(--border)}}

/* ── SECTIONS COMMON ── */
section{padding:80px 5%}
.section-inner{max-width:1100px;margin:0 auto}
.section-tag{display:inline-block;background:var(--brand-light);color:var(--brand);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:2px;padding:5px 14px;border-radius:99px;margin-bottom:16px}
.section-title{font-size:clamp(26px,3.5vw,40px);font-weight:800;color:var(--text);letter-spacing:-1px;line-height:1.2;margin-bottom:14px}
.section-sub{font-size:16px;color:var(--text2);max-width:600px;line-height:1.65}

/* ── FEATURES ── */
.features-bg{background:var(--bg)}
.features-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:48px}
.feat-card{background:#fff;border:1px solid var(--border);border-radius:var(--radius-lg);padding:28px;transition:.2s;position:relative;overflow:hidden}
.feat-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;border-radius:0 0 2px 2px;opacity:0;transition:.2s}
.feat-card:hover{box-shadow:var(--shadow-md);transform:translateY(-3px)}
.feat-card:hover::after{opacity:1}
.feat-card:nth-child(1)::after{background:linear-gradient(90deg,var(--brand),var(--teal))}
.feat-card:nth-child(2)::after{background:linear-gradient(90deg,var(--teal),var(--green))}
.feat-card:nth-child(3)::after{background:linear-gradient(90deg,var(--green),#34D399)}
.feat-card:nth-child(4)::after{background:linear-gradient(90deg,var(--gold),#FCD34D)}
.feat-card:nth-child(5)::after{background:linear-gradient(90deg,var(--purple),#A78BFA)}
.feat-card:nth-child(6)::after{background:linear-gradient(90deg,var(--red),#F87171)}
.feat-icon{width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:18px}
.feat-icon svg{width:22px;height:22px}
.fi-blue{background:var(--brand-light);color:var(--brand)}
.fi-teal{background:#F0FDFF;color:var(--teal)}
.fi-green{background:#ECFDF5;color:var(--green)}
.fi-gold{background:#FFFBEB;color:var(--gold)}
.fi-purple{background:#F5F3FF;color:var(--purple)}
.fi-red{background:#FEF2F2;color:var(--red)}
.feat-title{font-size:16px;font-weight:700;color:var(--text);margin-bottom:8px}
.feat-desc{font-size:13px;color:var(--text2);line-height:1.65}
@media(max-width:900px){.features-grid{grid-template-columns:1fr 1fr}}
@media(max-width:580px){.features-grid{grid-template-columns:1fr}}

/* ── HOW IT WORKS ── */
.how-inner{display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:center;margin-top:48px}
.steps-list{display:flex;flex-direction:column;gap:0}
.step-item{display:flex;gap:20px;padding:24px 0;border-bottom:1px solid var(--border);cursor:pointer;transition:.15s;border-radius:8px}
.step-item:last-child{border-bottom:none}
.step-item.active .step-circle{background:var(--brand);border-color:var(--brand);color:#fff}
.step-item.active .step-title{color:var(--brand)}
.step-circle{width:40px;height:40px;border-radius:50%;border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;color:var(--text3);flex-shrink:0;transition:.2s;margin-top:2px}
.step-title{font-size:16px;font-weight:700;color:var(--text);margin-bottom:6px;transition:.2s}
.step-desc{font-size:13px;color:var(--text2);line-height:1.6}
.step-visual{background:linear-gradient(145deg,var(--sidebar),#0F2554);border-radius:var(--radius-xl);padding:32px;min-height:360px;display:flex;flex-direction:column;justify-content:center;position:relative;overflow:hidden}
.step-visual::before{content:'';position:absolute;inset:0;background:url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23FFFFFF' fill-opacity='0.03'%3E%3Ccircle cx='20' cy='20' r='1'/%3E%3C/g%3E%3C/svg%3E")}
.visual-panel{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:18px;margin-bottom:12px;position:relative;z-index:1}
.visual-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,.35);margin-bottom:10px}
.visual-field{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:10px 14px;font-size:12px;color:rgba(255,255,255,.6);font-family:monospace;margin-bottom:8px;word-break:break-all}
.visual-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(5,150,105,.15);border:1px solid rgba(5,150,105,.3);border-radius:99px;padding:4px 12px;font-size:11px;font-weight:700;color:#34D399}
.visual-badge::before{content:'';width:6px;height:6px;border-radius:50%;background:#34D399}
@media(max-width:860px){.how-inner{grid-template-columns:1fr;gap:40px}}

/* ── PRICING ── */
.pricing-bg{background:linear-gradient(180deg,#fff 0%,var(--bg) 100%)}
.pricing-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:48px}
.price-card{background:#fff;border:1.5px solid var(--border);border-radius:var(--radius-xl);padding:32px;position:relative;transition:.2s}
.price-card:hover{box-shadow:var(--shadow-lg);transform:translateY(-4px)}
.price-card.featured{border-color:var(--brand);background:linear-gradient(145deg,#FAFCFF,#EEF3FF)}
.price-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:linear-gradient(90deg,var(--brand),var(--teal));color:#fff;font-size:11px;font-weight:800;padding:4px 16px;border-radius:99px;letter-spacing:.5px;white-space:nowrap}
.price-tier{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--text2);margin-bottom:14px}
.price-amount{font-size:42px;font-weight:900;color:var(--text);letter-spacing:-2px;line-height:1}
.price-amount sup{font-size:18px;font-weight:700;letter-spacing:0;vertical-align:super}
.price-amount sub{font-size:13px;font-weight:500;color:var(--text2);letter-spacing:0;vertical-align:baseline;margin-left:2px}
.price-desc{font-size:13px;color:var(--text2);margin:12px 0 24px;line-height:1.5;min-height:40px}
.price-divider{height:1px;background:var(--border);margin-bottom:22px}
.price-features{list-style:none;display:flex;flex-direction:column;gap:10px;margin-bottom:28px}
.price-features li{display:flex;align-items:flex-start;gap:10px;font-size:13px;color:var(--text2)}
.price-features li::before{content:'✓';color:var(--green);font-weight:800;flex-shrink:0;font-size:12px;margin-top:1px}
.price-features li.no::before{content:'✕';color:var(--text3)}
.price-features li.no{color:var(--text3)}
.price-cta{width:100%;padding:13px;border-radius:var(--radius);font-size:14px;font-weight:700;cursor:pointer;font-family:var(--font);transition:.18s;text-align:center;display:block;text-decoration:none}
.cta-outlined{background:transparent;border:1.5px solid var(--border);color:var(--text2)}
.cta-outlined:hover{border-color:var(--brand);color:var(--brand);background:var(--brand-light)}
.cta-brand{background:var(--brand);color:#fff;border:none}
.cta-brand:hover{background:var(--brand-dark);box-shadow:0 4px 16px rgba(26,79,214,.3)}
.cta-dark{background:var(--sidebar);color:#fff;border:none}
.cta-dark:hover{background:#0D2040}
@media(max-width:860px){.pricing-grid{grid-template-columns:1fr}}

/* ── FAQ ── */
.faq-list{margin-top:48px;max-width:780px;margin-left:auto;margin-right:auto;display:flex;flex-direction:column;gap:12px}
.faq-item{border:1.5px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;transition:.15s}
.faq-item.open{border-color:var(--brand);box-shadow:0 0 0 4px rgba(26,79,214,.06)}
.faq-q{display:flex;align-items:center;justify-content:space-between;padding:20px 24px;cursor:pointer;user-select:none}
.faq-q-text{font-size:15px;font-weight:600;color:var(--text)}
.faq-icon{width:28px;height:28px;border-radius:50%;border:1.5px solid var(--border);display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.25s;color:var(--text2)}
.faq-item.open .faq-icon{background:var(--brand);border-color:var(--brand);color:#fff;transform:rotate(45deg)}
.faq-a{max-height:0;overflow:hidden;transition:max-height .35s ease,padding .2s}
.faq-a-inner{padding:0 24px 20px;font-size:14px;color:var(--text2);line-height:1.7}
.faq-item.open .faq-a{max-height:400px}

/* ── CTA BAND ── */
.cta-band{background:linear-gradient(135deg,#071120 0%,#0F2554 50%,#1A4FD6 100%);padding:80px 5%;text-align:center;position:relative;overflow:hidden}
.cta-band::before{content:'';position:absolute;inset:0;background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23FFFFFF' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4z'/%3E%3C/g%3E%3C/svg%3E")}
.cta-band h2{font-size:clamp(26px,3.5vw,42px);font-weight:900;color:#fff;letter-spacing:-1px;max-width:640px;margin:0 auto 16px;position:relative}
.cta-band p{font-size:16px;color:rgba(255,255,255,.6);max-width:500px;margin:0 auto 36px;position:relative}
.cta-band-actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;position:relative}
.btn-white{background:#fff;color:var(--brand);border:none;font-weight:700}
.btn-white:hover{background:var(--brand-light);box-shadow:0 4px 20px rgba(255,255,255,.2)}

/* ── FOOTER ── */
footer{background:var(--sidebar);padding:60px 5% 32px;color:rgba(255,255,255,.5)}
.footer-inner{max-width:1100px;margin:0 auto}
.footer-top{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:40px;margin-bottom:48px}
.footer-brand{font-size:18px;font-weight:900;color:#fff;letter-spacing:-.5px;margin-bottom:12px}
.footer-brand em{font-style:normal;color:#5EAEFF}
.footer-tagline{font-size:13px;line-height:1.6;max-width:260px;margin-bottom:20px}
.footer-social{display:flex;gap:10px}
.social-btn{width:34px;height:34px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);border-radius:8px;display:flex;align-items:center;justify-content:center;transition:.15s;text-decoration:none;color:rgba(255,255,255,.5)}
.social-btn:hover{background:rgba(255,255,255,.12);color:#fff}
.footer-col h4{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,.3);margin-bottom:14px}
.footer-col ul{list-style:none;display:flex;flex-direction:column;gap:10px}
.footer-col ul li a{font-size:13px;color:rgba(255,255,255,.4);text-decoration:none;transition:.15s}
.footer-col ul li a:hover{color:#fff}
.footer-bottom{border-top:1px solid rgba(255,255,255,.07);padding-top:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.footer-legal{font-size:12px}
.footer-badges{display:flex;gap:8px}
.f-badge{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:6px;padding:4px 10px;font-size:10px;font-weight:700;letter-spacing:.5px;color:rgba(255,255,255,.35)}
@media(max-width:860px){.footer-top{grid-template-columns:1fr 1fr}}
@media(max-width:500px){.footer-top{grid-template-columns:1fr}}

/* ── MODAL DEMO ── */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;display:none;align-items:center;justify-content:center;backdrop-filter:blur(6px);padding:20px}
.modal-overlay.show{display:flex}
.modal-box{background:#fff;border-radius:var(--radius-xl);width:100%;max-width:680px;overflow:hidden;box-shadow:0 32px 80px rgba(0,0,0,.3)}
.modal-header{background:var(--sidebar);padding:20px 24px;display:flex;align-items:center;justify-content:space-between}
.modal-header-title{font-size:15px;font-weight:700;color:#fff}
.modal-x{width:30px;height:30px;background:rgba(255,255,255,.08);border:none;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,.6);font-size:18px;transition:.15s}
.modal-x:hover{background:rgba(255,255,255,.15);color:#fff}
.modal-video{aspect-ratio:16/9;background:linear-gradient(135deg,#0A1E45,#1A4FD6);display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;cursor:pointer;position:relative;overflow:hidden}
.play-btn{width:72px;height:72px;background:rgba(255,255,255,.15);backdrop-filter:blur(8px);border:2px solid rgba(255,255,255,.3);border-radius:50%;display:flex;align-items:center;justify-content:center;transition:.2s}
.play-btn:hover{background:rgba(255,255,255,.25);transform:scale(1.08)}
.play-btn svg{width:28px;height:28px;color:#fff;margin-left:4px}
.modal-video-text{font-size:14px;color:rgba(255,255,255,.6);font-weight:500}
.modal-video-badge{position:absolute;top:16px;right:16px;background:rgba(220,38,38,.9);color:#fff;font-size:11px;font-weight:700;padding:4px 10px;border-radius:6px;letter-spacing:.3px}
.modal-body{padding:24px}
.demo-steps{display:flex;gap:12px;flex-wrap:wrap}
.demo-step{flex:1;min-width:140px;background:var(--bg);border-radius:var(--radius);padding:14px;text-align:center}
.demo-step-num{font-size:20px;font-weight:900;color:var(--brand);margin-bottom:4px}
.demo-step-label{font-size:12px;color:var(--text2);font-weight:500;line-height:1.4}

/* ── SCROLL ANIMATIONS ── */
.reveal{opacity:0;transform:translateY(28px);transition:opacity .6s ease,transform .6s ease}
.reveal.visible{opacity:1;transform:translateY(0)}
.reveal-delay-1{transition-delay:.1s}
.reveal-delay-2{transition-delay:.2s}
.reveal-delay-3{transition-delay:.3s}
.reveal-delay-4{transition-delay:.4s}
.reveal-delay-5{transition-delay:.5s}
</style>
</head>
<body>

<!-- ══ NAVBAR ══ -->
<nav class="navbar" id="navbar">
  <a href="/" class="nav-logo">
    <div class="nav-logo-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" style="width:16px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
    </div>
    FINPRO<em>CAPITAL</em>
  </a>
  <ul class="nav-links">
    <li><a href="#caracteristicas">Características</a></li>
    <li><a href="#como-funciona">Cómo funciona</a></li>
    <li><a href="#precios">Precios</a></li>
    <li><a href="#faq">FAQ</a></li>
    <li><a href="/openapi.json" target="_blank">API Docs</a></li>
  </ul>
  <div class="nav-actions">
    <a href="/app" class="btn btn-ghost" style="font-size:13px">Iniciar sesión</a>
    <a href="/app?register=1" class="btn btn-primary" style="font-size:13px">Crear cuenta gratis</a>
  </div>
  <button class="hamburger" onclick="toggleMenu()" aria-label="Menú">
    <span></span><span></span><span></span>
  </button>
</nav>
<div class="mobile-menu" id="mobile-menu">
  <a href="#caracteristicas" onclick="closeMenu()">Características</a>
  <a href="#como-funciona" onclick="closeMenu()">Cómo funciona</a>
  <a href="#precios" onclick="closeMenu()">Precios</a>
  <a href="#faq" onclick="closeMenu()">FAQ</a>
  <a href="/openapi.json" target="_blank">API Docs</a>
  <a href="/app" style="color:var(--brand);font-weight:700">Iniciar sesión →</a>
</div>

<!-- ══ HERO ══ -->
<section class="hero" id="hero">
  <div class="hero-badge">
    <span></span>
    Integrado con DIAN &nbsp;·&nbsp; RADIAN &nbsp;·&nbsp; Facturación Electrónica
  </div>
  <h1>Cede tus facturas<br>electrónicas ante la <em>DIAN</em><br>en minutos</h1>
  <p class="hero-sub">La única plataforma que automatiza el proceso RADIAN completo: registro, habilitación como título valor y cesión de crédito, con contabilidad automática PUC incluida.</p>
  <div class="hero-ctas">
    <a href="/app?register=1" class="btn btn-primary btn-lg">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:16px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
      Crear cuenta gratis
    </a>
    <button class="btn btn-outline-white btn-lg" onclick="openDemo()">
      <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px"><path d="M5 3l14 9-14 9V3z"/></svg>
      Ver demo
    </button>
  </div>
  <div class="hero-trust">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
    Seguro &nbsp;<div class="hero-trust-dot"></div>&nbsp; HTTPS &nbsp;<div class="hero-trust-dot"></div>&nbsp; JWT httpOnly &nbsp;<div class="hero-trust-dot"></div>&nbsp; Datos en Colombia
  </div>
</section>

<!-- ══ STATS BAR ══ -->
<div class="stats-bar">
  <div class="stats-inner">
    <div class="stat-item reveal">
      <div class="stat-num"><span>+12.400</span></div>
      <div class="stat-label">Facturas procesadas</div>
      <div class="stat-sub">Registradas y cedidas en RADIAN</div>
    </div>
    <div class="stat-item reveal reveal-delay-2">
      <div class="stat-num"><span>340</span></div>
      <div class="stat-label">Empresas activas</div>
      <div class="stat-sub">PyMEs y grandes empresas</div>
    </div>
    <div class="stat-item reveal reveal-delay-4">
      <div class="stat-num"><span>&lt;2s</span></div>
      <div class="stat-label">Tiempo de cesión</div>
      <div class="stat-sub">Respuesta DIAN en tiempo real</div>
    </div>
  </div>
</div>

<!-- ══ CARACTERÍSTICAS ══ -->
<section class="features-bg" id="caracteristicas">
  <div class="section-inner">
    <div style="text-align:center;margin-bottom:0">
      <div class="section-tag reveal">Plataforma completa</div>
      <h2 class="section-title reveal">Todo lo que necesitas<br>para ceder facturas</h2>
      <p class="section-sub reveal" style="margin:0 auto">Desde el registro del CUFE hasta los asientos contables automáticos — sin salir de la plataforma.</p>
    </div>
    <div class="features-grid">
      <div class="feat-card reveal">
        <div class="feat-icon fi-blue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        </div>
        <div class="feat-title">Registro de facturas con CUFE</div>
        <div class="feat-desc">Ingresa facturas electrónicas con su Código Único de Factura Electrónica emitido por la DIAN. Validación automática de 96 caracteres hexadecimales.</div>
      </div>
      <div class="feat-card reveal reveal-delay-1">
        <div class="feat-icon fi-teal">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg>
        </div>
        <div class="feat-title">Habilitación como título valor</div>
        <div class="feat-desc">Convierte facturas electrónicas en títulos valores endosables con un clic. Cumple el proceso requerido por la DIAN antes de la cesión.</div>
      </div>
      <div class="feat-card reveal reveal-delay-2">
        <div class="feat-icon fi-green">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        </div>
        <div class="feat-title">Cesión RADIAN — Evento 037</div>
        <div class="feat-desc">Genera, firma digitalmente y envía el XML UBL 2.1 con SHA-384 al sistema RADIAN de la DIAN. Respuesta en menos de 2 segundos.</div>
      </div>
      <div class="feat-card reveal reveal-delay-3">
        <div class="feat-icon fi-gold">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
        </div>
        <div class="feat-title">Contabilidad automática PUC</div>
        <div class="feat-desc">Cada cesión genera asientos contables automáticamente con cuentas PUC colombianas (1305 Deudores · 4135 Ingresos). Libro diario en tiempo real.</div>
      </div>
      <div class="feat-card reveal reveal-delay-4">
        <div class="feat-icon fi-purple">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
        </div>
        <div class="feat-title">Reportes Excel profesionales</div>
        <div class="feat-desc">Descarga libro diario, análisis de cartera, estado de resultados, flujo de caja y reporte consolidado con formato contable y gráficas incluidas.</div>
      </div>
      <div class="feat-card reveal reveal-delay-5">
        <div class="feat-icon fi-red">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
        </div>
        <div class="feat-title">API REST + Explorer integrado</div>
        <div class="feat-desc">Integra RADIAN directamente en tu ERP con nuestra API REST documentada. Incluye explorador interactivo y schema OpenAPI/JSON.</div>
      </div>
    </div>
  </div>
</section>

<!-- ══ CÓMO FUNCIONA ══ -->
<section id="como-funciona">
  <div class="section-inner">
    <div class="section-tag reveal">Proceso simplificado</div>
    <h2 class="section-title reveal">3 pasos para ceder<br>una factura electrónica</h2>
    <p class="section-sub reveal">Lo que antes tomaba días de trámites, ahora lo haces en minutos desde tu navegador.</p>
    <div class="how-inner">
      <div class="steps-list">
        <div class="step-item active reveal" onclick="setStep(0)">
          <div class="step-circle">1</div>
          <div>
            <div class="step-title">Registra tu factura con el CUFE</div>
            <div class="step-desc">Ingresa los datos de tu factura electrónica: CUFE, número, emisor, adquiriente y valores. La plataforma valida automáticamente el formato DIAN.</div>
          </div>
        </div>
        <div class="step-item reveal reveal-delay-1" onclick="setStep(1)">
          <div class="step-circle">2</div>
          <div>
            <div class="step-title">Habilítala como título valor</div>
            <div class="step-desc">Con un clic conviertes la factura en un título valor endosable. La plataforma actualiza el estado en Supabase y queda lista para ceder.</div>
          </div>
        </div>
        <div class="step-item reveal reveal-delay-2" onclick="setStep(2)">
          <div class="step-circle">3</div>
          <div>
            <div class="step-title">Cede el crédito ante la DIAN</div>
            <div class="step-desc">Ingresa el NIT y nombre del cesionario, el valor a ceder. La plataforma construye el XML UBL 2.1, lo firma con SHA-384 y lo envía a RADIAN. Contabilidad generada automáticamente.</div>
          </div>
        </div>
      </div>
      <div class="step-visual" id="step-visual">
        <div class="visual-panel" id="sv-0">
          <div class="visual-label">Registrar Factura</div>
          <div class="visual-field">CUFE: a1b2c3d4e5f6...96chars</div>
          <div class="visual-field">FV-00001 · EMPRESA SAS</div>
          <div class="visual-field">$120.000.000 COP · 2026-05-30</div>
          <div class="visual-badge">Factura registrada · EMITIDA</div>
        </div>
        <div class="visual-panel" id="sv-1" style="display:none">
          <div class="visual-label">Habilitar como título valor</div>
          <div class="visual-field">es_titulo_valor: true</div>
          <div class="visual-field">Estado: VALIDADA_DIAN</div>
          <div class="visual-badge">Lista para ceder · ✓</div>
        </div>
        <div class="visual-panel" id="sv-2" style="display:none">
          <div class="visual-label">Cesión RADIAN — Evento 037</div>
          <div class="visual-field">CUDE: sha384_hash...</div>
          <div class="visual-field">Cesionario: BANCO SAS · NIT 900.x</div>
          <div class="visual-field">PUC 1305 Dr $120M · 4135 Cr $120M</div>
          <div class="visual-badge">Aceptado por DIAN · &lt;2s</div>
        </div>
        <div style="position:relative;z-index:1;margin-top:12px;display:flex;gap:8px">
          <div onclick="setStep(0)" style="flex:1;height:3px;border-radius:99px;background:rgba(255,255,255,.15);cursor:pointer" id="dot-0"><div style="height:100%;border-radius:99px;background:var(--teal);width:100%"></div></div>
          <div onclick="setStep(1)" style="flex:1;height:3px;border-radius:99px;background:rgba(255,255,255,.15);cursor:pointer" id="dot-1"></div>
          <div onclick="setStep(2)" style="flex:1;height:3px;border-radius:99px;background:rgba(255,255,255,.15);cursor:pointer" id="dot-2"></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ══ PRICING ══ -->
<section class="pricing-bg" id="precios">
  <div class="section-inner">
    <div style="text-align:center">
      <div class="section-tag reveal">Precios transparentes</div>
      <h2 class="section-title reveal">Planes para cada empresa</h2>
      <p class="section-sub reveal" style="margin:0 auto">Sin contratos anuales. Cancela cuando quieras. Factura en pesos colombianos.</p>
    </div>
    <div class="pricing-grid">
      <div class="price-card reveal">
        <div class="price-tier">Starter</div>
        <div class="price-amount">Gratis<sub style="font-size:14px;color:var(--text2)"> siempre</sub></div>
        <div class="price-desc">Ideal para probar la plataforma y proyectos pequeños con pocas facturas al mes.</div>
        <div class="price-divider"></div>
        <ul class="price-features">
          <li>Hasta 10 facturas / mes</li>
          <li>1 usuario</li>
          <li>Cesiones RADIAN ilimitadas</li>
          <li>Contabilidad automática PUC</li>
          <li>API REST acceso completo</li>
          <li class="no">Reportes Excel</li>
          <li class="no">Soporte prioritario</li>
          <li class="no">Integración ERP</li>
        </ul>
        <a href="/app?register=1" class="price-cta cta-outlined">Comenzar gratis</a>
      </div>
      <div class="price-card featured reveal reveal-delay-2">
        <div class="price-badge">MÁS POPULAR</div>
        <div class="price-tier" style="color:var(--brand)">Pro</div>
        <div class="price-amount"><sup>$</sup>99.000<sub>/mes</sub></div>
        <div class="price-desc">Para empresas que cedan facturas regularmente y necesitan reportes y soporte dedicado.</div>
        <div class="price-divider"></div>
        <ul class="price-features">
          <li>Facturas ilimitadas</li>
          <li>Hasta 5 usuarios</li>
          <li>Cesiones RADIAN ilimitadas</li>
          <li>Contabilidad automática PUC</li>
          <li>API REST acceso completo</li>
          <li>Reportes Excel profesionales</li>
          <li>Soporte prioritario (chat)</li>
          <li class="no">Integración ERP personalizada</li>
        </ul>
        <a href="/app?register=1" class="price-cta cta-brand">Empezar con Pro</a>
      </div>
      <div class="price-card reveal reveal-delay-4">
        <div class="price-tier">Enterprise</div>
        <div class="price-amount" style="font-size:32px">Precio<br>personalizado</div>
        <div class="price-desc">Para grupos empresariales, fondos de inversión y entidades financieras con alto volumen.</div>
        <div class="price-divider"></div>
        <ul class="price-features">
          <li>Volumen ilimitado</li>
          <li>Usuarios ilimitados</li>
          <li>SLA 99.9% uptime</li>
          <li>Integración ERP personalizada</li>
          <li>Reportes a medida</li>
          <li>Onboarding dedicado</li>
          <li>Soporte 24/7 vía canal directo</li>
          <li>Factura electrónica incluida</li>
        </ul>
        <a href="mailto:ventas@finprocapital.co" class="price-cta cta-dark">Contactar ventas</a>
      </div>
    </div>
  </div>
</section>

<!-- ══ FAQ ══ -->
<section id="faq">
  <div class="section-inner">
    <div style="text-align:center;margin-bottom:0">
      <div class="section-tag reveal">Preguntas frecuentes</div>
      <h2 class="section-title reveal">Todo lo que necesitas saber<br>sobre RADIAN y cesión</h2>
    </div>
    <div class="faq-list">
      <div class="faq-item reveal" onclick="toggleFaq(this)">
        <div class="faq-q">
          <span class="faq-q-text">¿Qué es RADIAN y para qué sirve?</span>
          <div class="faq-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px"><path d="M12 5v14M5 12h14"/></svg></div>
        </div>
        <div class="faq-a"><div class="faq-a-inner">RADIAN (Registro de Facturas Electrónicas de Venta como Título Valor) es el sistema de la DIAN que permite registrar facturas electrónicas como títulos valores y cederlas (endosarlas) a terceros — por ejemplo, a un banco o fondo de inversión para obtener liquidez anticipada. FinPro Capital automatiza todo el proceso técnico de integración con RADIAN mediante el Evento 037.</div></div>
      </div>
      <div class="faq-item reveal reveal-delay-1" onclick="toggleFaq(this)">
        <div class="faq-q">
          <span class="faq-q-text">¿Qué es el CUFE y dónde lo encuentro?</span>
          <div class="faq-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px"><path d="M12 5v14M5 12h14"/></svg></div>
        </div>
        <div class="faq-a"><div class="faq-a-inner">El CUFE (Código Único de Factura Electrónica) es el identificador único de 96 caracteres hexadecimales que la DIAN asigna a cada factura electrónica válida. Lo encuentras en el archivo XML de tu factura electrónica (campo &lt;cbc:UUID&gt;) o en el PDF que te entregó el proveedor de software de facturación. Sin CUFE no es posible registrar ni ceder la factura en RADIAN.</div></div>
      </div>
      <div class="faq-item reveal reveal-delay-2" onclick="toggleFaq(this)">
        <div class="faq-q">
          <span class="faq-q-text">¿Necesito un certificado digital para ceder facturas?</span>
          <div class="faq-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px"><path d="M12 5v14M5 12h14"/></svg></div>
        </div>
        <div class="faq-a"><div class="faq-a-inner">Sí. Para enviar eventos firmados a RADIAN se requiere un certificado digital emitido por una entidad de certificación autorizada por la DIAN, como Certicámara o Andes SCD. La plataforma realiza la firma XML con SHA-384 usando el certificado que configures. En el ambiente de habilitación (pruebas) puedes usar un certificado de prueba provisto por la DIAN.</div></div>
      </div>
      <div class="faq-item reveal reveal-delay-3" onclick="toggleFaq(this)">
        <div class="faq-q">
          <span class="faq-q-text">¿Qué pasa con la contabilidad después de una cesión?</span>
          <div class="faq-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px"><path d="M12 5v14M5 12h14"/></svg></div>
        </div>
        <div class="faq-a"><div class="faq-a-inner">FinPro Capital genera automáticamente los asientos contables correspondientes usando el PUC colombiano: débito a la cuenta 1305 (Deudores Comerciales — Clientes Nacionales) y crédito a la cuenta 4135 (Ingresos Financieros — Cesión de Cartera). Puedes descargar el Libro Diario, el Estado de Resultados, el análisis de cartera y el Flujo de Caja proyectado en Excel con formato contable profesional.</div></div>
      </div>
      <div class="faq-item reveal reveal-delay-4" onclick="toggleFaq(this)">
        <div class="faq-q">
          <span class="faq-q-text">¿Mis datos están seguros? ¿Dónde se almacenan?</span>
          <div class="faq-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:14px"><path d="M12 5v14M5 12h14"/></svg></div>
        </div>
        <div class="faq-a"><div class="faq-a-inner">La plataforma usa autenticación con JWT almacenado en cookies httpOnly (no accesible por JavaScript, protegido contra XSS), protección CSRF con el patrón double-submit cookie, y rate limiting en los endpoints de autenticación. Los datos se almacenan en Supabase (PostgreSQL) con infraestructura en región sudamericana. Las comunicaciones son siempre por HTTPS.</div></div>
      </div>
    </div>
  </div>
</section>

<!-- ══ CTA BAND ══ -->
<div class="cta-band">
  <h2 class="reveal">¿Listo para ceder tu primera factura?</h2>
  <p class="reveal reveal-delay-1">Regístrate gratis en menos de 2 minutos. Sin tarjeta de crédito. Sin letra pequeña.</p>
  <div class="cta-band-actions reveal reveal-delay-2">
    <a href="/app?register=1" class="btn btn-white btn-lg">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:16px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
      Crear cuenta gratis
    </a>
    <a href="mailto:demo@finprocapital.co" class="btn btn-outline-white btn-lg">Solicitar demo personalizada</a>
  </div>
</div>

<!-- ══ FOOTER ══ -->
<footer>
  <div class="footer-inner">
    <div class="footer-top">
      <div>
        <div class="footer-brand">FINPRO<em>CAPITAL</em></div>
        <div class="footer-tagline">Plataforma colombiana de cesión de facturas electrónicas RADIAN. Automatizamos el proceso completo: registro, habilitación y cesión ante la DIAN.</div>
        <div class="footer-social">
          <a href="#" class="social-btn" aria-label="LinkedIn">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/></svg>
          </a>
          <a href="#" class="social-btn" aria-label="GitHub">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width:14px"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 00-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0020 4.77 5.07 5.07 0 0019.91 1S18.73.65 16 2.48a13.38 13.38 0 00-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 005 4.77a5.44 5.44 0 00-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 009 18.13V22"/></svg>
          </a>
          <a href="mailto:contacto@finprocapital.co" class="social-btn" aria-label="Email">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          </a>
        </div>
      </div>
      <div class="footer-col">
        <h4>Producto</h4>
        <ul>
          <li><a href="#caracteristicas">Características</a></li>
          <li><a href="#precios">Precios</a></li>
          <li><a href="/openapi.json" target="_blank">API Docs</a></li>
          <li><a href="#faq">FAQ</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Legal</h4>
        <ul>
          <li><a href="#">Términos de uso</a></li>
          <li><a href="#">Política de privacidad</a></li>
          <li><a href="#">Tratamiento de datos</a></li>
          <li><a href="#">Seguridad</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Soporte</h4>
        <ul>
          <li><a href="mailto:soporte@finprocapital.co">soporte@finprocapital.co</a></li>
          <li><a href="mailto:ventas@finprocapital.co">ventas@finprocapital.co</a></li>
          <li><a href="#">Centro de ayuda</a></li>
          <li><a href="#">Estado del sistema</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="footer-legal">© 2026 FinPro Capital SAS · NIT 900.203.321-8 · Bogotá, Colombia</div>
      <div class="footer-badges">
        <span class="f-badge">DIAN</span>
        <span class="f-badge">RADIAN</span>
        <span class="f-badge">UBL 2.1</span>
        <span class="f-badge">SHA-384</span>
      </div>
    </div>
  </div>
</footer>

<!-- ══ MODAL DEMO ══ -->
<div class="modal-overlay" id="demo-modal" onclick="if(event.target===this)closeDemo()">
  <div class="modal-box">
    <div class="modal-header">
      <span class="modal-header-title">Demo — FinPro Capital RADIAN</span>
      <button class="modal-x" onclick="closeDemo()">✕</button>
    </div>
    <div class="modal-video">
      <div class="modal-video-badge">PRÓXIMAMENTE</div>
      <div class="play-btn">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 3l14 9-14 9V3z"/></svg>
      </div>
      <div class="modal-video-text">Video demo del proceso completo de cesión</div>
    </div>
    <div class="modal-body">
      <p style="font-size:13px;color:var(--text2);margin-bottom:16px">Mientras tanto, puedes explorar la plataforma directamente o solicitar una demo en vivo con nuestro equipo.</p>
      <div class="demo-steps">
        <div class="demo-step"><div class="demo-step-num">1</div><div class="demo-step-label">Registra la factura con su CUFE</div></div>
        <div class="demo-step"><div class="demo-step-num">2</div><div class="demo-step-label">Habilítala como título valor</div></div>
        <div class="demo-step"><div class="demo-step-num">3</div><div class="demo-step-label">Cede el crédito ante la DIAN</div></div>
      </div>
      <div style="display:flex;gap:10px;margin-top:20px">
        <a href="/app?register=1" class="btn btn-primary" style="flex:1;justify-content:center">Probar ahora gratis</a>
        <a href="mailto:demo@finprocapital.co" class="btn btn-ghost" style="flex:1;justify-content:center">Solicitar demo</a>
      </div>
    </div>
  </div>
</div>

<script>
// ── NAVBAR SCROLL ──
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 20);
}, {passive: true});

// ── MOBILE MENU ──
function toggleMenu() { document.getElementById('mobile-menu').classList.toggle('open'); }
function closeMenu()  { document.getElementById('mobile-menu').classList.remove('open'); }

// ── DEMO MODAL ──
function openDemo()  { document.getElementById('demo-modal').classList.add('show'); document.body.style.overflow='hidden'; }
function closeDemo() { document.getElementById('demo-modal').classList.remove('show'); document.body.style.overflow=''; }
document.addEventListener('keydown', e => { if(e.key==='Escape') closeDemo(); });

// ── HOW IT WORKS STEPS ──
function setStep(n) {
  document.querySelectorAll('.step-item').forEach((el,i) => el.classList.toggle('active', i===n));
  [0,1,2].forEach(i => {
    document.getElementById('sv-'+i).style.display = i===n ? '' : 'none';
    const dot = document.getElementById('dot-'+i);
    dot.innerHTML = i===n ? '<div style="height:100%;border-radius:99px;background:var(--teal);width:100%"></div>' : '';
  });
}
// Auto-advance steps
let stepIdx = 0;
setInterval(() => { stepIdx = (stepIdx+1)%3; setStep(stepIdx); }, 3500);

// ── FAQ ──
function toggleFaq(el) {
  const isOpen = el.classList.contains('open');
  document.querySelectorAll('.faq-item').forEach(f => f.classList.remove('open'));
  if(!isOpen) el.classList.add('open');
}

// ── SCROLL REVEAL (Intersection Observer) ──
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if(e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); } });
}, {threshold: 0.12, rootMargin: '0px 0px -40px 0px'});
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// ── SMOOTH SCROLL FOR ANCHOR LINKS ──
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if(target) { e.preventDefault(); target.scrollIntoView({behavior:'smooth', block:'start'}); closeMenu(); }
  });
});
</script>
</body>
</html>"""

@app.get("/", include_in_schema=False)
async def landing():
    return HTMLResponse(LANDING)

@app.get("/app", include_in_schema=False)
async def app_ui():
    return HTMLResponse(UI)

@app.get("/health", tags=["Health"])
async def health():
    return {"sistema": "RADIAN API", "version": "1.0.0", "estado": "activo"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
