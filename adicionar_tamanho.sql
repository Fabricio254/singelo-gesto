-- ========================================================
-- Adicionar campo tamanho nas vendas
-- ========================================================

-- Adicionar coluna tamanho na tabela de vendas
ALTER TABLE singelo_vendas 
ADD COLUMN IF NOT EXISTS tamanho TEXT;

-- Verificar
SELECT 'Campo tamanho adicionado com sucesso!' as status;
