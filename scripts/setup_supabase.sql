-- LEADS
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ghl_contact_id TEXT UNIQUE,
    name TEXT,
    phone TEXT,
    email TEXT,
    source TEXT CHECK (source IN ('form', 'whatsapp_directo', 'referido')),
    status TEXT DEFAULT 'nuevo' CHECK (status IN (
        'nuevo', 'en_calificacion', 'calificado', 'agendado',
        'pre_llamada', 'post_llamada', 'cerrado', 'descartado',
        'dormido', 'escalado'
    )),
    qualification_score INT DEFAULT 0,
    diabetes_type TEXT,
    medication TEXT,
    years_with_diabetes INT,
    motivation TEXT,
    investment_ready BOOLEAN,
    clinical_data_sent BOOLEAN DEFAULT false,
    funnel_stage TEXT DEFAULT 'sin_vsl' CHECK (funnel_stage IN (
        'sin_vsl', 'vio_vsl', 'lleno_form', 'en_nutricion',
        'calificado', 'agendado'
    )),
    window_open_until TIMESTAMPTZ,
    assigned_agent TEXT DEFAULT 'setter' CHECK (assigned_agent IN ('setter', 'post_agenda', 'human')),
    form_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    agent TEXT CHECK (agent IN ('setter', 'post_agenda')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'closed')),
    started_at TIMESTAMPTZ DEFAULT now(),
    last_message_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    close_reason TEXT
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('bot', 'lead', 'system')),
    content TEXT NOT NULL,
    original_audio_url TEXT,
    was_audio BOOLEAN DEFAULT false,
    template_used TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    ghl_appointment_id TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL,
    zoom_link TEXT,
    show_status TEXT DEFAULT 'pending' CHECK (show_status IN (
        'pending', 'showed', 'no_show', 'cancelled', 'rescheduled'
    )),
    reschedule_count INT DEFAULT 0,
    reminder_24h_sent BOOLEAN DEFAULT false,
    reminder_2h_sent BOOLEAN DEFAULT false,
    rescue_attempts INT DEFAULT 0,
    call_result TEXT CHECK (call_result IN ('venta_cerrada', 'no_cerro', 'pensando')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE funnel_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT CHECK (type IN ('link', 'video', 'image', 'document')),
    url TEXT NOT NULL,
    funnel_stage TEXT,
    avatar_segment TEXT DEFAULT 'general',
    description TEXT,
    active BOOLEAN DEFAULT true
);

CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT CHECK (category IN (
        'caso_exito', 'objecion_respuesta', 'faq', 'protocolo', 'regla'
    )),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    avatar_segment TEXT DEFAULT 'general',
    priority INT DEFAULT 0,
    active BOOLEAN DEFAULT true
);

CREATE TABLE bot_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT
);

CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    ghl_template_id TEXT NOT NULL,
    variables JSONB,
    use_case TEXT
);

CREATE TABLE scheduled_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL,
    lead_id UUID REFERENCES leads(id),
    scheduled_for TIMESTAMPTZ NOT NULL,
    executed BOOLEAN DEFAULT false,
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE objections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    conversation_id UUID REFERENCES conversations(id),
    text TEXT NOT NULL,
    category TEXT CHECK (category IN (
        'precio', 'tiempo', 'confianza', 'medico', 'pareja', 'otro'
    )),
    resolved BOOLEAN DEFAULT false,
    resolution_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE frequent_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    conversation_id UUID REFERENCES conversations(id),
    question_text TEXT NOT NULL,
    category TEXT,
    count INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE conversation_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    conversation_id UUID REFERENCES conversations(id),
    qualification_score INT,
    engagement_score INT,
    message_count INT,
    duration_minutes INT,
    outcome TEXT CHECK (outcome IN ('agendado', 'descartado', 'dormido', 'escalado')),
    drop_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE weekly_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    total_leads INT,
    qualified INT,
    scheduled INT,
    showed INT,
    top_objections JSONB,
    top_questions JSONB,
    insights JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID,
    event_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- INDEXES
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_ghl_contact_id ON leads(ghl_contact_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_appointments_lead_id ON appointments(lead_id);
CREATE INDEX idx_appointments_scheduled_at ON appointments(scheduled_at);
CREATE INDEX idx_scheduled_jobs_scheduled_for ON scheduled_jobs(scheduled_for)
    WHERE executed = false;
CREATE INDEX idx_event_log_lead_id ON event_log(lead_id);
CREATE INDEX idx_event_log_created_at ON event_log(created_at);

-- UPDATED_AT TRIGGER
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
