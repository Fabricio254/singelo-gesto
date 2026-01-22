-- ========================================
-- SISTEMA DE FICHA TÉCNICA DE PRODUTOS
-- ========================================

-- Tabela de Materiais/Insumos
CREATE TABLE singelo_materiais (
    id BIGSERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    unidade_medida TEXT NOT NULL, -- 'unidade', 'metro', 'litro', 'kg', 'pacote', etc
    estoque_atual NUMERIC DEFAULT 0,
    custo_unitario NUMERIC NOT NULL, -- custo por unidade de medida
    ultima_compra_data DATE,
    fornecedor_principal TEXT,
    observacoes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de Fichas Técnicas (composição dos produtos)
CREATE TABLE singelo_fichas_tecnicas (
    id BIGSERIAL PRIMARY KEY,
    produto TEXT NOT NULL, -- nome do produto final (ex: "Box de Flor com Caneca")
    material_id BIGINT REFERENCES singelo_materiais(id) ON DELETE CASCADE,
    quantidade NUMERIC NOT NULL, -- quantidade do material necessária
    observacoes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(produto, material_id) -- não permitir material duplicado na mesma ficha
);

-- Tabela de Movimentações de Estoque
CREATE TABLE singelo_movimentacoes_estoque (
    id BIGSERIAL PRIMARY KEY,
    material_id BIGINT REFERENCES singelo_materiais(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL, -- 'entrada' (compra) ou 'saida' (uso em produção)
    quantidade NUMERIC NOT NULL,
    custo_unitario NUMERIC, -- registra o custo no momento da movimentação
    compra_id BIGINT REFERENCES singelo_compras(id) ON DELETE SET NULL, -- se for entrada de compra
    venda_id BIGINT REFERENCES singelo_vendas(id) ON DELETE SET NULL, -- se for saída por produção
    observacoes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para melhorar performance
CREATE INDEX idx_materiais_nome ON singelo_materiais(nome);
CREATE INDEX idx_fichas_produto ON singelo_fichas_tecnicas(produto);
CREATE INDEX idx_fichas_material ON singelo_fichas_tecnicas(material_id);
CREATE INDEX idx_movimentacoes_material ON singelo_movimentacoes_estoque(material_id);
CREATE INDEX idx_movimentacoes_tipo ON singelo_movimentacoes_estoque(tipo);

-- Políticas de segurança (Row Level Security)
ALTER TABLE singelo_materiais ENABLE ROW LEVEL SECURITY;
ALTER TABLE singelo_fichas_tecnicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE singelo_movimentacoes_estoque ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir todas operações em materiais" ON singelo_materiais
FOR ALL
USING (true)
WITH CHECK (true);

CREATE POLICY "Permitir todas operações em fichas_tecnicas" ON singelo_fichas_tecnicas
FOR ALL
USING (true)
WITH CHECK (true);

CREATE POLICY "Permitir todas operações em movimentacoes_estoque" ON singelo_movimentacoes_estoque
FOR ALL
USING (true)
WITH CHECK (true);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_materiais_updated_at
    BEFORE UPDATE ON singelo_materiais
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

-- View para visualizar custo total por produto
CREATE OR REPLACE VIEW vw_custo_produtos AS
SELECT 
    ft.produto,
    SUM(ft.quantidade * m.custo_unitario) as custo_total_producao,
    COUNT(ft.id) as total_materiais,
    json_agg(
        json_build_object(
            'material', m.nome,
            'quantidade', ft.quantidade,
            'unidade', m.unidade_medida,
            'custo_unitario', m.custo_unitario,
            'custo_total', ft.quantidade * m.custo_unitario
        )
    ) as detalhes_materiais
FROM singelo_fichas_tecnicas ft
JOIN singelo_materiais m ON ft.material_id = m.id
GROUP BY ft.produto;
