from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from routers import facturas, cesion, autenticacion, consultas
from config import settings

app = FastAPI(title="RADIAN API", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(autenticacion.router, prefix="/api/v1/auth",     tags=["Autenticacion"])
app.include_router(facturas.router,      prefix="/api/v1/facturas",  tags=["Facturas"])
app.include_router(cesion.router,        prefix="/api/v1/cesion",    tags=["Cesion RADIAN"])
app.include_router(consultas.router,     prefix="/api/v1/consultas", tags=["Consultas DIAN"])

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

/* ─── RESPONSIVE ─── */
@media(max-width:900px){
  .auth-left{display:none}
  .auth-right{width:100%}
  .stats-grid{grid-template-columns:1fr 1fr}
  .grid-2,.grid-2-eq{grid-template-columns:1fr}
  .form-row,.form-row-3{grid-template-columns:1fr}
  .aging-grid{grid-template-columns:1fr 1fr}
  .kpi-grid{grid-template-columns:1fr 1fr}
}
@media(max-width:640px){
  .stats-grid{grid-template-columns:1fr}
  .sidebar{transform:translateX(-100%)}
  .sidebar.open{transform:translateX(0)}
  .main{margin-left:0}
  .content{padding:16px}
  .topbar{padding:0 16px}
  .aging-grid{grid-template-columns:1fr}
  .kpi-grid{grid-template-columns:1fr}
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
  <div class="topbar">
    <div class="topbar-left">
      <div class="page-title" id="page-title">Dashboard</div>
      <div class="page-subtitle" id="page-sub">Resumen general</div>
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
        <table class="tbl">
          <thead><tr><th>Número / CUFE</th><th>Adquiriente</th><th>Valor Total</th><th>Vencimiento</th><th>Estado</th><th style="text-align:center">Acciones</th></tr></thead>
          <tbody id="facturas-body"><tr><td colspan="6"><div class="empty-state" style="padding:32px"><div class="empty-text">Cargando facturas...</div></div></td></tr></tbody>
        </table>
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
            <div class="fg"><label>CUFE <span style="color:var(--red)">*</span></label><input id="reg-cufe" placeholder="Código Único de Factura Electrónica (96 chars)"/></div>
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
            <div class="fg"><label>CUFE de la factura <span style="color:var(--red)">*</span></label><input id="f-cufe" placeholder="Código único de la factura electrónica"/><div class="hint">La factura debe estar habilitada como título valor</div></div>
            <div class="divider"></div>
            <div class="section-label">Cesionario (quien recibe)</div>
            <div class="form-row">
              <div class="fg"><label>NIT Cesionario <span style="color:var(--red)">*</span></label><input id="f-nit-ces" placeholder="900.123.456-1"/></div>
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
        <table class="tbl">
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
let TOKEN = sessionStorage.getItem('radian_token') || '';
let USER_DATA = JSON.parse(sessionStorage.getItem('radian_user') || 'null');

// ── INIT ──
window.onload = () => { if(TOKEN) showApp(); };

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
    const r = await fetch(API+'/api/v1/auth/token', {method:'POST', body:fd});
    const d = await r.json();
    if(!r.ok){ showErr(errEl, errTxt, d.detail||'Credenciales incorrectas'); return; }
    TOKEN = d.access_token;
    sessionStorage.setItem('radian_token', TOKEN);
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
    const r=await fetch(API+'/api/v1/auth/registro',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,nombre,nit,telefono:tel||null,password:pass})});
    const d=await r.json();
    if(!r.ok){ showErr(errEl, errTxt, d.detail||'Error al registrar'); return; }
    toast('Cuenta creada. Ahora inicia sesión.', 'ok');
    showPanel('login');
    document.getElementById('l-email').value=email;
  }catch(e){ showErr(errEl, errTxt, 'Error de conexión'); }
  finally{ btn.textContent='Crear cuenta'; btn.disabled=false; }
}

function doLogout() {
  TOKEN=''; USER_DATA=null;
  sessionStorage.removeItem('radian_token');
  sessionStorage.removeItem('radian_user');
  document.getElementById('app-screen').style.display='none';
  document.getElementById('auth-screen').style.display='flex';
}

function showErr(el, txtEl, msg){ if(txtEl) txtEl.textContent=msg; el.classList.add('show'); }

// ── APP ──
function showApp() {
  document.getElementById('auth-screen').style.display='none';
  document.getElementById('app-screen').style.display='block';
  loadDashboard();
}

