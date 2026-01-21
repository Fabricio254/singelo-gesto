-- SQL para criar tabela de itens de compras no Supabase
-- Execute este código no SQL Editor do Supabase

CREATE TABLE singelo_itens_compras (
    id BIGSERIAL PRIMARY KEY,
    compra_id BIGINT REFERENCES singelo_compras(id) ON DELETE CASCADE,
    nome_produto TEXT NOT NULL,
    descricao TEXT,
    quantidade NUMERIC NOT NULL,
    valor_unitario NUMERIC NOT NULL,
    valor_total NUMERIC NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar índice para melhorar performance nas buscas
CREATE INDEX idx_itens_compras_compra_id ON singelo_itens_compras(compra_id);
CREATE INDEX idx_itens_compras_nome_produto ON singelo_itens_compras(nome_produto);

-- Habilitar Row Level Security (RLS)
ALTER TABLE singelo_itens_compras ENABLE ROW LEVEL SECURITY;

-- Criar política para permitir todas as operações (ajuste conforme necessário)
CREATE POLICY "Permitir todas operações em itens_compras" ON singelo_itens_compras
FOR ALL
USING (true)
WITH CHECK (true);
