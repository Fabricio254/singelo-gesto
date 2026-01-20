-- Tabela para controlar parcelas de compras
CREATE TABLE IF NOT EXISTS singelo_parcelas_compras (
    id BIGSERIAL PRIMARY KEY,
    compra_id BIGINT REFERENCES singelo_compras(id) ON DELETE CASCADE,
    numero_parcela INTEGER NOT NULL,
    total_parcelas INTEGER NOT NULL,
    valor_parcela DECIMAL(10, 2) NOT NULL,
    data_vencimento TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'pago')),
    data_pagamento TIMESTAMP WITH TIME ZONE,
    descricao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_parcelas_compra_id ON singelo_parcelas_compras(compra_id);
CREATE INDEX IF NOT EXISTS idx_parcelas_status ON singelo_parcelas_compras(status);
CREATE INDEX IF NOT EXISTS idx_parcelas_vencimento ON singelo_parcelas_compras(data_vencimento);

-- Comentários
COMMENT ON TABLE singelo_parcelas_compras IS 'Controle de parcelas de compras a pagar';
COMMENT ON COLUMN singelo_parcelas_compras.numero_parcela IS 'Número da parcela (1, 2, 3...)';
COMMENT ON COLUMN singelo_parcelas_compras.total_parcelas IS 'Total de parcelas da compra';
COMMENT ON COLUMN singelo_parcelas_compras.status IS 'Status da parcela: pendente ou pago';
