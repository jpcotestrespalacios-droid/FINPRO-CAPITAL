-- migrations/email_preferences.sql
-- Ejecutar en el SQL Editor de Supabase (https://app.supabase.com → SQL Editor)
--
-- Tabla de preferencias de notificaciones por email por usuario.
-- Un row por usuario, todos los flags en true por defecto.

CREATE TABLE IF NOT EXISTS email_preferences (
    id          uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     bigint      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,

    -- Flags de notificación (todos habilitados por defecto)
    notify_bienvenida           boolean NOT NULL DEFAULT true,
    notify_cesion_aceptada      boolean NOT NULL DEFAULT true,
    notify_cesion_rechazada     boolean NOT NULL DEFAULT true,
    notify_vencimiento_7d       boolean NOT NULL DEFAULT true,
    notify_vencimiento_vencida  boolean NOT NULL DEFAULT true,
    notify_reporte_mensual      boolean NOT NULL DEFAULT true,

    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now(),

    UNIQUE (user_id)
);

-- Índice para búsquedas rápidas por user_id
CREATE INDEX IF NOT EXISTS idx_email_preferences_user_id
    ON email_preferences (user_id);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_email_preferences_updated_at ON email_preferences;
CREATE TRIGGER trg_email_preferences_updated_at
    BEFORE UPDATE ON email_preferences
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- RLS: cada usuario solo puede ver/editar sus propias preferencias
ALTER TABLE email_preferences ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_own_prefs_select" ON email_preferences;
CREATE POLICY "user_own_prefs_select"
    ON email_preferences FOR SELECT
    USING (user_id::text = auth.uid()::text);

DROP POLICY IF EXISTS "user_own_prefs_insert" ON email_preferences;
CREATE POLICY "user_own_prefs_insert"
    ON email_preferences FOR INSERT
    WITH CHECK (user_id::text = auth.uid()::text);

DROP POLICY IF EXISTS "user_own_prefs_update" ON email_preferences;
CREATE POLICY "user_own_prefs_update"
    ON email_preferences FOR UPDATE
    USING (user_id::text = auth.uid()::text);

DROP POLICY IF EXISTS "service_role_all" ON email_preferences;
CREATE POLICY "service_role_all"
    ON email_preferences FOR ALL
    USING (true)
    WITH CHECK (true);
