-- Adicionar campos de endereço de entrega na tabela singelo_vendas
ALTER TABLE singelo_vendas 
ADD COLUMN IF NOT EXISTS data_entrega DATE,
ADD COLUMN IF NOT EXISTS cep VARCHAR(10),
ADD COLUMN IF NOT EXISTS logradouro TEXT,
ADD COLUMN IF NOT EXISTS numero VARCHAR(20),
ADD COLUMN IF NOT EXISTS complemento TEXT,
ADD COLUMN IF NOT EXISTS bairro VARCHAR(100),
ADD COLUMN IF NOT EXISTS cidade VARCHAR(100),
ADD COLUMN IF NOT EXISTS uf VARCHAR(2);

-- Comentários
COMMENT ON COLUMN singelo_vendas.data_entrega IS 'Data prevista para entrega';
COMMENT ON COLUMN singelo_vendas.cep IS 'CEP do endereço de entrega';
COMMENT ON COLUMN singelo_vendas.logradouro IS 'Rua/Avenida do endereço de entrega';
COMMENT ON COLUMN singelo_vendas.numero IS 'Número do endereço de entrega';
COMMENT ON COLUMN singelo_vendas.complemento IS 'Complemento do endereço';
COMMENT ON COLUMN singelo_vendas.bairro IS 'Bairro do endereço de entrega';
COMMENT ON COLUMN singelo_vendas.cidade IS 'Cidade do endereço de entrega';
COMMENT ON COLUMN singelo_vendas.uf IS 'Estado (UF) do endereço de entrega';
