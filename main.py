from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from routers import facturas, cesion, autenticacion, consultas
from config import settings
from database import engine, Base

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables: {e}")

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
<title>FINPRO CAPITAL — RADIAN API</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F0F2F5;color:#1a1a2e;min-height:100vh}

/* ── LOGIN ── */
#login-screen{display:flex;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#0A1628 0%,#1347CC 100%)}
.login-box{background:#fff;border-radius:16px;padding:40px;width:420px;box-shadow:0 24px 64px rgba(0,0,0,0.3)}
.login-logo{font-size:26px;font-weight:900;color:#0A1628;letter-spacing:-1px;margin-bottom:4px}
.login-logo em{font-style:normal;color:#1347CC}
.login-sub{font-size:12px;color:#94A3B8;margin-bottom:32px;text-transform:uppercase;letter-spacing:1.5px}
.login-title{font-size:20px;font-weight:700;color:#0F172A;margin-bottom:4px}
.login-desc{font-size:13px;color:#64748B;margin-bottom:24px}
.lf{display:flex;flex-direction:column;gap:5px;margin-bottom:14px}
.lf label{font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px}
.lf input{padding:11px 14px;border:1.5px solid #E2E8F0;border-radius:10px;font-size:14px;font-family:inherit;outline:none;transition:.15s}
.lf input:focus{border-color:#1347CC;box-shadow:0 0 0 3px rgba(19,71,204,0.1)}
.login-btn{width:100%;padding:13px;background:linear-gradient(135deg,#1347CC,#0891B2);color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit;margin-top:8px;transition:.15s}
.login-btn:hover{opacity:.9;transform:translateY(-1px)}
.login-toggle{text-align:center;margin-top:20px;font-size:13px;color:#64748B}
.login-toggle a{color:#1347CC;font-weight:600;cursor:pointer;text-decoration:none}
.login-err{background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;border-radius:8px;padding:10px 14px;font-size:13px;margin-bottom:14px;display:none}

/* ── APP ── */
#app-screen{display:none;min-height:100vh;display:none}
.sidebar{width:240px;background:#0A1628;display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:100}
.logo{padding:20px;border-bottom:1px solid rgba(255,255,255,0.07)}
.logo-text{font-size:20px;font-weight:900;color:#fff;letter-spacing:-0.5px}
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
.sidebar-bottom{margin-top:auto;padding:16px;border-top:1px solid rgba(255,255,255,0.07)}
.user-row{display:flex;align-items:center;gap:10px}
.avatar{width:34px;height:34px;background:#1347CC;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0}
.user-name{font-size:13px;font-weight:600;color:rgba(255,255,255,0.85)}
.user-nit{font-size:10px;color:rgba(255,255,255,0.3);margin-top:1px}
.logout-btn{width:100%;margin-top:10px;padding:8px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#EF4444;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;transition:.15s}
.logout-btn:hover{background:rgba(239,68,68,0.2)}

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

.content{padding:24px 28px;flex:1}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:20px;position:relative;overflow:hidden}
.stat::after{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.stat.s1::after{background:#00C2FF}
.stat.s2::after{background:#10B981}
.stat.s3::after{background:#F59E0B}
.stat.s4::after{background:#7C3AED}
.stat-label{font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:600}
.stat-val{font-size:30px;font-weight:800;color:#0F172A;line-height:1;letter-spacing:-1px}
.stat-sub{font-size:11px;margin-top:6px;color:#94A3B8}

.grid{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;margin-bottom:20px}
.card{background:#fff;border:1px solid #E2E8F0;border-radius:12px;overflow:hidden}
.card-head{padding:16px 20px;border-bottom:1px solid #F1F5F9;display:flex;align-items:center;justify-content:space-between}
.card-title{font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px}
.card-link{font-size:12px;color:#1347CC;font-weight:600;cursor:pointer}
.card-body{padding:20px}

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
.b-gray{background:#F1F5F9;color:#64748B}
.act-btn{background:none;border:1px solid #E2E8F0;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;font-family:inherit;color:#374151;font-weight:600;transition:.15s}
.act-btn:hover{border-color:#1347CC;color:#1347CC}
.act-btn.pri{background:#1347CC;color:#fff;border-color:#1347CC}

.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:0}
.fg{display:flex;flex-direction:column;gap:5px;margin-bottom:12px}
.fg label{font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:0.5px}
.fg input,.fg select{padding:9px 12px;border:1.5px solid #E2E8F0;border-radius:8px;font-size:13px;font-family:inherit;color:#0F172A;background:#F8FAFC;outline:none;transition:.15s}
.fg input:focus,.fg select:focus{border-color:#1347CC;background:#fff;box-shadow:0 0 0 3px rgba(19,71,204,0.08)}
.fg input::placeholder{color:#94A3B8}
.submit-btn{width:100%;padding:12px;background:linear-gradient(135deg,#1347CC,#0891B2);color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;display:flex;align-items:center;justify-content:center;gap:8px;transition:.15s;margin-top:4px}
.submit-btn:hover{opacity:.9;transform:translateY(-1px)}
.submit-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}

.resp-box{background:#0D1117;border-radius:8px;padding:16px;font-family:monospace;font-size:12px;line-height:1.7;margin-top:14px;display:none;max-height:260px;overflow-y:auto}
.resp-box.show{display:block}
.r-ok{color:#10B981;font-weight:700;font-size:13px;margin-bottom:6px}
.r-err{color:#EF4444;font-weight:700}

.tab-content{display:none}
.tab-content.active{display:block}

.ep-item{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #F8FAFC;font-size:12px}
.ep-item:last-child{border:none}
.method{padding:3px 8px;border-radius:5px;font-size:10px;font-weight:800;min-width:46px;text-align:center;font-family:monospace}
.m-post{background:#ECFDF5;color:#059669}
.m-get{background:#EFF6FF;color:#1347CC}
.m-put{background:#FFFBEB;color:#D97706}
.ep-path{font-family:monospace;font-size:12px;color:#374151;flex:1}
.ep-desc{font-size:11px;color:#94A3B8}

.empty{text-align:center;padding:40px;color:#94A3B8;font-size:13px}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}

/* Toast */
#toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:600;color:#fff;z-index:9999;transform:translateY(80px);opacity:0;transition:.3s;pointer-events:none}
#toast.show{transform:translateY(0);opacity:1}
#toast.ok{background:#10B981}
#toast.err{background:#EF4444}

/* Steps */
.step{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px solid #F8FAFC}
.step:last-child{border:none}
.step-num{width:26px;height:26px;border-radius:50%;background:#1347CC;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0}
.step-num.done{background:#10B981}
.step-title{font-size:13px;font-weight:600;color:#0F172A}
.step-desc{font-size:11px;color:#64748B;margin-top:2px}

/* Filter bar */
.filter-bar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.filter-btn{padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;border:1.5px solid #E2E8F0;background:#fff;cursor:pointer;transition:.15s;font-family:inherit;color:#64748B}
.filter-btn:hover,.filter-btn.active{background:#1347CC;color:#fff;border-color:#1347CC}
</style>
</head>
<body>

<!-- ═══ LOGIN ═══ -->
<div id="login-screen">
  <div class="login-box">
    <div class="login-logo">FINPRO<em>CAPITAL</em></div>
    <div class="login-sub">Sistema RADIAN · Endoso de Facturas</div>
    <div id="login-panel">
      <div class="login-title">Iniciar sesión</div>
      <div class="login-desc">Ingresa tus credenciales para continuar</div>
      <div class="login-err" id="login-err"></div>
      <div class="lf"><label>Correo electrónico</label><input id="l-email" type="email" placeholder="empresa@correo.com" /></div>
      <div class="lf"><label>Contraseña</label><input id="l-pass" type="password" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()" /></div>
      <button class="login-btn" onclick="doLogin()" id="login-btn">Ingresar</button>
      <div class="login-toggle">¿No tienes cuenta? <a onclick="showPanel('register')">Registrar empresa</a></div>
    </div>
    <div id="register-panel" style="display:none">
      <div class="login-title">Registrar empresa</div>
      <div class="login-desc">Crea tu cuenta para acceder al sistema RADIAN</div>
      <div class="login-err" id="reg-err"></div>
      <div class="form-row">
        <div class="lf"><label>Nombre empresa</label><input id="r-nombre" placeholder="MI EMPRESA SAS" /></div>
        <div class="lf"><label>NIT</label><input id="r-nit" placeholder="900.123.456-1" /></div>
      </div>
      <div class="lf"><label>Correo electrónico</label><input id="r-email" type="email" placeholder="empresa@correo.com" /></div>
      <div class="lf"><label>Contraseña</label><input id="r-pass" type="password" placeholder="••••••••" /></div>
      <button class="login-btn" onclick="doRegister()" id="reg-btn">Crear cuenta</button>
      <div class="login-toggle">¿Ya tienes cuenta? <a onclick="showPanel('login')">Iniciar sesión</a></div>
    </div>
  </div>
</div>

<!-- ═══ APP ═══ -->
<div id="app-screen">
<nav class="sidebar">
  <div class="logo">
    <div class="logo-text">FINPRO<em>CAPITAL</em></div>
    <div class="logo-sub">RADIAN · v1.0.0</div>
  </div>
  <div class="env-badge"><div class="env-dot"></div><span class="env-text">DIAN Habilitación</span></div>
  <div class="nav-section">Principal</div>
  <a class="nav-item active" id="nav-dashboard" onclick="showPage('dashboard')"><span class="nav-icon">📊</span> Dashboard</a>
  <a class="nav-item" id="nav-facturas" onclick="showPage('facturas')"><span class="nav-icon">📋</span> Facturas</a>
  <a class="nav-item" id="nav-cesion" onclick="showPage('cesion')"><span class="nav-icon">⚡</span> Nueva Cesión</a>
  <a class="nav-item" id="nav-consultar" onclick="showPage('consultar')"><span class="nav-icon">🔍</span> Consultar DIAN</a>
  <div class="nav-section">Sistema</div>
  <a class="nav-item" id="nav-api" onclick="showPage('api')"><span class="nav-icon">🔌</span> API Explorer</a>
  <a class="nav-item" href="/openapi.json" target="_blank"><span class="nav-icon">📖</span> OpenAPI JSON</a>
  <div class="sidebar-bottom">
    <div class="user-row">
      <div class="avatar" id="user-avatar">?</div>
      <div><div class="user-name" id="user-name">Cargando...</div><div class="user-nit" id="user-nit"></div></div>
    </div>
    <button class="logout-btn" onclick="doLogout()">Cerrar sesión</button>
  </div>
</nav>

<div class="main">
  <div class="topbar">
    <div><div class="page-h" id="page-title">Dashboard</div><div class="page-sub" id="page-sub">Resumen general</div></div>
    <div class="topbar-actions">
      <button class="btn btn-ghost" onclick="showPage('api')">🔌 API</button>
      <button class="btn btn-primary" onclick="showPage('cesion')">⚡ Nueva Cesión</button>
    </div>
  </div>

  <div class="content">

    <!-- ═══ DASHBOARD ═══ -->
    <div id="page-dashboard" class="tab-content active">
      <div class="stats">
        <div class="stat s1"><div class="stat-label">Total Facturas</div><div class="stat-val" id="st-total">—</div><div class="stat-sub">registradas en el sistema</div></div>
        <div class="stat s2"><div class="stat-label">Cedidas</div><div class="stat-val" id="st-cedidas">—</div><div class="stat-sub">cesiones completadas</div></div>
        <div class="stat s3"><div class="stat-label">Títulos Valor</div><div class="stat-val" id="st-titulos">—</div><div class="stat-sub">listas para ceder</div></div>
        <div class="stat s4"><div class="stat-label">En Proceso</div><div class="stat-val" id="st-proceso">—</div><div class="stat-sub">enviadas a DIAN</div></div>
      </div>
      <div class="grid">
        <div class="card">
          <div class="card-head"><div class="card-title">⚡ Últimas Facturas</div><a class="card-link" onclick="showPage('facturas')">Ver todas →</a></div>
          <div class="card-body" style="padding:0">
            <table class="tbl">
              <thead><tr><th>Número</th><th>Adquiriente</th><th>Valor</th><th>Estado</th></tr></thead>
              <tbody id="dash-facturas"><tr><td colspan="4" class="empty">Cargando...</td></tr></tbody>
            </table>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:16px">
          <div class="card">
            <div class="card-head"><div class="card-title">📋 Proceso de Cesión</div></div>
            <div class="card-body">
              <div class="step"><div class="step-num done">1</div><div><div class="step-title">Factura validada DIAN</div><div class="step-desc">CUFE emitido y activo</div></div></div>
              <div class="step"><div class="step-num done">2</div><div><div class="step-title">Evento 032 y 033</div><div class="step-desc">Recibo y aceptación del adquiriente</div></div></div>
              <div class="step"><div class="step-num">3</div><div><div class="step-title">Habilitar título valor</div><div class="step-desc">Marcar factura como endosable</div></div></div>
              <div class="step"><div class="step-num" style="background:#00C2FF;color:#000">4</div><div><div class="step-title">Ceder en RADIAN</div><div class="step-desc">Evento 037 → DIAN (~1 seg)</div></div></div>
            </div>
          </div>
          <div class="card">
            <div class="card-head"><div class="card-title">⚙️ Estado del sistema</div></div>
            <div class="card-body">
              <div style="display:flex;flex-direction:column;gap:10px">
                <div style="display:flex;justify-content:space-between;align-items:center;font-size:13px">
                  <span style="color:#64748B">API RADIAN</span>
                  <span class="badge b-green" id="status-api">Verificando...</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;font-size:13px">
                  <span style="color:#64748B">DIAN Habilitación</span>
                  <span class="badge b-gold" id="status-dian">Sin certificado</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;font-size:13px">
                  <span style="color:#64748B">Base de datos</span>
                  <span class="badge b-green" id="status-db">Conectada</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ FACTURAS ═══ -->
    <div id="page-facturas" class="tab-content">
      <div class="filter-bar">
        <button class="filter-btn active" onclick="filterFacturas(this,'')">Todas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'EMITIDA')">Emitidas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'VALIDADA_DIAN')">Validadas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'CEDIDA')">Cedidas</button>
        <button class="filter-btn" onclick="filterFacturas(this,'EN_CESION')">En Cesión</button>
        <button class="filter-btn" onclick="filterFacturas(this,'RECHAZADA')">Rechazadas</button>
      </div>
      <div class="card">
        <div class="card-head">
          <div class="card-title">📋 Facturas <span id="fact-count" style="font-size:12px;color:#94A3B8;font-weight:500"></span></div>
          <button class="btn btn-primary" style="font-size:12px;padding:6px 14px" onclick="showPage('cesion')">⚡ Nueva Cesión</button>
        </div>
        <div class="card-body" style="padding:0">
          <table class="tbl">
            <thead><tr><th>Número / CUFE</th><th>Adquiriente</th><th>Valor Total</th><th>Vencimiento</th><th>Estado</th><th>Acción</th></tr></thead>
            <tbody id="facturas-body"><tr><td colspan="6" class="empty">Cargando...</td></tr></tbody>
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
            <div class="fg"><label>CUFE de la Factura</label><input id="f-cufe" placeholder="Código único de la factura electrónica" /></div>
            <div class="form-row">
              <div class="fg"><label>NIT Cesionario</label><input id="f-nit-ces" placeholder="900.123.456-1" /></div>
              <div class="fg"><label>Nombre Cesionario</label><input id="f-nombre-ces" placeholder="BANCO EJEMPLO SAS" /></div>
            </div>
            <div class="form-row">
              <div class="fg"><label>NIT Deudor</label><input id="f-nit-deu" placeholder="800.000.000-1" /></div>
              <div class="fg"><label>Nombre Deudor</label><input id="f-nombre-deu" placeholder="EMPRESA DEUDORA SAS" /></div>
            </div>
            <div class="fg"><label>Valor a Ceder (COP)</label><input id="f-valor" type="number" placeholder="120000000" /></div>
            <button class="submit-btn" onclick="ceder()" id="btn-ceder">
              <span id="btn-ceder-text">⚡ Enviar a DIAN RADIAN</span>
            </button>
            <div class="resp-box" id="resp-cesion"></div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:16px">
          <div class="card">
            <div class="card-head"><div class="card-title">📋 Pasos requeridos</div></div>
            <div class="card-body">
              <div class="step"><div class="step-num done">1</div><div><div class="step-title">Validar que sea título valor</div><div class="step-desc">La factura debe tener <code style="background:#F1F5F9;padding:1px 5px;border-radius:3px">es_titulo_valor = true</code></div></div></div>
              <div class="step"><div class="step-num done">2</div><div><div class="step-title">Construir XML UBL 2.1</div><div class="step-desc">Evento 037 con CUDE SHA-384</div></div></div>
              <div class="step"><div class="step-num done">3</div><div><div class="step-title">Firmar digitalmente</div><div class="step-desc">Certificado Certicámara / Andes SCD</div></div></div>
              <div class="step"><div class="step-num" style="background:#00C2FF;color:#000">4</div><div><div class="step-title">Respuesta DIAN</div><div class="step-desc">Procesada en ~1 segundo</div></div></div>
            </div>
          </div>
          <div class="card">
            <div class="card-head"><div class="card-title">🔧 Habilitar título valor</div></div>
            <div class="card-body">
              <div class="fg"><label>CUFE de la factura</label><input id="f-cufe-hab" placeholder="Ingresa el CUFE a habilitar" /></div>
              <button class="btn btn-ghost" style="width:100%;padding:10px" onclick="habilitarTitulo()">✅ Habilitar como título valor</button>
              <div class="resp-box" id="resp-habilitar"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ CONSULTAR DIAN ═══ -->
    <div id="page-consultar" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-head"><div class="card-title">🔍 Consultar estado en DIAN</div></div>
          <div class="card-body">
            <div class="fg"><label>CUDE del evento de cesión</label><input id="f-cude" placeholder="d8f3a1...sha384" /></div>
            <button class="submit-btn" onclick="consultarDian()" style="background:linear-gradient(135deg,#059669,#0891B2)">🔍 Consultar en DIAN</button>
            <div class="resp-box" id="resp-dian"></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><div class="card-title">🏥 Ping a DIAN</div></div>
          <div class="card-body">
            <p style="font-size:13px;color:#64748B;margin-bottom:16px">Verifica la conectividad con el webservice de la DIAN (ambiente de habilitación).</p>
            <button class="submit-btn" onclick="pingDian()" style="background:linear-gradient(135deg,#7C3AED,#1347CC)">🏥 Verificar conexión DIAN</button>
            <div class="resp-box" id="resp-ping"></div>
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
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/api/v1/facturas/</div><div class="ep-desc">Listar todas las facturas</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/api/v1/facturas/{cufe}</div><div class="ep-desc">Consultar factura por CUFE</div></div></div>
            <div class="ep-item"><span class="method m-post">POST</span><div><div class="ep-path">/api/v1/cesion/crear</div><div class="ep-desc">⚡ Ceder factura en RADIAN</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/api/v1/cesion/{cude}/estado</div><div class="ep-desc">Estado de cesión en DIAN</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/api/v1/consultas/ping-dian</div><div class="ep-desc">Verificar conexión DIAN</div></div></div>
            <div class="ep-item"><span class="method m-get">GET</span><div><div class="ep-path">/health</div><div class="ep-desc">Estado de la API</div></div></div>
          </div>
        </div>
        <div class="card">
          <div class="card-head"><div class="card-title">🧪 Probar endpoint</div></div>
          <div class="card-body">
            <div class="fg"><label>Endpoint</label>
              <select id="ep-sel">
                <option value="/health">GET /health</option>
                <option value="/api/v1/facturas/">GET /facturas (requiere auth)</option>
                <option value="/api/v1/consultas/ping-dian">GET /ping-dian (requiere auth)</option>
              </select>
            </div>
            <button class="btn btn-primary" style="width:100%;padding:10px;margin-bottom:12px" onclick="probarEndpoint()">▶ Ejecutar</button>
            <div class="resp-box show" id="resp-api" style="min-height:120px">
              <div style="color:#4B5563;font-size:12px">// Selecciona un endpoint y ejecuta...</div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>
</div>

<div id="toast"></div>

<script>
const API = '';
let TOKEN = sessionStorage.getItem('radian_token') || '';
let USER_DATA = JSON.parse(sessionStorage.getItem('radian_user') || 'null');

// ── INIT ──
window.onload = () => {
  if(TOKEN) {
    showApp();
  }
};

function showPanel(p) {
  document.getElementById('login-panel').style.display = p==='login'?'':'none';
  document.getElementById('register-panel').style.display = p==='register'?'':'none';
}

// ── AUTH ──
async function doLogin() {
  const email = document.getElementById('l-email').value.trim();
  const pass = document.getElementById('l-pass').value;
  const errEl = document.getElementById('login-err');
  const btn = document.getElementById('login-btn');
  if(!email||!pass){showErr(errEl,'Completa todos los campos');return;}
  btn.textContent='Ingresando...';btn.disabled=true;
  try {
    const fd = new FormData();
    fd.append('username',email);fd.append('password',pass);
    const r = await fetch(API+'/api/v1/auth/token',{method:'POST',body:fd});
    const d = await r.json();
    if(!r.ok){showErr(errEl,d.detail||'Credenciales incorrectas');return;}
    TOKEN = d.access_token;
    sessionStorage.setItem('radian_token',TOKEN);
    showApp();
  } catch(e){showErr(errEl,'Error de conexión con el servidor');}
  finally{btn.textContent='Ingresar';btn.disabled=false;}
}

async function doRegister() {
  const nombre=document.getElementById('r-nombre').value.trim();
  const nit=document.getElementById('r-nit').value.trim();
  const email=document.getElementById('r-email').value.trim();
  const pass=document.getElementById('r-pass').value;
  const errEl=document.getElementById('reg-err');
  const btn=document.getElementById('reg-btn');
  if(!nombre||!nit||!email||!pass){showErr(errEl,'Completa todos los campos');return;}
  btn.textContent='Creando cuenta...';btn.disabled=true;
  try {
    const r=await fetch(API+'/api/v1/auth/registro',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,nombre,nit,password:pass})});
    const d=await r.json();
    if(!r.ok){showErr(errEl,d.detail||'Error al registrar');return;}
    toast('Cuenta creada. Ahora inicia sesión.','ok');
    showPanel('login');
    document.getElementById('l-email').value=email;
  }catch(e){showErr(errEl,'Error de conexión');}
  finally{btn.textContent='Crear cuenta';btn.disabled=false;}
}

function doLogout() {
  TOKEN='';USER_DATA=null;
  sessionStorage.removeItem('radian_token');
  sessionStorage.removeItem('radian_user');
  document.getElementById('app-screen').style.display='none';
  document.getElementById('login-screen').style.display='flex';
}

function showErr(el,msg){el.textContent=msg;el.style.display='block';}

// ── APP ──
function showApp() {
  document.getElementById('login-screen').style.display='none';
  document.getElementById('app-screen').style.display='block';
  loadDashboard();
}

function authHeaders(){return {'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'};}

async function loadUserInfo() {
  try {
    const r=await fetch(API+'/api/v1/auth/me',{headers:authHeaders()});
    if(r.ok){
      const d=await r.json();
      USER_DATA=d;sessionStorage.setItem('radian_user',JSON.stringify(d));
    }
  }catch(e){}
  if(USER_DATA){
    document.getElementById('user-name').textContent=USER_DATA.nombre||USER_DATA.email;
    document.getElementById('user-nit').textContent='NIT '+USER_DATA.nit;
    const ini=(USER_DATA.nombre||USER_DATA.email).substring(0,2).toUpperCase();
    document.getElementById('user-avatar').textContent=ini;
  }
}

async function loadDashboard() {
  loadUserInfo();
  checkApiStatus();
  try {
    const r=await fetch(API+'/api/v1/facturas/?limit=100',{headers:authHeaders()});
    if(r.status===401){doLogout();return;}
    if(!r.ok) throw new Error();
    const d=await r.json();
    const facts=d.facturas||[];
    document.getElementById('st-total').textContent=d.total||0;
    document.getElementById('st-cedidas').textContent=facts.filter(f=>f.estado==='CEDIDA').length;
    document.getElementById('st-titulos').textContent=facts.filter(f=>f.es_titulo_valor&&f.estado!=='CEDIDA').length;
    document.getElementById('st-proceso').textContent=facts.filter(f=>f.estado==='EN_CESION').length;
    const tbody=document.getElementById('dash-facturas');
    if(!facts.length){tbody.innerHTML='<tr><td colspan="4" class="empty">No hay facturas registradas aún</td></tr>';return;}
    tbody.innerHTML=facts.slice(0,5).map(f=>`
      <tr>
        <td><div class="td-main">${f.prefijo||'FV'}-${f.numero}</div><div class="td-sub">${(f.cufe||'').substring(0,16)}...</div></td>
        <td style="font-size:12px">${f.adquiriente_nombre||'—'}</td>
        <td class="td-val">$${fmtNum(f.valor_total)}</td>
        <td>${badgeEstado(f.estado)}</td>
      </tr>`).join('');
  }catch(e){document.getElementById('dash-facturas').innerHTML='<tr><td colspan="4" class="empty">Error cargando facturas</td></tr>';}
}

async function loadFacturas(estado='') {
  const tbody=document.getElementById('facturas-body');
  tbody.innerHTML='<tr><td colspan="6" class="empty">Cargando...</td></tr>';
  try {
    const url=API+'/api/v1/facturas/?limit=100'+(estado?'&estado='+estado:'');
    const r=await fetch(url,{headers:authHeaders()});
    if(!r.ok) throw new Error();
    const d=await r.json();
    const facts=d.facturas||[];
    document.getElementById('fact-count').textContent='('+d.total+')';
    if(!facts.length){tbody.innerHTML='<tr><td colspan="6" class="empty">No hay facturas con este filtro</td></tr>';return;}
    tbody.innerHTML=facts.map(f=>`
      <tr>
        <td><div class="td-main">${f.prefijo||'FV'}-${f.numero}</div><div class="td-sub">${(f.cufe||'').substring(0,20)}...</div></td>
        <td style="font-size:12px">${f.adquiriente_nombre||'—'}</td>
        <td class="td-val">$${fmtNum(f.valor_total)}</td>
        <td style="font-size:12px;color:#64748B">${fmtDate(f.fecha_vencimiento)}</td>
        <td>${badgeEstado(f.estado)}</td>
        <td>${f.es_titulo_valor&&f.estado!=='CEDIDA'?`<button class="act-btn pri" onclick="irCeder('${f.cufe}')">⚡ Ceder</button>`:`<button class="act-btn" onclick="irDetalle('${f.cufe}')">Ver</button>`}</td>
      </tr>`).join('');
  }catch(e){tbody.innerHTML='<tr><td colspan="6" class="empty">Error cargando datos</td></tr>';}
}

function filterFacturas(btn,estado){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  loadFacturas(estado);
}

function irCeder(cufe){
  document.getElementById('f-cufe').value=cufe;
  showPage('cesion');
}
function irDetalle(cufe){
  toast('CUFE: '+cufe,'ok');
}

async function ceder() {
  const cufe=document.getElementById('f-cufe').value.trim();
  const nit=document.getElementById('f-nit-ces').value.trim();
  const nombre=document.getElementById('f-nombre-ces').value.trim();
  const nitDeu=document.getElementById('f-nit-deu').value.trim();
  const nombreDeu=document.getElementById('f-nombre-deu').value.trim();
  const valor=parseFloat(document.getElementById('f-valor').value);
  const box=document.getElementById('resp-cesion');
  const btn=document.getElementById('btn-ceder');
  if(!cufe||!nit||!nombre||!valor){
    box.className='resp-box show';box.innerHTML='<div class="r-err">⚠ Completa los campos requeridos</div>';return;
  }
  btn.disabled=true;document.getElementById('btn-ceder-text').innerHTML='<span class="spinner"></span> Enviando a DIAN...';
  try {
    const r=await fetch(API+'/api/v1/cesion/crear',{method:'POST',headers:authHeaders(),body:JSON.stringify({cufe_factura:cufe,cesionario_nit:nit,cesionario_nombre:nombre,deudor_nit:nitDeu,deudor_nombre:nombreDeu,valor_cesion:valor})});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok){
      box.innerHTML='<div class="r-ok">✅ '+d.mensaje+'</div><pre style="color:#00C2FF;margin-top:8px">'+JSON.stringify(d,null,2)+'</pre>';
      toast('Cesión enviada exitosamente','ok');
    } else {
      box.innerHTML='<div class="r-err">❌ '+JSON.stringify(d.detail)+'</div>';
    }
  }catch(e){box.className='resp-box show';box.innerHTML='<div class="r-err">❌ Error de conexión</div>';}
  finally{btn.disabled=false;document.getElementById('btn-ceder-text').textContent='⚡ Enviar a DIAN RADIAN';}
}

async function habilitarTitulo() {
  const cufe=document.getElementById('f-cufe-hab').value.trim();
  const box=document.getElementById('resp-habilitar');
  if(!cufe){box.className='resp-box show';box.innerHTML='<div class="r-err">Ingresa el CUFE</div>';return;}
  try {
    const r=await fetch(API+'/api/v1/facturas/'+cufe+'/habilitar-cesion',{method:'PUT',headers:authHeaders()});
    const d=await r.json();
    box.className='resp-box show';
    if(r.ok){box.innerHTML='<div class="r-ok">✅ '+d.mensaje+'</div>';toast('Factura habilitada','ok');}
    else box.innerHTML='<div class="r-err">❌ '+JSON.stringify(d.detail)+'</div>';
  }catch(e){box.className='resp-box show';box.innerHTML='<div class="r-err">❌ Error de conexión</div>';}
}

async function consultarDian() {
  const cude=document.getElementById('f-cude').value.trim();
  const box=document.getElementById('resp-dian');
  if(!cude){box.className='resp-box show';box.innerHTML='<div class="r-err">Ingresa el CUDE</div>';return;}
  box.className='resp-box show';box.innerHTML='<div style="color:#4B5563">Consultando DIAN...</div>';
  try {
    const r=await fetch(API+'/api/v1/cesion/'+cude+'/estado',{headers:authHeaders()});
    const d=await r.json();
    box.innerHTML=r.ok?'<div class="r-ok">✅ Respuesta DIAN</div><pre style="color:#00C2FF;margin-top:6px">'+JSON.stringify(d,null,2)+'</pre>':'<div class="r-err">❌ '+JSON.stringify(d.detail)+'</div>';
  }catch(e){box.innerHTML='<div class="r-err">❌ Error de conexión</div>';}
}

async function pingDian() {
  const box=document.getElementById('resp-ping');
  box.className='resp-box show';box.innerHTML='<div style="color:#4B5563">Verificando conexión...</div>';
  try {
    const r=await fetch(API+'/api/v1/consultas/ping-dian',{headers:authHeaders()});
    const d=await r.json();
    box.innerHTML=r.ok?'<div class="r-ok">✅ Conexión exitosa</div><pre style="color:#00C2FF;margin-top:6px">'+JSON.stringify(d,null,2)+'</pre>':'<div class="r-err">❌ '+JSON.stringify(d)+'</div>';
  }catch(e){box.innerHTML='<div class="r-err">❌ No se pudo conectar a DIAN</div>';}
}

async function probarEndpoint() {
  const ep=document.getElementById('ep-sel').value;
  const box=document.getElementById('resp-api');
  box.innerHTML='<div style="color:#4B5563">Ejecutando...</div>';
  try {
    const hdrs=ep.startsWith('/api')?authHeaders():{};
    const r=await fetch(API+ep,{headers:hdrs});
    const d=await r.json();
    box.innerHTML='<div class="r-ok">'+r.status+' OK</div><pre style="color:#00C2FF;font-size:11px;margin-top:6px">'+JSON.stringify(d,null,2)+'</pre>';
  }catch(e){box.innerHTML='<div class="r-err">Error de conexión</div>';}
}

async function checkApiStatus() {
  try {
    const r=await fetch(API+'/health');
    document.getElementById('status-api').className='badge '+(r.ok?'b-green':'b-red');
    document.getElementById('status-api').textContent=r.ok?'Activa':'Error';
  }catch(e){document.getElementById('status-api').className='badge b-red';document.getElementById('status-api').textContent='Sin conexión';}
}

function showPage(p) {
  document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(e=>e.classList.remove('active'));
  const el=document.getElementById('page-'+p);
  if(el) el.classList.add('active');
  const nav=document.getElementById('nav-'+p);
  if(nav) nav.classList.add('active');
  const titles={
    dashboard:['Dashboard','Resumen general del sistema RADIAN'],
    facturas:['Facturas','Gestión de facturas electrónicas endosables'],
    cesion:['Nueva Cesión','Enviar evento 037 a RADIAN / DIAN'],
    consultar:['Consultar DIAN','Verificar estado de eventos en RADIAN'],
    api:['API Explorer','Prueba los endpoints directamente']
  };
  const t=titles[p]||[p,''];
  document.getElementById('page-title').textContent=t[0];
  document.getElementById('page-sub').textContent=t[1];
  if(p==='facturas') loadFacturas();
}

// ── UTILS ──
function fmtNum(n){if(!n&&n!==0)return'—';if(n>=1e9)return(n/1e9).toFixed(1)+'B';if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(0)+'K';return n.toLocaleString('es-CO');}
function fmtDate(d){if(!d)return'—';try{return new Date(d).toLocaleDateString('es-CO',{day:'2-digit',month:'short',year:'numeric'});}catch{return d;}}
function badgeEstado(e){const m={'EMITIDA':'b-gray','VALIDADA_DIAN':'b-blue','EN_CESION':'b-gold','CEDIDA':'b-green','PAGADA':'b-green','RECHAZADA':'b-red'};return`<span class="badge ${m[e]||'b-gray'}">${e||'—'}</span>`;}
function toast(msg,type){const t=document.getElementById('toast');t.textContent=msg;t.className='show '+type;clearTimeout(t._t);t._t=setTimeout(()=>t.className='',3000);}
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
