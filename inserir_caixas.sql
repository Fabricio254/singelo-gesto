-- Script para cadastrar caixas de embalagem no sistema Singelo Gesto
-- Execute este script no SQL Editor do Supabase

INSERT INTO singelo_materiais (nome, descricao, unidade_medida, custo_unitario, estoque_atual, fornecedor_principal, observacoes, created_at)
VALUES
-- Caixa 1
('Caixa Redonda Tradicional P (15x12)', 'Caixa redonda tradicional tamanho P - 15cm x 12cm', 'unidade', 19.70, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: ROSA, MARFIN, BRANCO, VERDE ÁGUA, PRETO, AZUL', NOW()),

-- Caixa 2
('Caixa Redonda Tradicional M (19x15)', 'Caixa redonda tradicional tamanho M - 19cm x 15cm', 'unidade', 22.90, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: PRETO, ROSA, MARFIN, BRANCO, AZUL BABY, VERDE ÁGUA, AZUL ESCURO', NOW()),

-- Caixa 3
('Caixa Redonda Tradicional MG (23x15)', 'Caixa redonda tradicional tamanho MG - 23cm x 15cm', 'unidade', 24.70, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: ROSA, LILAS, PRETO, BRANCO, AZUL', NOW()),

-- Caixa 4
('Caixa Quadrada Baixa c/ Tampa (30x30x10)', 'Caixa quadrada baixa com tampa - 30cm x 30cm x 10cm', 'unidade', 29.90, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: ROSA, AZUL, BRANCO', NOW()),

-- Caixa 5
('Caixa Redonda Tradicional GG (29x15)', 'Caixa redonda tradicional tamanho GG - 29cm x 15cm', 'unidade', 42.90, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: MARFIN, AZUL ESCURO, AZUL BABY, ROSA, PRETO', NOW()),

-- Caixa 6
('Caixa Carta (22x12x31)', 'Caixa modelo carta - 22cm x 12cm x 31cm', 'unidade', 24.90, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: ROSA, MARFIN, PRETO, VERDE ÁGUA', NOW()),

-- Caixa 7
('Caixa Sacola + Alça Bandeja M (22x12x12)', 'Caixa sacola com alça bandeja tamanho M - 22cm x 12cm x 12cm', 'unidade', 25.70, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: MARFIN, ROSA, PRETO, AZUL ESCURO', NOW()),

-- Caixa 8
('Caixa Sacola + Alça Bandeja G (28x14x14)', 'Caixa sacola com alça bandeja tamanho G - 28cm x 14cm x 14cm', 'unidade', 30.70, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: MARFIN, ROSA, PRETO, AZUL ESCURO', NOW()),

-- Caixa 9
('Caixa Quadrada Baixa c/ Tampa (21x21x11)', 'Caixa quadrada baixa com tampa - 21cm x 21cm x 11cm', 'unidade', 23.90, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: PRETO, ROSA, MARFIN, AZUL', NOW()),

-- Caixa 10
('Caixa Quadrada Alta (18x18x18)', 'Caixa quadrada alta - 18cm x 18cm x 18cm', 'unidade', 23.90, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: ROSA, MARFIM, PRETO', NOW()),

-- Caixa 11
('Caixa Gaveta (16x16x20)', 'Caixa modelo gaveta - 16cm x 16cm x 20cm', 'unidade', 34.70, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: ROSA, MARFIN, AZUL BABY', NOW()),

-- Caixa 12
('Caixa Toga M (19x15)', 'Caixa modelo toga tamanho M - 19cm x 15cm', 'unidade', 29.70, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: ROSA, BRANCO, PRETO', NOW()),

-- Caixa 13
('Caixa Porta Garrafa (12x34)', 'Caixa porta garrafa - 12cm x 34cm', 'unidade', 33.90, 0, 'Fornecedor de Embalagens', 'Cores disponíveis: PRETO, AZUL', NOW());

-- Verificar se foram inseridos corretamente
SELECT nome, custo_unitario, unidade_medida FROM singelo_materiais WHERE fornecedor_principal = 'Fornecedor de Embalagens' ORDER BY custo_unitario;
