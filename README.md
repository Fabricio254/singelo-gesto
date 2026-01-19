# 🎁 Singelo Gesto - Sistema de Gestão

Sistema de gerenciamento de vendas e compras para **Singelo Gesto - Box de Luxo Personalizadas**.

## 🚀 Funcionalidades

- ✅ Dashboard financeiro com resumo de compras, vendas e lucro
- ✅ Registro de compras com valor total e descrição
- ✅ Registro de vendas com produto, quantidade e valor
- ✅ Histórico completo de todas as movimentações
- ✅ Boxes pré-cadastradas:
  - Box Café da manhã/tarde
  - Box Chocolate
  - Box Maternidade
  - Box Casamento
  - Box Aniversário
- ✅ Interface responsiva (funciona em desktop e mobile)
- ✅ Cores e design inspirados na identidade visual da empresa
- ✅ Dados sincronizados em tempo real com Supabase

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Conta no Supabase (gratuita)

## 🔧 Instalação

1. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

2. **Configure o Supabase:**

   a) Você já tem acesso ao Supabase em: https://supabase.com/dashboard
   
   b) No dashboard do Supabase, vá em **SQL Editor** e execute o arquivo `criar_tabelas.sql`:
      - Clique em **SQL Editor** no menu lateral
      - Clique em **New Query**
      - Cole todo o conteúdo do arquivo `criar_tabelas.sql`
      - Clique em **Run** ou pressione `Ctrl + Enter`
      - Você verá uma mensagem de sucesso confirmando que as tabelas foram criadas

   c) Copie sua **Anon Key** do Supabase:
      - Vá em **Settings** → **API**
      - Copie a **anon/public key**

   d) Edite o arquivo `app.py` (linha 9) e cole sua Anon Key:
   ```python
   SUPABASE_URL = "https://fjgugglxqyhlyxwzvdts.supabase.co"  # Já configurado
   SUPABASE_KEY = "cole_sua_anon_key_aqui"  # COLE AQUI
   ```

3. **Adicione a logo (opcional):**
   - Salve a logo da empresa como `logo.png` na pasta do projeto

## ▶️ Como Executar

Execute o comando:
```bash
streamlit run app.py
```

O sistema abrirá automaticamente no navegador em `http://localhost:8501`

## 📱 Acesso Mobile

Para acessar pelo celular:

1. Certifique-se de que o celular está na mesma rede WiFi do computador
2. Execute o app no computador
3. No terminal, procure por "Network URL" (ex: http://192.168.1.10:8501)
4. Acesse esse endereço no navegador do celular

## 🌐 Deploy Online (Opcional)

Para deixar o app online 24/7:

1. Crie uma conta gratuita no [Streamlit Community Cloud](https://streamlit.io/cloud)
2. Conecte seu repositório GitHub
3. Configure as variáveis de ambiente (SUPABASE_URL e SUPABASE_KEY)
4. Deploy automático!

## 🎨 Cores do Tema

- **Primary:** #C9A58A (Bege rosado)
- **Secondary:** #A67C6B (Terracota)
- **Background:** #F5E6DC (Bege claro)
- **Text:** #6B4E3D (Marrom)

## 📊 Estrutura do Banco de Dados

⚠️ **IMPORTANTE:** As tabelas usam o prefixo `singelo_` para não conflitar com o sistema existente (produtos, grades, lotes)

### Tabela: singelo_compras
- `id` - Identificador único
- `data` - Data e hora da compra
- `valor_total` - Valor total da compra
- `descricao` - Descrição opcional
- `created_at` - Data de criação do registro

### Tabela: singelo_vendas
- `id` - Identificador único
- `data` - Data e hora da venda
- `produto` - Nome da box vendida
- `quantidade` - Quantidade de boxes
- `valor_total` - Valor total da venda
- `created_at` - Data de criação do registro

## 🛠️ Suporte

Para problemas ou dúvidas, verifique:
- ✅ Credenciais do Supabase estão corretas
- ✅ Tabelas foram criadas no banco de dados
- ✅ Dependências estão instaladas (`pip install -r requirements.txt`)

## 📄 Licença

Sistema desenvolvido exclusivamente para Singelo Gesto.
