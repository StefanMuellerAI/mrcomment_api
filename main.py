from fastapi import FastAPI, Security, HTTPException, Depends, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import os
# import secrets # Nicht mehr benötigt
from openai import OpenAI
from typing import List
from dotenv import load_dotenv # Hinzugefügt
from fastapi.middleware.cors import CORSMiddleware # Hinzugefügt

# Lade Umgebungsvariablen aus der .env Datei
load_dotenv() # Hinzugefügt

# --- Configuration ---
# Lade API-Schlüssel aus Umgebungsvariablen (geladen aus .env)
API_KEY = os.getenv("API_KEY") # Geändert: Kein Default mehr
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Sicherstellen, dass es geladen wird für Checks

# Überprüfen, ob die Schlüssel gesetzt sind
if not API_KEY:
    raise ValueError("API_KEY nicht in der .env Datei oder Umgebungsvariablen gefunden.")
if not OPENAI_API_KEY:
    # Obwohl die OpenAI-Bibliothek es selbst lädt, prüfen wir hier zur Sicherheit
    raise ValueError("OPENAI_API_KEY nicht in der .env Datei oder Umgebungsvariablen gefunden.")

# Lade den Systemprompt aus der Markdown-Datei
try:
    with open("linkedin_hook_system_prompt.md", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    raise FileNotFoundError("Die Datei 'linkedin_hook_system_prompt.md' wurde nicht gefunden. Bitte erstellen Sie sie.")
except Exception as e:
    raise RuntimeError(f"Fehler beim Lesen von 'linkedin_hook_system_prompt.md': {e}")

if not SYSTEM_PROMPT:
    raise ValueError("Die Datei 'linkedin_hook_system_prompt.md' ist leer.")

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Initialize OpenAI client (liest OPENAI_API_KEY aus Umgebungsvariablen)
# Die Variable wurde bereits oben geprüft
client = OpenAI()

# --- Security ---
async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Validates the API Key provided in the header."""
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

# --- Application ---
app = FastAPI(
    title="Hook Generator API",
    description="API to generate LinkedIn hooks based on key phrases.",
    version="0.1.0",
)

# --- CORS Middleware ---
# Definiere die erlaubten Ursprünge (Origins) mittels Regex
# Erlaubt http://localhost (mit optionalem Port), alle Subdomains von stefanai.de (http/https) und ALLE Vercel-Domains
origin_regex = r"^https?:\/\/(.*\.)?stefanai\.de$|^http:\/\/localhost(:[0-9]+)?$|^https:\/\/.*\.vercel\.app$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origin_regex, # Regex anstelle einer Liste verwenden
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class HealthCheck(BaseModel):
    status: str = "OK"

class HookRequest(BaseModel):
    key_phrase: str

class HookResponse(BaseModel):
    hooks: List[str]
    key_phrase: str

# --- Endpoints ---
@app.get("/health", response_model=HealthCheck, tags=["Status"])
async def health_check():
    """Performs a health check."""
    return HealthCheck(status="OK")

@app.post("/generate-hook", response_model=HookResponse, tags=["Hooks"], dependencies=[Depends(get_api_key)])
async def generate_hook(request: HookRequest):
    """
    Generates multiple LinkedIn hook ideas based on the provided key phrase using OpenAI.
    Requires API Key authentication.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    # Verwende den geladenen Systemprompt
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Erstelle 5 kurze, aufmerksamkeitsstarke Hook-Ideen für einen LinkedIn-Post zum Thema: '{request.key_phrase}'. Gib nur die Hook-Texte als nummerierte Liste zurück, ohne zusätzliche Erklärungen."
                }
            ],
            temperature=0.8,
            max_tokens=200,
            n=1
        )

        # Extrahieren der Hooks aus der Antwort
        content = response.choices[0].message.content
        generated_hooks = [line.strip().split('. ', 1)[-1] for line in content.strip().split('\n') if line.strip()]

        if not generated_hooks:
            raise HTTPException(status_code=500, detail="OpenAI hat keine Hooks zurückgegeben.")

        return HookResponse(hooks=generated_hooks, key_phrase=request.key_phrase)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Hook-Generierung: {e}")

# --- Optional: Run with uvicorn (for development) ---
if __name__ == "__main__":
    import uvicorn
    print(f"--- Starting API ---")
    # Gib den API-Key nicht mehr aus Sicherheitsgründen aus
    # print(f"Default API Key for testing: {API_KEY}") 
    print(f"API Key loaded from .env") # Geänderte Nachricht
    print(f"Header name for authentication: '{API_KEY_NAME}'") # Geänderte Nachricht
    print(f"--------------------")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) # Uvicorn angepasst für Reload 