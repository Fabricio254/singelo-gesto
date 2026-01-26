import os

secrets_content = """SUPABASE_URL = "https://brfoyobozvbmtj76aafaed.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJyZm95b2JvenZibXRqNzZhYWZhZWQiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTczNjY5MDcyNSwiZXhwIjoyMDUyMjY2NzI1fQ.tJJ-wdUwLPuGD19b8mGrCCPFTh-zRXUtzQMwfT55qgk"
GEMINI_API_KEY = "AIzaSyAwfEBRyUUm03JutVf0Q-Bcqc5GkOLY4WM"
"""

os.makedirs('.streamlit', exist_ok=True)

with open('.streamlit/secrets.toml', 'w', encoding='utf-8') as f:
    f.write(secrets_content)

print('✅ Chave do Gemini adicionada com sucesso!')
