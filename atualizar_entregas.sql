-- ========================================================
-- Atualização: Adicionar controle de entregas
-- ========================================================

-- Adicionar coluna taxa_entrega na tabela de vendas
ALTER TABLE singelo_vendas 
ADD COLUMN IF NOT EXISTS taxa_entrega NUMERIC(10, 2) DEFAULT 0;

-- Criar tabela para custos de entrega
CREATE TABLE IF NOT EXISTS singelo_entregas (
  id BIGSERIAL PRIMARY KEY,
  data TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  custo_entregador NUMERIC(10, 2) NOT NULL CHECK (custo_entregador >= 0),
  descricao TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para melhorar performance
CREATE INDEX IF NOT EXISTS idx_singelo_entregas_data ON singelo_entregas(data DESC);

-- Comentários
COMMENT ON TABLE singelo_entregas IS 'Custos pagos aos entregadores';
COMMENT ON COLUMN singelo_entregas.custo_entregador IS 'Valor pago ao entregador';

-- Habilitar Row Level Security
ALTER TABLE singelo_entregas ENABLE ROW LEVEL SECURITY;

-- Política de acesso
CREATE POLICY "Permitir tudo em singelo_entregas" 
ON singelo_entregas 
FOR ALL 
USING (true) 
WITH CHECK (true);

-- Verificar
SELECT 'Atualização concluída!' as status;
