-- ============================================================================
-- 🧠 TABLAS PARA SISTEMA DE MEMORIA AVANZADO
-- ============================================================================

-- Tabla para memoria semántica (conocimiento y conceptos)
CREATE TABLE IF NOT EXISTS semantic_memory (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    concept TEXT NOT NULL,
    knowledge TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para memoria semántica
CREATE INDEX IF NOT EXISTS idx_semantic_memory_session_id ON semantic_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_semantic_memory_concept ON semantic_memory(concept);
CREATE INDEX IF NOT EXISTS idx_semantic_memory_category ON semantic_memory(category);
CREATE INDEX IF NOT EXISTS idx_semantic_memory_confidence ON semantic_memory(confidence);

-- Tabla para memoria procedimental (procedimientos y workflows)
CREATE TABLE IF NOT EXISTS procedural_memory (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    procedure_name TEXT NOT NULL,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    context TEXT DEFAULT '',
    success_rate FLOAT DEFAULT 1.0,
    usage_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para memoria procedimental
CREATE INDEX IF NOT EXISTS idx_procedural_memory_session_id ON procedural_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_procedural_memory_procedure_name ON procedural_memory(procedure_name);
CREATE INDEX IF NOT EXISTS idx_procedural_memory_success_rate ON procedural_memory(success_rate);
CREATE INDEX IF NOT EXISTS idx_procedural_memory_usage_count ON procedural_memory(usage_count);
CREATE INDEX IF NOT EXISTS idx_procedural_memory_last_used ON procedural_memory(last_used);

-- Índice GIN para búsquedas en steps JSONB
CREATE INDEX IF NOT EXISTS idx_procedural_memory_steps_gin ON procedural_memory USING GIN (steps);

-- Función para actualizar updated_at en memoria semántica
CREATE OR REPLACE FUNCTION update_semantic_memory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at en memoria semántica
DROP TRIGGER IF EXISTS update_semantic_memory_updated_at_trigger ON semantic_memory;
CREATE TRIGGER update_semantic_memory_updated_at_trigger
    BEFORE UPDATE ON semantic_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_semantic_memory_updated_at();

-- Políticas de seguridad RLS para memoria semántica
ALTER TABLE semantic_memory ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all operations on semantic_memory" ON semantic_memory;
CREATE POLICY "Allow all operations on semantic_memory" ON semantic_memory
    FOR ALL USING (true);

-- Políticas de seguridad RLS para memoria procedimental
ALTER TABLE procedural_memory ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all operations on procedural_memory" ON procedural_memory;
CREATE POLICY "Allow all operations on procedural_memory" ON procedural_memory
    FOR ALL USING (true);

-- Función para obtener estadísticas de memoria semántica
CREATE OR REPLACE FUNCTION get_semantic_memory_stats(p_session_id TEXT)
RETURNS TABLE(
    session_id TEXT,
    total_concepts BIGINT,
    categories TEXT[],
    avg_confidence FLOAT,
    most_recent_concept TEXT,
    most_confident_concept TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_session_id,
        COUNT(*) as total_concepts,
        ARRAY_AGG(DISTINCT category) as categories,
        AVG(confidence) as avg_confidence,
        (SELECT concept FROM semantic_memory 
         WHERE semantic_memory.session_id = p_session_id 
         ORDER BY created_at DESC LIMIT 1) as most_recent_concept,
        (SELECT concept FROM semantic_memory 
         WHERE semantic_memory.session_id = p_session_id 
         ORDER BY confidence DESC LIMIT 1) as most_confident_concept
    FROM semantic_memory 
    WHERE semantic_memory.session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estadísticas de memoria procedimental
CREATE OR REPLACE FUNCTION get_procedural_memory_stats(p_session_id TEXT)
RETURNS TABLE(
    session_id TEXT,
    total_procedures BIGINT,
    avg_success_rate FLOAT,
    total_usage_count BIGINT,
    most_used_procedure TEXT,
    best_procedure TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_session_id,
        COUNT(*) as total_procedures,
        AVG(success_rate) as avg_success_rate,
        SUM(usage_count) as total_usage_count,
        (SELECT procedure_name FROM procedural_memory 
         WHERE procedural_memory.session_id = p_session_id 
         ORDER BY usage_count DESC LIMIT 1) as most_used_procedure,
        (SELECT procedure_name FROM procedural_memory 
         WHERE procedural_memory.session_id = p_session_id 
         ORDER BY success_rate DESC LIMIT 1) as best_procedure
    FROM procedural_memory 
    WHERE procedural_memory.session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Función para buscar conocimiento semántico por texto
CREATE OR REPLACE FUNCTION search_semantic_knowledge(
    p_session_id TEXT,
    p_search_text TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    id BIGINT,
    concept TEXT,
    knowledge TEXT,
    category TEXT,
    confidence FLOAT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sm.id,
        sm.concept,
        sm.knowledge,
        sm.category,
        sm.confidence,
        sm.created_at
    FROM semantic_memory sm
    WHERE sm.session_id = p_session_id
    AND (sm.concept ILIKE '%' || p_search_text || '%' 
         OR sm.knowledge ILIKE '%' || p_search_text || '%')
    ORDER BY sm.confidence DESC, sm.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Función para buscar procedimientos por contexto
CREATE OR REPLACE FUNCTION search_procedures_by_context(
    p_session_id TEXT,
    p_context_text TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    id BIGINT,
    procedure_name TEXT,
    steps JSONB,
    context TEXT,
    success_rate FLOAT,
    usage_count INTEGER,
    last_used TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pm.id,
        pm.procedure_name,
        pm.steps,
        pm.context,
        pm.success_rate,
        pm.usage_count,
        pm.last_used
    FROM procedural_memory pm
    WHERE pm.session_id = p_session_id
    AND (pm.procedure_name ILIKE '%' || p_context_text || '%' 
         OR pm.context ILIKE '%' || p_context_text || '%')
    ORDER BY pm.success_rate DESC, pm.usage_count DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar memoria antigua (opcional)
CREATE OR REPLACE FUNCTION cleanup_old_advanced_memory(days_to_keep INTEGER DEFAULT 30)
RETURNS TABLE(
    semantic_deleted INTEGER,
    procedural_deleted INTEGER
) AS $$
DECLARE
    semantic_count INTEGER;
    procedural_count INTEGER;
BEGIN
    -- Limpiar memoria semántica antigua
    DELETE FROM semantic_memory 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    GET DIAGNOSTICS semantic_count = ROW_COUNT;
    
    -- Limpiar memoria procedimental antigua (solo procedimientos poco usados)
    DELETE FROM procedural_memory 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep
    AND usage_count < 3;
    GET DIAGNOSTICS procedural_count = ROW_COUNT;
    
    RETURN QUERY SELECT semantic_count, procedural_count;
END;
$$ LANGUAGE plpgsql;

-- Comentarios para documentación
COMMENT ON TABLE semantic_memory IS 'Almacena conocimiento semántico: conceptos, hechos y información aprendida';
COMMENT ON TABLE procedural_memory IS 'Almacena memoria procedimental: procedimientos, workflows y patrones de resolución';

COMMENT ON COLUMN semantic_memory.concept IS 'Concepto o tema del conocimiento';
COMMENT ON COLUMN semantic_memory.knowledge IS 'Información o conocimiento específico';
COMMENT ON COLUMN semantic_memory.category IS 'Categoría del conocimiento (user_profile, conversation_topics, etc.)';
COMMENT ON COLUMN semantic_memory.confidence IS 'Nivel de confianza en el conocimiento (0.0 a 1.0)';

COMMENT ON COLUMN procedural_memory.procedure_name IS 'Nombre identificativo del procedimiento';
COMMENT ON COLUMN procedural_memory.steps IS 'Pasos del procedimiento en formato JSON';
COMMENT ON COLUMN procedural_memory.context IS 'Contexto donde se aplica el procedimiento';
COMMENT ON COLUMN procedural_memory.success_rate IS 'Tasa de éxito del procedimiento (0.0 a 1.0)';
COMMENT ON COLUMN procedural_memory.usage_count IS 'Número de veces que se ha usado el procedimiento';

-- Ejemplos de uso:
-- SELECT * FROM get_semantic_memory_stats('session_123');
-- SELECT * FROM get_procedural_memory_stats('session_123');
-- SELECT * FROM search_semantic_knowledge('session_123', 'usuario', 5);
-- SELECT * FROM search_procedures_by_context('session_123', 'reglamento', 5);
-- SELECT * FROM cleanup_old_advanced_memory(30); 