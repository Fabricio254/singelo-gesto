# 🚀 GUIA RÁPIDO DE INSTALAÇÃO - SINGELO GESTO

## ✅ Passo 1: Instalar Dependências
Abra o PowerShell e execute:
```powershell
cd Z:\codigos\Singelo
pip install -r requirements.txt
```

## ✅ Passo 2: Criar as Tabelas no Supabase

1. Acesse: https://supabase.com/dashboard
2. Selecione seu projeto
3. Clique em **SQL Editor** no menu lateral
4. Clique em **New Query**
5. Abra o arquivo `criar_tabelas.sql` desta pasta
6. **Copie TODO o conteúdo** e cole no SQL Editor
7. Clique em **Run** (ou pressione Ctrl + Enter)
8. ✅ Você verá uma mensagem de sucesso!

## ✅ Passo 3: Copiar a Anon Key

1. No Supabase Dashboard, vá em **Settings** → **API**
2. Procure por **Project API keys**
3. Copie a chave **anon / public** (a chave grande)

## ✅ Passo 4: Configurar o app.py

1. Abra o arquivo `app.py`
2. Procure pela linha 9:
```python
SUPABASE_KEY = "COLE_SUA_ANON_KEY_AQUI"
```
3. **Substitua** "COLE_SUA_ANON_KEY_AQUI" pela sua chave (mantendo as aspas)
4. Salve o arquivo (Ctrl + S)

Exemplo final:
```python
SUPABASE_URL = "https://fjgugglxqyhlyxwzvdts.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBh..."
```

## ✅ Passo 5: Executar o Sistema

No PowerShell, execute:
```powershell
streamlit run app.py
```

O sistema abrirá automaticamente no navegador! 🎉

## 📱 Acesso pelo Celular

Quando o sistema estiver rodando, o PowerShell mostrará algo como:
```
Local URL: http://localhost:8501
Network URL: http://192.168.1.10:8501
```

No celular (conectado na mesma WiFi):
1. Abra o navegador
2. Digite o **Network URL** (ex: http://192.168.1.10:8501)
3. Pronto! O sistema funciona no celular também! 📱

## ❓ Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'streamlit'"
**Solução:** Execute novamente: `pip install -r requirements.txt`

### Erro: "Error connecting to Supabase"
**Solução:** Verifique se copiou a Anon Key corretamente no app.py

### O sistema não abre no navegador
**Solução:** Abra manualmente: http://localhost:8501

### Erro: "Table singelo_compras does not exist"
**Solução:** Execute o script SQL no Supabase (Passo 2)

## 🎨 Logo (Opcional)

Para adicionar a logo da empresa:
1. Salve a imagem como `logo.png` nesta pasta
2. A logo aparecerá automaticamente no topo do sistema

---

## 📞 Contato

Se tiver alguma dúvida, me avise! 😊
