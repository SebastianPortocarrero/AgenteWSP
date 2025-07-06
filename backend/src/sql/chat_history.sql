-- Crear tabla para el historial de chat con memoria a largo plazo
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    message_type TEXT NOT NULL CHECK (message_type IN ('human', 'ai', 'system')),
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Crear índices para búsquedas eficientes
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_history_message_type ON chat_history(message_type);
CREATE INDEX IF NOT EXISTS idx_chat_history_session_created ON chat_history(session_id, created_at);

-- Índice GIN para búsquedas en contenido JSONB
CREATE INDEX IF NOT EXISTS idx_chat_history_content_gin ON chat_history USING GIN (content);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at
DROP TRIGGER IF EXISTS update_chat_history_updated_at ON chat_history;
CREATE TRIGGER update_chat_history_updated_at
    BEFORE UPDATE ON chat_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Políticas de seguridad RLS (Row Level Security)
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas las operaciones (ajustar según necesidades de seguridad)
DROP POLICY IF EXISTS "Allow all operations on chat_history" ON chat_history;
CREATE POLICY "Allow all operations on chat_history" ON chat_history
    FOR ALL USING (true);

-- Función para limpiar mensajes antiguos (opcional)
CREATE OR REPLACE FUNCTION cleanup_old_chat_history(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chat_history 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estadísticas de sesión
CREATE OR REPLACE FUNCTION get_session_stats(p_session_id TEXT)
RETURNS TABLE(
    session_id TEXT,
    total_messages BIGINT,
    first_message TIMESTAMPTZ,
    last_message TIMESTAMPTZ,
    human_messages BIGINT,
    ai_messages BIGINT,
    system_messages BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_session_id,
        COUNT(*) as total_messages,
        MIN(created_at) as first_message,
        MAX(created_at) as last_message,
        COUNT(*) FILTER (WHERE message_type = 'human') as human_messages,
        COUNT(*) FILTER (WHERE message_type = 'ai') as ai_messages,
        COUNT(*) FILTER (WHERE message_type = 'system') as system_messages
    FROM chat_history 
    WHERE chat_history.session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Función para búsqueda de texto en mensajes
CREATE OR REPLACE FUNCTION search_chat_messages(
    p_session_id TEXT,
    p_search_text TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    id BIGINT,
    message_type TEXT,
    content JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ch.id,
        ch.message_type,
        ch.content,
        ch.created_at
    FROM chat_history ch
    WHERE ch.session_id = p_session_id
    AND ch.content::text ILIKE '%' || p_search_text || '%'
    ORDER BY ch.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Comentarios para documentación
COMMENT ON TABLE chat_history IS 'Almacena el historial de conversaciones para memoria a largo plazo';
COMMENT ON COLUMN chat_history.session_id IS 'Identificador único de la sesión de conversación';
COMMENT ON COLUMN chat_history.message_type IS 'Tipo de mensaje: human, ai, o system';
COMMENT ON COLUMN chat_history.content IS 'Contenido del mensaje en formato JSON';
COMMENT ON COLUMN chat_history.metadata IS 'Metadatos adicionales del mensaje';

-- Ejemplo de uso:
-- INSERT INTO chat_history (session_id, message_type, content) 
-- VALUES ('session_123', 'human', '{"content": "Hola, ¿cómo estás?"}');

-- SELECT * FROM get_session_stats('session_123');
-- SELECT * FROM search_chat_messages('session_123', 'hola', 5); 