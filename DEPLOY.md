# 🚀 GUIA DE DEPLOY - STREAMLIT CLOUD

## 📋 Pré-requisitos

1. ✅ Conta no GitHub (gratuita)
2. ✅ Conta no Streamlit Cloud (gratuita)

---

## 🎯 PASSO A PASSO COMPLETO

### 1️⃣ **Criar Repositório no GitHub**

1. Acesse: https://github.com/new
2. Configure:
   - **Repository name:** `singelo-gesto`
   - **Description:** Sistema de Gestão - Singelo Gesto
   - **Visibility:** Private (privado) ✅ 
   - ⚠️ **NÃO** marque "Add a README file"
3. Clique em **Create repository**

---

### 2️⃣ **Enviar Código para o GitHub**

Abra o PowerShell na pasta do projeto:

```powershell
cd Z:\codigos\Singelo

# Inicializar Git
git init

# Adicionar todos os arquivos
git add .

# Fazer primeiro commit
git commit -m "Sistema Singelo Gesto - Primeira versão"

# Conectar com GitHub (substitua SEU_USUARIO pelo seu usuário do GitHub)
git remote add origin https://github.com/SEU_USUARIO/singelo-gesto.git

# Enviar para GitHub
git branch -M main
git push -u origin main
```

⚠️ **Se pedir usuário e senha:**
- Usuário: seu username do GitHub
- Senha: use um **Personal Access Token** (não a senha normal)
  - Crie em: https://github.com/settings/tokens
  - Clique em "Generate new token (classic)"
  - Marque: `repo` (full control)
  - Copie o token e use como senha

---

### 3️⃣ **Fazer Deploy no Streamlit Cloud**

1. Acesse: https://share.streamlit.io/

2. Clique em **"New app"**

3. Configure:
   - **Repository:** `seu-usuario/singelo-gesto`
   - **Branch:** `main`
   - **Main file path:** `app.py`

4. Clique em **"Advanced settings"**

5. Cole no campo **"Secrets"**:
```toml
SUPABASE_URL = "https://fjgugglxqyhlyxwzvdts.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqZ3VnZ2x4cXlobHl4d3p2ZHRzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzODI4NzQsImV4cCI6MjA3NTk1ODg3NH0.YGQIfxghu4yK58iVoklI1YkwwH6aoprZ06LUsWzcYPk"
```

6. Clique em **"Deploy!"**

7. ⏳ Aguarde 2-3 minutos enquanto faz o deploy

8. 🎉 **Pronto!** Você receberá um link tipo:
   ```
   https://singelo-gesto.streamlit.app
   ```

---

## 📱 **Como Usar**

**No computador/celular:**
- Abra o link que você recebeu
- Funciona de qualquer lugar, 24/7!
- Salve nos favoritos do celular

---

## 🔄 **Como Atualizar o Sistema**

Quando quiser fazer mudanças:

```powershell
cd Z:\codigos\Singelo

# Fazer alterações no código...

# Enviar atualizações
git add .
git commit -m "Descrição da mudança"
git push

# O Streamlit Cloud atualiza automaticamente em 1-2 minutos!
```

---

## ❓ **Problemas Comuns**

### "Git não é reconhecido"
Instale o Git: https://git-scm.com/download/win

### "Permission denied" no push
Use um Personal Access Token como senha (veja passo 2)

### App não carrega
Verifique os secrets no Streamlit Cloud (Settings → Secrets)

---

## 🎯 **Resultado Final**

✅ Sistema online 24/7  
✅ Acesso de qualquer lugar  
✅ URL personalizada  
✅ Sem custo algum  
✅ Atualiza automaticamente  

---

## 📞 **Precisa de Ajuda?**

Me avise se encontrar algum problema! 😊
