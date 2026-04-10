from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from routers import facturas, cesion, autenticacion, consultas
from config import settings
from database import engine, Base

Base.metadata.create_all(bind=engine)

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
<title>RadianAPI</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F0F2F5;color:#1a1a2e;min-height:100vh;display:flex}

/* SIDEBAR */
.sidebar{width:240px;background:#0A1628;display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0}
.logo{padding:20px;border-bottom:1px solid rgba(255,255,255,0.07)}
.logo-text{font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.5px}
.logo-text em{font-style:normal;color:#00C2FF}
.logo-sub{font-size:10px;color:rgba(255,255,255,0.3);margin-top:2px;letter-spacing:1px;text-transform:uppercase}
.env-badge{margin:12px;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:8px 12px;display:flex;align-items:center;gap:8px}
.env-dot{width:7px;height:7px;border-radius:50%;background:#10B981;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
.env-text{font-size:11px;color:#10B981;font-weight:600}
.nav-section{padding:16px 12px 6px;font-size:10px;color:rgba(255,255,255,0.25);text-transform:uppercase;letter-spacing:2px}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 14px;border-radius:8px;margin:2px 8px;cursor:pointer;font-size:13px;font-weight:500;color:rgba(255,255,255,0.5);transition:.15s;border:1px solid transparent;text-decoration:none}
.nav-item:hover{background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.85)}
.nav-item.active{background:rgba(0,194,255,0.1);border-color:rgba(0,194,255,0.2);color:#fff}
.nav-icon{width:16px;text-align:center;font-size:14px}
.nav-badge{margin-left:auto;background:#00C2FF;color:#000;font-size:9px;font-weight:800;padding:1px 7px;border-radius:10px}
.sidebar-bottom{margin-top:auto;padding:16px;border-top:1px solid rgba(255,255,255,0.07)}
.user-row{display:flex;align-items:center;gap:10px}
.avatar{width:34px;height:34px;background:#1347CC;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0}
.user-name{font-size:13px;font-weight:600;color:rgba(255,255,255,0.85)}
.user-plan{font-size:10px;color:rgba(255,255,255,0.3);margin-top:1px}

/* MAIN */
.main{margin-left:240px;flex:1;display:flex;flex-direction:column;min-height:100vh}
.topbar{background:#fff;border-bottom:1px solid #E2E8F0;padding:0 28px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}
.page-h{font-size:17px;font-weight:700;letter-spacing:-0.3px}
.page-sub{font-size:12px;color:#64748B;margin-top:1px}
.topbar-actions{display:flex;gap:10px}
.btn{padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:none;font-family:inherit;transition:.15s}
.btn-ghost{background:none;border:1px solid #E2E8F0;color:#374151}
.btn-ghost:hover{border-color:#1347CC;color:#1347CC}
.btn-primary{background:#1347CC;color:#fff}
.btn-primary:hover{background:#0f3ba8}
.btn-green{background:#10B981;color:#fff}
.btn-green:hover{background:#059669}

/* CONTENT */
.content{padding:24px 28px;flex:1}

/* STATS */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:20px;position:relative;overflow:hidden}
.stat::after{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.stat.s1::after{background:#00C2FF}
.stat.s2::after{background:#10B981}
.stat.s3::after{background:#F59E0B}
.stat.s4::after{background:#7C3AED}
.stat-label{font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600}
.stat-val{font-size:30px;font-weight:800;color:#0F172A;line-height:1;letter-spacing:-1px}
.stat-change{font-size:11px;margin-top:6px;color:#10B981;font-weight:600}

/* GRID */
.grid{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;margin-bottom:20px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}

/* CARD */
.card{background:#fff;border:1px solid #E2E8F0;border-radius:12px;overflow:hidden}
.card-head{padding:16px 20px;border-bottom:1px solid #F1F5F9;display:flex;align-items:center;justify-content:space-between}
.card-title{font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px}
.card-link{font-size:12px;color:#1347CC;font-weight:600;cursor:pointer;text-decoration:none}
.card-body{padding:20px}

/* TABLE */
.tbl{width:100%;border-collapse:collapse}
.tbl th{padding:8px 14px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#64748B;border-bottom:2px solid #F1F5F9;font-weight:700}
.tbl td{padding:11px 14px;font-size:13px;border-bottom:1px solid #F8FAFC;vertical-align:middle}
.tbl tr:last-child td{border-bottom:none}
.tbl tr:hover td{background:#FAFBFC}
.td-main{font-weight:600;color:#0F172A;margin-bottom:2px}
.td-sub{font-size:11px;color:#94A3B8;font-family:monospace}
.td-val{font-weight:700;color:#0F172A;font-family:monospace}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:10px;font-weight:700;letter-spacing:0.3px}
.badge::before{content:'';width:5px;height:5px;border-radius:50%;background:currentColor}
.b-green{background:#ECFDF5;color:#059669}
.b-blue{background:#EFF6FF;color:#1347CC}
.b-gold{background:#FFFBEB;color:#D97706}
.b-red{background:#FEF2F2;color:#DC2626}
.b-purple{background:#F5F3FF;color:#7C3AED}
.act-btn{background:none;border:1px solid #E2E8F0;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;font-family:inherit;color:#374151;font-weight:600;transition:.15s}
.act-btn:hover{border-color:#1347CC;color:#1347CC}
.act-btn.pri{background:#1347CC;color:#fff;border-color:#1347CC}

/* FORM */
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.fg{display:flex;flex-direction:column;gap:5px;margin-bottom:12px}
.fg label{font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px}
.fg input,.fg select{padding:9px 12px;border:1.5px solid #E2E8F0;border-radius:8px;font-size:13px;font-family:inherit;color:#0F172A;background:#F8FAFC;outline:none;transition:.15s}
.fg input:focus,.fg select:focus{border-color:#1347CC;background:#fff;box-shadow:0 0 0 3px rgba(19,71,204,0.08)}
.fg input::placeholder{color:#94A3B8}
.submit-btn{width:100%;padding:12px;background:linear-gradient(135deg,#1347CC,#0891B2);color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;display:flex;align-items:center;justify-content:center;gap:8px;transition:.15s;margin-top:4px}
.submit-btn:hover{opacity:.9;transform:translateY(-1px)}

/* CHART */
.chart-bars{display:flex;align-items:flex-end;gap:6px;height:72px;padding:0 4px}
.bar-wrap{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}
.bar-fill{width:100%;border-radius:4px 4px 0 0;background:#1347CC;opacity:.25;transition:.2s;cursor:pointer;min-height:4px}
.bar-fill.active{opacity:1;background:#00C2FF}
.bar-fill:hover{opacity:.7}
.bar-lbl{font-size:9px;color:#94A3B8;font-weight:600}

/* LOG */
.log-item{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #F8FAFC}
.log-item:last-child{border:none}
.log-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.li-green{background:#ECFDF5}
.li-blue{background:#EFF6FF}
.li-gold{background:#FFFBEB}
.log-title{font-size:13px;font-weight:600;color:#0F172A;margin-bottom:2px}
.log-desc{font-size:11px;color:#64748B}
.log-time{font-size:10px;color:#94A3B8;margin-top:2px;font-family:monospace}

/* API KEYS */
.key-row{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.key-label{font-size:12px;font-weight:700;color:#0F172A;margin-bottom:2px}
.key-val{font-size:11px;color:#64748B;font-family:monospace}

/* ENDPOINT LIST */
.ep-item{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #F8FAFC;font-size:12px}
.ep-item:last-child{border:none}
.method{padding:3px 8px;border-radius:5px;font-size:10px;font-weight:800;min-width:46px;text-align:center;font-family:monospace}
.m-post{background:#ECFDF5;color:#059669}
.m-get{background:#EFF6FF;color:#1347CC}
.m-put{background:#FFFBEB;color:#D97706}
.ep-path{font-family:monospace;font-size:12px;color:#374151;flex:1}
.ep-desc{font-size:11px;color:#94A3B8}

/* TABS */
.tabs{display:flex;gap:0;border-bottom:2px solid #F1F5F9;margin-bottom:20px}
.tab{padding:10px 18px;font-size:13px;font-weight:600;cursor:pointer;color:#64748B;border-bottom:2px solid transparent;margin-bottom:-2px;transition:.15s}
.tab.active{color:#1347CC;border-bottom-color:#1347CC}
.tab-content{display:none}
.tab-content.active{display:block}

/* RESP BOX */
.resp-box{background:#0D1117;border-radius:8px;padding:16px;font-family:monospace;font-size:12px;line-height:1.7;margin-top:14px;display:none}
.resp-box.show{display:block}
.r-ok{color:#10B981;font-weight:700;font-size:13px;margin-bottom:6px}
.r-key{color:#6B7280}
.r-val{color:#00C2FF}
.r-err{color:#EF4444;font-weight:700}

/* MISC */
.section-title{font-size:16px;font-weight:700;margin-bottom:16px;letter-spacing:-0.3px}
.empty{text-align:center;padding:32px;color:#94A3B8;font-size:13px}
.spinner{display:none;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>

<!-- SIDEBAR -->
<nav class="sidebar">
  <div class="logo">
    <div class="logo-text">Radian<em>API</em></div>
    <div class="logo-sub">v1.0.0 &nbsp;·&nbsp; Colombia</div>
  </div>
  <div class="env-badge"><div class="env-dot"></div><span class="env-text">DIAN Habilitación Activa</span></div>

  <div class="nav-section">Principal</div>
  <a class="nav-item active" onclick="showPage('dashboard')"><span class="nav-icon">📊</span> Dashboard</a>
  <a class="nav-item" onclick="showPage('facturas')"><span class="nav-icon">📋</span> Facturas <span class="nav-badge">47</span></a>
  <a class="nav-item" onclick="showPage('cesion')"><span class="nav-icon">⚡</span> Nueva Cesión</a>
  <a class="nav-item" onclick="showPage('api')"><span class="nav-icon">🔌</span> API Explorer</a>

  <div class="nav-section">Sistema</div>
  <a class="nav-item" onclick="showPage('keys')"><span class="nav-icon">🔑</span> API Keys</a>
  <a class="nav-item" href="/openapi.json" target="_blank"><span class="nav-icon">📖</span> OpenAPI JSON</a>

  <div class="sidebar-bottom">
    <div class="user-row">
      <div class="avatar">LM</div>
      <div><div class="user-name">Luis Mig</div><div class="user-plan">Plan Profesional</div></div>
    </div>
  </div>
</nav>

<!-- MAIN -->
<div class="main">

  <!-- TOPBAR -->
  <div class="topbar">
    <div><div class="page-h" id="page-title">Dashboard</div><div class="page-sub" id="page-sub">Resumen general · NIT 900.000.000-0</div></div>
    <div class="topbar-actions">
      <button class="btn btn-ghost" onclick="showPage('api')">🔌 API Explorer</button>
      <button class="btn btn-primary" onclick="showPage('cesion')">⚡ Nueva Cesión</button>
    </div>
  </div>

  <!-- CONTENT -->
  <div class="content">

    <!-- ═══ DASHBOARD ═══ -->
    <div id="page-dashboard" class="tab-content active">
      <div class="stats">
        <div class="stat s1"><div class="stat-label">Facturas</div><div class="stat-val">47</div><div class="stat-change">↑ 12 este mes</div></div>
        <div class="stat s2"><div class="stat-label">Cedidas</div><div class="stat-val">23</div><div class="stat-change">↑ 8 este mes</div></div>
        <div class="stat s3"><div class="stat-label">Valor COP</div><div class="stat-val">$890M</div><div class="stat-change">↑ $210M vs ant.</div></div>
        <div class="stat s4"><div class="stat-label">Tasa DIAN</div><div class="stat-val">96.8%</div><div class="stat-change">↑ 2.1% vs ant.</div></div>
      </div>

      <div class="grid">
        <!-- TABLA -->
        <div class="card">
          <div class="card-head"><div class="card-title">⚡ Últimas Cesiones</div><a class="card-link" onclick="showPage('facturas')">Ver todas →</a></div>
          <div class="card-body" style="padding:0">
            <table class="tbl">
              <thead><tr><th>Factura</th><th>Cesionario</th><th>Valor</th><th>Estado</th><th></th></tr></thead>
              <tbody>
                <tr><td><div class="td-main">FV-2024-001234</div><div class="td-sub">abc123...sha384</div></td><td>Banco Ejemplo SAS</td><td class="td-val">$120M</td><td><span class="badge b-green">CEDIDA</span></td><td><button class="act-btn">XML</button></td></tr>
                <tr><td><div class="td-main">FV-2024-001235</div><div class="td-sub">def456...sha384</div></td><td>Fintech Rápida SAS</td><td class="td-val">$75.5M</td><td><span class="badge b-green">CEDIDA</span></td><td><button class="act-btn">XML</button></td></tr>
                <tr><td><div class="td-main">FV-2024-001236</div><div class="td-sub">ghi789...sha384</div></td><td>Factor Capital SAS</td><td class="td-val">$200M</td><td><span class="badge b-gold">EN PROCESO</span></td><td><button class="act-btn">Ver</button></td></tr>
                <tr><td><div class="td-main">FV-2024-001237</div><div class="td-sub">jkl012...sha384</div></td><td>Inversiones Sur SAS</td><td class="td-val">$45M</td><td><span class="badge b-blue">TÍTULO VALOR</span></td><td><button class="act-btn pri" onclick="showPage('cesion')">Ceder</button></td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- RIGHT COL -->
        <div style="display:flex;flex-direction:column;gap:16px">
          <!-- CHART -->
          <div class="card">
            <div class="card-head"><div class="card-title">📈 Cesiones / mes</div><span style="font-size:11px;color:#94A3B8">2024</span></div>
            <div class="card-body">
              <div class="chart-bars">
                <div class="bar-wrap"><div class="bar-fill" style="height:30%"></div><div class="bar-lbl">Ene</div></div>
                <div class="bar-wrap"><div class="bar-fill" style="height:45%"></div><div class="bar-lbl">Feb</div></div>
                <div class="bar-wrap"><div class="bar-fill" style="height:35%"></div><div class="bar-lbl">Mar</div></div>
                <div class="bar-wrap"><div class="bar-fill" style="height:60%"></div><div class="bar-lbl">Abr</div></div>
                <div class="bar-wrap"><div class="bar-fill" style="height:50%"></div><div class="bar-lbl">May</div></div>
                <div class="bar-wrap"><div class="bar-fill" style="height:70%"></div><div class="bar-lbl">Jun</div></div>
                <div class="bar-wrap"><div class="bar-fill active" style="height:100%"></div><div class="bar-lbl">Jul</div></div>
              </div>
            </div>
          </div>
          <!-- LOG -->
          <div class="card">
            <div class="card-head"><div class="card-title">📋 Log RADIAN</div><a class="card-link">Ver todo</a></div>
            <div class="card-body" style="padding:12px 20px">
              <div class="log-item"><div class="log-icon li-green">✅</div><div><div class="log-title">Cesión aceptada DIAN</div><div class="log-desc">FV-001234 · Evento 037</div><div class="log-time">Hace 5 min</div></div></div>
              <div class="log-item"><div class="log-icon li-blue">📤</div><div><div class="log-title">XML firmado y enviado</div><div class="log-desc">FV-001236 · $200M COP</div><div class="log-time">Hace 12 min</div></div></div>
              <div class="log-item"><div class="log-icon li-gold">🔔</div><div><div class="log-title">Webhook disparado</div><div class="log-desc">200 OK · tu-app.co/webhooks</div><div class="log-time">Hace 13 min</div></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ FACTURAS ═══ -->
    <div id="page-facturas" class="tab-content">
      <div class="card">
        <div class="card-head"><div class="card-title">📋 Todas las Facturas</div><button class="btn btn-primary" style="font-size:12px;padding:6px 14px">+ Registrar factura</button></div>
        <div class="card-body" style="padding:0">
          <table class="tbl">
            <thead><tr><th>Número</th><th>Emisor</th><th>Adquiriente</th><th>Valor Total</th><th>Vence</th><th>Estado</th><th>Acción</th></tr></thead>
            <tbody>
              <tr><td><div class="td-main">FV-2024-001234</div><div class="td-sub">CUFE: abc123...384</div></td><td>Mi Empresa SAS</td><td>Banco Ejemplo SAS</td><td class="td-val">$120M</td><td style="font-size:12px;color:#64748B">30/08/2024</td><td><span class="badge b-green">CEDIDA</span></td><td><button class="act-btn">Ver XML</button></td></tr>
              <tr><td><div class="td-main">FV-2024-001235</div><div class="td-sub">CUFE: def456...384</div></td><td>Mi Empresa SAS</td><td>Fintech Rápida SAS</td><td class="td-val">$75.5M</td><td style="font-size:12px;color:#64748B">15/09/2024</td><td><span class="badge b-green">CEDIDA</span></td><td><button class="act-btn">Ver XML</button></td></tr>
              <tr><td><div class="td-main">FV-2024-001236</div><div class="td-sub">CUFE: ghi789...384</div></td><td>Mi Empresa SAS</td><td>Factor Capital SAS</td><td class="td-val">$200M</td><td style="font-size:12px;color:#64748B">01/10/2024</td><td><span class="badge b-gold">EN PROCESO</span></td><td><button class="act-btn">Ver estado</button></td></tr>
              <tr><td><div class="td-main">FV-2024-001237</div><div class="td-sub">CUFE: jkl012...384</div></td><td>Mi Empresa SAS</td><td>Inversiones Sur SAS</td><td class="td-val">$45M</td><td style="font-size:12px;color:#64748B">20/10/2024</td><td><span class="badge b-blue">TÍTULO VALOR</span></td><td><button class="act-btn pri" onclick="showPage('cesion')">⚡ Ceder</button></td></tr>
              <tr><td><div class="td-main">FV-2024-001238</div><div class="td-sub">CUFE: mno345...384</div></td><td>Mi Empresa SAS</td><td>—</td><td class="td-val">$90M</td><td style="font-size:12px;color:#64748B">05/11/2024</td><td><span class="badge b-red">RECHAZADA</span></td><td><button class="act-btn">Reintentar</button></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══ NUEVA CESIÓN ═══ -->
    <div id="page-cesion" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-head"><div class="card-title">⚡ Nueva Cesión RADIAN — Evento 037</div></div>
          <div class="card-body">
            <div class="fg"><label>CUFE de la Factura</label><input id="f-cufe" placeholder="abc123def456...sha384hash" /></div>
            <div class="form-row">
              <div class="fg"><label>NIT Cesionario</label><input id="f-nit" placeholder="900.123.456-1" /></div>
              <div class="fg"><label>Nombre Cesionario</label><input id="f-nombre" placeholder="BANCO EJEMPLO SAS" /></div>
            </div>
            <div class="fg"><label>Valor a Ceder (COP)</label><input id="f-valor" type="number" placeholder="120000000" /></div>
            <button class="submit-btn" onclick="ceder()">
              <div class="spinner" id="spin"></div>
              <span id="btn-text">⚡ Enviar a DIAN RADIAN</span>
            </button>
            <div class="resp-box" id="resp-box"></div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:16px">
          <div class="card">
            <div class="card-head"><div class="card-title">📋 Proceso de Cesión</div></div>
            <div class="card-body">
              <div style="display:flex;flex-direction:column;gap:12px">
                <div style="display:flex;gap:12px;align-items:flex-start"><div style="width:26px;height:26px;border-radius:50%;background:#1347CC;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0">1</div><div><div style="font-size:13px;font-weight:600">Validar factura</div><div style="font-size:11px;color:#64748B">Verifica que sea título valor</div></div></div>
                <div style="display:flex;gap:12px;align-items:flex-start"><div style="width:26px;height:26px;border-radius:50%;background:#1347CC;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0">2</div><div><div style="font-size:13px;font-weight:600">Construir XML UBL 2.1</div><div style="font-size:11px;color:#64748B">Evento 037 con CUDE SHA-384</div></div></div>
                <div style="display:flex;gap:12px;align-items:flex-start"><div style="width:26px;height:26px;border-radius:50%;background:#1347CC;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0">3</div><div><div style="font-size:13px;font-weight:600">Firmar digitalmente</div><div style="font-size:11px;color:#64748B">Certificado Certicámara</div></div></div>
                <div style="display:flex;gap:12px;align-items:flex-start"><div style="width:26px;height:26px;border-radius:50%;background:#00C2FF;color:#000;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0">4</div><div><div style="font-size:13px;font-weight:600;color:#0EA5E9">Enviar a RADIAN DIAN</div><div style="font-size:11px;color:#64748B">Respuesta en ~1 segundo</div></div></div>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-head"><div class="card-title">🔍 Consultar Estado</div></div>
            <div class="card-body">
              <div class="fg"><label>CUDE del evento</label><input id="f-cude" placeholder="d8f3a1...sha384" /></div>
              <button class="btn btn-ghost" style="width:100%;padding:10px" onclick="consultar()">🔍 Consultar en DIAN</button>
              <div class="resp-box" id="resp-consulta"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ API EXPLORER ═══ -->
    <div id="page-api" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-head"><div class="card-title">🔌 Endpoints disponibles</div></div>
          <div class="card-body">
            <div class="ep-item"><span class="method m-post">POST</span><div><div class="ep-path">/api/v1/auth/registro</div><div class="ep-desc">Registrar nueva empresa</div></div></div>
            <div class="ep-item"><span class="method m-post">POST</span><div><div class="ep-path">/api/v1/auth/token</div><div class="ep-desc">Obtener token JWT</div></div></div>
            <div class="ep-item"><span class="method m-post">POST</span><div><div class="ep-path">/api/v1/facturas/registrar</div><div class="ep-desc">Registrar factura electrónica</div></div></div>
            <div class="ep-item"><span class="method m-put">PUT</span><div><div class="ep-path">/api/v1/facturas/{cufe}/habilitar-cesion</div><div class="ep-desc">Habilitar como título valor</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/api/v1/facturas/{cufe}</div><div class="ep-desc">Consultar factura</div></div></div>
            <div class="ep-item"><span class="method m-post">POST</span><div><div class="ep-path">/api/v1/cesion/crear</div><div class="ep-desc">⚡ Ceder factura en RADIAN</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/api/v1/cesion/{cude}/estado</div><div class="ep-desc">Estado en DIAN</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/api/v1/consultas/ping-dian</div><div class="ep-desc">Verificar conexión DIAN</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/openapi.json</div><div class="ep-desc">Especificación OpenAPI completa</div></div></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><div class="card-title">🧪 Probar API</div></div>
          <div class="card-body">
            <div class="fg"><label>Endpoint</label>
              <select id="ep-sel">
                <option value="/health">GET /health</option>
                <option value="/api/v1/consultas/ping-dian">GET /ping-dian</option>
                <option value="/api/v1/facturas/">GET /facturas</option>
              </select>
            </div>
            <button class="btn btn-primary" style="width:100%;padding:10px;margin-bottom:12px" onclick="probar()">▶ Ejecutar</button>
            <div class="resp-box show" id="resp-api" style="min-height:120px">
              <div style="color:#4B5563;font-size:12px">// Selecciona un endpoint y ejecuta...</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ API KEYS ═══ -->
    <div id="page-keys" class="tab-content">
      <div class="card" style="max-width:640px">
        <div class="card-head"><div class="card-title">🔑 API Keys</div><button class="btn btn-primary" style="font-size:12px;padding:6px 14px">+ Nueva key</button></div>
        <div class="card-body">
          <div class="key-row"><div><div class="key-label">Producción</div><div class="key-val">rdn_live_••••••••••••••2f8a</div></div><div style="display:flex;gap:8px"><button class="act-btn">Copiar</button><button class="act-btn">Rotar</button></div></div>
          <div class="key-row"><div><div class="key-label">Pruebas / Desarrollo</div><div class="key-val">rdn_test_••••••••••••••9c1b</div></div><div style="display:flex;gap:8px"><button class="act-btn">Copiar</button><button class="act-btn">Rotar</button></div></div>
          <div style="margin-top:16px;padding:14px;background:#F8FAFC;border-radius:8px;font-size:12px;color:#64748B;line-height:1.6">
            <strong style="color:#374151">Uso:</strong> Incluye el header <code style="background:#E2E8F0;padding:1px 6px;border-radius:4px">Authorization: Bearer TU_TOKEN</code> en cada request a la API.
          </div>
        </div>
      </div>
    </div>

  </div><!-- /content -->
</div><!-- /main -->

<script>
const API = 'http://localhost:8000';

function showPage(p){
  document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(e=>e.classList.remove('active'));
  document.getElementById('page-'+p).classList.add('active');
  const titles={dashboard:['Dashboard','Resumen general'],facturas:['Facturas','Gestión de facturas electrónicas'],cesion:['Nueva Cesión','Enviar evento 037 a RADIAN/DIAN'],api:['API Explorer','Prueba los endpoints directamente'],keys:['API Keys','Gestiona tus credenciales']};
  const t=titles[p]||['',''];
  document.getElementById('page-title').textContent=t[0];
  document.getElementById('page-sub').textContent=t[1];
}

async function ceder(){
  const cufe=document.getElementById('f-cufe').value;
  const nit=document.getElementById('f-nit').value;
  const nombre=document.getElementById('f-nombre').value;
  const valor=parseFloat(document.getElementById('f-valor').value);
  const box=document.getElementById('resp-box');
  const spin=document.getElementById('spin');
  const btn=document.getElementById('btn-text');
  if(!cufe||!nit||!nombre||!valor){
    box.className='resp-box show';
    box.innerHTML='<div class="r-err">⚠ Completa todos los campos</div>';
    return;
  }
  spin.style.display='block';btn.textContent='Enviando a DIAN...';
  try{
    const r=await fetch(API+'/api/v1/cesion/crear',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cufe_factura:cufe,cesionario_nit:nit,cesionario_nombre:nombre,valor_cesion:valor})});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok) box.innerHTML='<div class="r-ok">✅ '+d.mensaje+'</div><div><span class="r-key">cude: </span><span class="r-val">"'+d.cude+'"</span></div><div><span class="r-key">estado: </span><span class="r-val">"'+d.estado+'"</span></div>';
    else box.innerHTML='<div class="r-err">❌ Error: '+JSON.stringify(d.detail)+'</div>';
  }catch(e){
    box.className='resp-box show';
    box.innerHTML='<div class="r-err">❌ API no disponible. ¿Está corriendo el servidor?</div>';
  }
  spin.style.display='none';btn.textContent='⚡ Enviar a DIAN RADIAN';
}

async function consultar(){
  const cude=document.getElementById('f-cude').value;
  const box=document.getElementById('resp-consulta');
  if(!cude){box.className='resp-box show';box.innerHTML='<div class="r-err">Ingresa el CUDE</div>';return;}
  try{
    const r=await fetch(API+'/api/v1/cesion/'+cude+'/estado');
    const d=await r.json();
    box.className='resp-box show';
    box.innerHTML='<pre style="color:#00C2FF;font-size:11px">'+JSON.stringify(d,null,2)+'</pre>';
  }catch(e){box.className='resp-box show';box.innerHTML='<div class="r-err">Error de conexión</div>';}
}

async function probar(){
  const ep=document.getElementById('ep-sel').value;
  const box=document.getElementById('resp-api');
  box.innerHTML='<div style="color:#4B5563">Ejecutando...</div>';
  try{
    const r=await fetch(API+ep);
    const d=await r.json();
    box.innerHTML='<div class="r-ok">'+r.status+' OK</div><pre style="color:#00C2FF;font-size:11px;margin-top:6px">'+JSON.stringify(d,null,2)+'</pre>';
  }catch(e){box.innerHTML='<div class="r-err">Error de conexión</div>';}
}
</script>
</body>
</html>"""

@app.get("/docs", include_in_schema=False)
async def ui():
    return HTMLResponse(UI)

@app.get("/", tags=["Health"])
async def root():
    return {"sistema":"RADIAN API","version":"1.0.0","estado":"activo","docs":"http://localhost:8000/docs"}

@app.get("/health", tags=["Health"])
async def health():
    return {"status":"ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
