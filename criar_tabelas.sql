-- ========================================================
-- Script SQL para criar tabelas do Sistema Singelo Gesto
-- ========================================================
-- IMPORTANTE: Execute este script no SQL Editor do Supabase
-- Acesse: https://supabase.com/dashboard > SQL Editor > New Query
-- ========================================================

-- ============================================
-- Tabela: singelo_compras
-- Armazena todas as compras realizadas
-- ============================================
CREATE TABLE IF NOT EXISTS singelo_compras (
  id BIGSERIAL PRIMARY KEY,
  data TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  valor_total NUMERIC(10, 2) NOT NULL CHECK (valor_total > 0),
  descricao TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para melhorar performance nas consultas por data
CREATE INDEX IF NOT EXISTS idx_singelo_compras_data ON singelo_compras(data DESC);

-- Comentários na tabela
COMMENT ON TABLE singelo_compras IS 'Registros de compras do sistema Singelo Gesto';
COMMENT ON COLUMN singelo_compras.data IS 'Data e hora da compra';
COMMENT ON COLUMN singelo_compras.valor_total IS 'Valor total da compra em reais';
COMMENT ON COLUMN singelo_compras.descricao IS 'Descrição opcional da compra';

-- ============================================
-- Tabela: singelo_vendas
-- Armazena todas as vendas realizadas
-- ============================================
CREATE TABLE IF NOT EXISTS singelo_vendas (
  id BIGSERIAL PRIMARY KEY,
  data TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  produto TEXT NOT NULL,
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  valor_total NUMERIC(10, 2) NOT NULL CHECK (valor_total > 0),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_singelo_vendas_data ON singelo_vendas(data DESC);
CREATE INDEX IF NOT EXISTS idx_singelo_vendas_produto ON singelo_vendas(produto);

-- Comentários na tabela
COMMENT ON TABLE singelo_vendas IS 'Registros de vendas do sistema Singelo Gesto';
COMMENT ON COLUMN singelo_vendas.data IS 'Data e hora da venda';
COMMENT ON COLUMN singelo_vendas.produto IS 'Nome da box vendida';
COMMENT ON COLUMN singelo_vendas.quantidade IS 'Quantidade de boxes vendidas';
COMMENT ON COLUMN singelo_vendas.valor_total IS 'Valor total da venda em reais';

-- ============================================
-- Row Level Security (RLS)
-- ============================================
-- Habilita segurança a nível de linha
ALTER TABLE singelo_compras ENABLE ROW LEVEL SECURITY;
ALTER TABLE singelo_vendas ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Políticas de Acesso
-- ============================================
-- Permite todas as operações para usuários autenticados
-- Se você quer acesso público (sem autenticação), use estas políticas:

-- Política para singelo_compras (permite tudo)
CREATE POLICY "Permitir tudo em singelo_compras" 
ON singelo_compras 
FOR ALL 
USING (true) 
WITH CHECK (true);

-- Política para singelo_vendas (permite tudo)
CREATE POLICY "Permitir tudo em singelo_vendas" 
ON singelo_vendas 
FOR ALL 
USING (true) 
WITH CHECK (true);

-- ============================================
-- Verificação final
-- ============================================
-- Execute esta query para confirmar que as tabelas foram criadas:
SELECT 
  table_name, 
  table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE 'singelo_%'
ORDER BY table_name;

-- ============================================
-- FIM DO SCRIPT
-- ============================================
-- ✅ Se tudo correu bem, você verá:
--    - singelo_compras (table)
--    - singelo_vendas (table)
-- ============================================
