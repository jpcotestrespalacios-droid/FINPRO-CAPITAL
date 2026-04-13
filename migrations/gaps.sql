-- migrations/gaps.sql
-- GAP 4: Portal del Deudor — tabla de notificaciones legales (Ley 1231 de 2008)
-- GAP 2: Multi-tenancy — organizaciones, miembros, invitaciones
-- GAP 3: Pagos Wompi — suscripciones y pagos

-- ─────────────────────────────────────────────────────────────────────────────
-- GAP 4 · notificaciones_deudor
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notificaciones_deudor (
    id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    cude                text        NOT NULL,
    deudor_nit          text        NOT NULL,
    deudor_email        text        NOT NULL,
    estado              text        NOT NULL DEFAULT 'ENVIADA'
                                    CHECK (estado IN ('ENVIADA','CONFIRMADA','FALLIDA')),
    token_confirmacion  text        NOT NULL UNIQUE,
    enviado_en          timestamptz NOT NULL DEFAULT now(),
    confirmado_en       timestamptz,
    ip_confirmacion     text,
    created_at          timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notif_deudor_cude
    ON notificaciones_deudor (cude);

CREATE INDEX IF NOT EXISTS idx_notif_deudor_token
    ON notificaciones_deudor (token_confirmacion);

ALTER TABLE notificaciones_deudor ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_notif_deudor" ON notificaciones_deudor;
CREATE POLICY "service_role_notif_deudor"
    ON notificaciones_deudor FOR ALL
    USING (true) WITH CHECK (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- GAP 2 · organizaciones / multi-tenancy
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS organizaciones (
    id              uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre          text        NOT NULL,
    nit             text        NOT NULL UNIQUE,
    plan            text        NOT NULL DEFAULT 'starter'
                                CHECK (plan IN ('starter','professional','enterprise')),
    max_cesiones    int         NOT NULL DEFAULT 5,
    owner_id        bigint      NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    activa          boolean     NOT NULL DEFAULT true,
    created_at      timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS miembros_org (
    id              uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    organizacion_id uuid        NOT NULL REFERENCES organizaciones(id) ON DELETE CASCADE,
    usuario_id      bigint      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    rol             text        NOT NULL DEFAULT 'miembro'
                                CHECK (rol IN ('owner','admin','miembro')),
    activo          boolean     NOT NULL DEFAULT true,
    joined_at       timestamptz DEFAULT now(),
    UNIQUE (organizacion_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS invitaciones (
    id              uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    organizacion_id uuid        NOT NULL REFERENCES organizaciones(id) ON DELETE CASCADE,
    email           text        NOT NULL,
    rol             text        NOT NULL DEFAULT 'miembro'
                                CHECK (rol IN ('admin','miembro')),
    token           text        NOT NULL UNIQUE DEFAULT gen_random_uuid()::text,
    estado          text        NOT NULL DEFAULT 'PENDIENTE'
                                CHECK (estado IN ('PENDIENTE','ACEPTADA','EXPIRADA')),
    invitado_por    bigint      REFERENCES usuarios(id),
    created_at      timestamptz DEFAULT now(),
    expira_en       timestamptz DEFAULT (now() + INTERVAL '7 days')
);

-- Columna organizacion_id en facturas (nullable para no romper registros anteriores)
ALTER TABLE facturas ADD COLUMN IF NOT EXISTS organizacion_id uuid REFERENCES organizaciones(id) ON DELETE SET NULL;
ALTER TABLE cesiones ADD COLUMN IF NOT EXISTS organizacion_id uuid REFERENCES organizaciones(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_facturas_org ON facturas (organizacion_id);
CREATE INDEX IF NOT EXISTS idx_cesiones_org ON cesiones (organizacion_id);

ALTER TABLE organizaciones  ENABLE ROW LEVEL SECURITY;
ALTER TABLE miembros_org    ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitaciones    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_organizaciones" ON organizaciones;
CREATE POLICY "service_role_organizaciones" ON organizaciones FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "service_role_miembros_org" ON miembros_org;
CREATE POLICY "service_role_miembros_org"   ON miembros_org   FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "service_role_invitaciones" ON invitaciones;
CREATE POLICY "service_role_invitaciones"   ON invitaciones   FOR ALL USING (true) WITH CHECK (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- GAP 3 · pagos Wompi / suscripciones
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suscripciones (
    id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    organizacion_id     uuid        REFERENCES organizaciones(id) ON DELETE CASCADE,
    usuario_id          bigint      REFERENCES usuarios(id) ON DELETE CASCADE,
    plan                text        NOT NULL DEFAULT 'starter'
                                    CHECK (plan IN ('starter','professional','enterprise')),
    estado              text        NOT NULL DEFAULT 'ACTIVA'
                                    CHECK (estado IN ('ACTIVA','CANCELADA','VENCIDA','TRIAL')),
    max_cesiones        int         NOT NULL DEFAULT 5,
    cesiones_usadas     int         NOT NULL DEFAULT 0,
    wompi_subscription_id text,
    periodo_inicio      date        NOT NULL DEFAULT CURRENT_DATE,
    periodo_fin         date        NOT NULL DEFAULT (CURRENT_DATE + INTERVAL '30 days'),
    created_at          timestamptz DEFAULT now(),
    updated_at          timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pagos (
    id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    suscripcion_id      uuid        REFERENCES suscripciones(id) ON DELETE SET NULL,
    organizacion_id     uuid        REFERENCES organizaciones(id) ON DELETE SET NULL,
    usuario_id          bigint      REFERENCES usuarios(id) ON DELETE SET NULL,
    wompi_transaction_id text       UNIQUE,
    referencia          text        NOT NULL UNIQUE,
    monto               numeric(12,2) NOT NULL,
    moneda              text        NOT NULL DEFAULT 'COP',
    estado              text        NOT NULL DEFAULT 'PENDIENTE'
                                    CHECK (estado IN ('PENDIENTE','APROBADO','RECHAZADO','VOIDED','ERROR')),
    plan_comprado       text,
    wompi_payload       jsonb,
    created_at          timestamptz DEFAULT now(),
    updated_at          timestamptz DEFAULT now()
);

ALTER TABLE suscripciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos          ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_suscripciones" ON suscripciones;
CREATE POLICY "service_role_suscripciones" ON suscripciones FOR ALL USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "service_role_pagos" ON pagos;
CREATE POLICY "service_role_pagos"         ON pagos         FOR ALL USING (true) WITH CHECK (true);