function authH(){ return {'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'}; }

async function loadUserInfo() {
  try {
    const r=await fetch(API+'/api/v1/auth/me',{headers:authH()});
    if(r.ok){ const d=await r.json(); USER_DATA=d; sessionStorage.setItem('radian_user',JSON.stringify(d)); }
  }catch(e){}
  if(USER_DATA){
    const n=USER_DATA.nombre||USER_DATA.email;
    document.getElementById('user-name').textContent=n;
    document.getElementById('user-nit').textContent='NIT '+USER_DATA.nit;
    document.getElementById('user-avatar').textContent=n.substring(0,2).toUpperCase();
  }
}

async function loadDashboard() {
  loadUserInfo();
  checkApiStatus();
  // Load cesiones KPIs for dashboard
  fetch(API+'/api/v1/cesion/?limit=500',{headers:authH()}).then(r=>r.json()).then(d=>{
    const ces=(d.cesiones||[]).filter(c=>c.estado==='ACEPTADA');
    const tot=ces.reduce((s,c)=>s+(c.valor_cesion||0),0);
    const el=document.getElementById('dash-ces-total');
    if(el) el.textContent='$'+fmtNum(tot)+' en '+ces.length+' cesión'+(ces.length!==1?'es':'');
  }).catch(()=>{});
  try {
    const r=await fetch(API+'/api/v1/facturas/?limit=100',{headers:authH()});
    if(r.status===401){ doLogout(); return; }
    if(!r.ok) throw new Error();
    const d=await r.json();
    const fs=d.facturas||[];
    document.getElementById('st-total').textContent=d.total||0;
    document.getElementById('st-cedidas').textContent=fs.filter(f=>f.estado==='CEDIDA').length;
    document.getElementById('st-titulos').textContent=fs.filter(f=>f.es_titulo_valor&&f.estado!=='CEDIDA').length;
    document.getElementById('st-proceso').textContent=fs.filter(f=>f.estado==='EN_CESION').length;
    const tbody=document.getElementById('dash-facturas');
    if(!fs.length){
      tbody.innerHTML='<tr><td colspan="4"><div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">No hay facturas registradas</div><div class="empty-sub">Comienza registrando tu primera factura electrónica</div></div></td></tr>';
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
    const url=API+'/api/v1/facturas/?limit=100'+(estado?'&estado='+estado:'');
    const r=await fetch(url,{headers:authH()});
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
        <td><div class="td-primary">${f.prefijo||'FV'}-${f.numero}</div><div class="td-mono">${(f.cufe||'').substring(0,22)}…</div></td>
        <td style="font-size:12px">${f.adquiriente_nombre||'—'}<div class="td-mono">${f.adquiriente_nit||''}</div></td>
        <td><div class="td-amount">$${fmtNum(f.valor_total)}</div></td>
        <td style="font-size:12px;color:var(--text-muted)">${fmtDate(f.fecha_vencimiento)}</td>
        <td>${badgeEstado(f.estado)}</td>
        <td style="text-align:center">
          <div style="display:flex;gap:6px;justify-content:center">
            <button class="btn btn-ghost btn-sm" onclick="verDetalle('${f.cufe}')">Ver</button>
            ${f.es_titulo_valor&&f.estado!=='CEDIDA'?`<button class="btn btn-primary btn-sm" onclick="irCeder('${f.cufe}')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:11px"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              Ceder</button>`:''}
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
    const r=await fetch(API+'/api/v1/facturas/'+cufe,{headers:authH()});
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
    const r=await fetch(API+'/api/v1/facturas/'+cufe+'/habilitar-cesion',{method:'PUT',headers:authH()});
    const d=await r.json();
    if(r.ok){ toast('Factura habilitada como título valor','ok'); loadFacturas(); closeModal('modal-detalle'); }
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
    const r=await fetch(API+'/api/v1/facturas/registrar',{method:'POST',headers:authH(),body:JSON.stringify(body)});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok){
      box.innerHTML='<div class="resp-ok">✅ '+d.mensaje+'</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>';
      toast('Factura registrada exitosamente','ok');
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
    const r=await fetch(API+'/api/v1/facturas/'+cufe+'/habilitar-cesion',{method:'PUT',headers:authH()});
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
    const r=await fetch(API+'/api/v1/cesion/crear',{method:'POST',headers:authH(),body:JSON.stringify({cufe_factura:cufe,cesionario_nit:nit,cesionario_nombre:nombre,valor_cesion:valor})});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok){
      box.innerHTML='<div class="resp-ok">✅ '+d.mensaje+'</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>';
      toast('Cesión registrada en RADIAN','ok');
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
    const r=await fetch(API+'/api/v1/cesion/'+cude+'/estado',{headers:authH()});
    const d=await r.json();
    box.innerHTML=r.ok?'<div class="resp-ok">✅ Respuesta DIAN</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>':'<div class="resp-err">❌ '+(d.detail||JSON.stringify(d))+'</div>';
  }catch(e){ box.innerHTML='<div class="resp-err">❌ Error de conexión</div>'; }
}

async function pingDian() {
  const box=document.getElementById('resp-ping');
  box.className='resp-box show'; box.innerHTML='<div style="color:#9CA3AF">Verificando conexión DIAN...</div>';
  try {
    const r=await fetch(API+'/api/v1/consultas/ping-dian',{headers:authH()});
    const d=await r.json();
    box.innerHTML=r.ok?'<div class="resp-ok">✅ Conexión exitosa</div><div class="resp-data">'+JSON.stringify(d,null,2)+'</div>':'<div class="resp-err">❌ '+JSON.stringify(d)+'</div>';
  }catch(e){ box.innerHTML='<div class="resp-err">❌ No se pudo conectar a DIAN</div>'; }
}

async function probarEndpoint() {
  const ep=document.getElementById('ep-sel').value;
  const box=document.getElementById('resp-api');
  box.innerHTML='<div style="color:#9CA3AF">Ejecutando...</div>';
  try {
    const hdrs=ep.startsWith('/api')?authH():{};
    const r=await fetch(API+ep,{headers:hdrs});
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
    const r = await fetch(API+'/api/v1/cesion/?limit=200', {headers:authH()});
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
    tbody.innerHTML='<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">📋</div><div class="empty-text">No hay cesiones registradas</div><div class="empty-sub"><a style="color:var(--brand);cursor:pointer" onclick="showPage(\'cesion\')">Crear primera cesión</a></div></div></td></tr>';
    return;
  }
  tbody.innerHTML = ces.map(c => `
    <tr>
      <td><div class="td-primary" style="font-size:12px">${c.numero_cesion||'—'}</div><div class="td-mono">${(c.cude||'').substring(0,14)}…</div></td>
      <td><div class="td-mono">${(c.cufe_factura||'').substring(0,16)}…</div></td>
      <td style="font-size:12px">${c.cedente_nombre||'—'}<div class="td-mono">${c.cedente_nit||''}</div></td>
      <td style="font-size:12px">${c.cesionario_nombre||'—'}<div class="td-mono">${c.cesionario_nit||''}</div></td>
      <td><div class="td-amount">$${fmtNum(c.valor_cesion)}</div></td>
      <td style="font-size:12px;color:var(--text-muted)">${fmtDate(c.fecha_cesion)}</td>
      <td>${badgeCesion(c.estado)}</td>
      <td style="text-align:center"><button class="btn btn-ghost btn-sm" onclick="descargarXml('${c.cude}')">
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
function badgeCesion(e) {
  const m = {'ACEPTADA':'b-green','RECHAZADA':'b-red','PENDIENTE':'b-gold'};
  return `<span class="badge ${m[e]||'b-gray'}">${e||'—'}</span>`;
}

// ── CARTERA ──
async function loadCartera() {
  try {
    const r = await fetch(API+'/api/v1/facturas/?limit=200', {headers:authH()});
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
    const r = await fetch(API+'/api/v1/facturas/?limit=200', {headers:authH()});
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
    const r = await fetch(API+'/api/v1/cesion/?limit=500', {headers:authH()});
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
    const r = await fetch(API+'/api/v1/cesion/?limit=500', {headers:authH()});
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

function showPage(p) {
  document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(e=>e.classList.remove('active'));
  const el=document.getElementById('page-'+p); if(el) el.classList.add('active');
  const nav=document.getElementById('nav-'+p); if(nav) nav.classList.add('active');
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

@app.get("/", include_in_schema=False)
async def ui():
    return HTMLResponse(UI)

@app.get("/health", tags=["Health"])
async def health():
    return {"sistema": "RADIAN API", "version": "1.0.0", "estado": "activo"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
