with open(r'Z:\codigos\Singelo\.streamlit\secrets.toml', 'w', encoding='utf-8') as f:
    f.write('SUPABASE_URL = "https://brfoyobozvbmtj76aafaed.supabase.co"\n')
    f.write('SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJyZm95b2JvenZibXRqNzZhYWZhZWQiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTczNjY5MDcyNSwiZXhwIjoyMDUyMjY2NzI1fQ.tJJ-wdUwLPuGD19b8mGrCCPFTh-zRXUtzQMwfT55qgk"\n')
    f.write('GEMINI_API_KEY = "AIzaSyAwfEBRyUUm03JutVf0Q-Bcqc5GkOLY4WM"\n')

print("✅ Arquivo secrets.toml criado com sucesso!")
