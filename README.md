# LinkedIn Hook Generator API

Eine einfache FastAPI-Anwendung zur Generierung von LinkedIn Hook-Ideen mithilfe der OpenAI API.

## Features

*   Generiert mehrere Hook-Vorschläge für LinkedIn-Posts basierend auf einem Stichwort (`key_phrase`).
*   Gesichert durch einen API-Schlüssel.
*   CORS-Konfiguration zur Unterstützung von Frontend-Anfragen (localhost und `*.stefanai.de`).
*   `/health` Endpunkt zur Überprüfung des API-Status.

## Setup

1.  **Klonen Sie das Repository (falls zutreffend)**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Erstellen Sie eine virtuelle Umgebung (empfohlen)**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```

3.  **Installieren Sie die Abhängigkeiten**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Erstellen Sie eine `.env`-Datei**

    Kopieren Sie die `.env.example` (falls vorhanden) oder erstellen Sie eine neue `.env`-Datei im Stammverzeichnis des Projekts und fügen Sie Ihre API-Schlüssel hinzu:

    ```dotenv
    # .env
    API_KEY="IHR_SICHERER_FASTAPI_API_SCHLÜSSEL"
    OPENAI_API_KEY="IHR_OPENAI_API_SCHLÜSSEL"
    ```

    *   `API_KEY`: Ein selbst definierter, sicherer Schlüssel für den Zugriff auf diese API.
    *   `OPENAI_API_KEY`: Ihr API-Schlüssel von OpenAI.

## Ausführung

Starten Sie die API mit Uvicorn:

```bash
python main.py
```

Die API läuft standardmäßig unter `http://localhost:8000`. Dank `reload=True` startet der Server automatisch neu, wenn Sie Änderungen am Code speichern.

## API Endpunkte

Die interaktive API-Dokumentation (Swagger UI), die ebenfalls detaillierte Informationen zu den Modellen und Endpunkten enthält, finden Sie unter `http://localhost:8000/docs`.

### Health Check

*   **URL:** `/health`
*   **Methode:** `GET`
*   **Beschreibung:** Überprüft den Status der API.
*   **Antwort:**
    ```json
    {
      "status": "OK"
    }
    ```

### Generate Hook Ideas

*   **URL:** `/generate-hook`
*   **Methode:** `POST`
*   **Beschreibung:** Generiert LinkedIn Hook-Ideen basierend auf der übergebenen `key_phrase`.
*   **Authentifizierung:** Erfordert einen HTTP-Header namens `access_token` mit dem Wert des `API_KEY` aus der `.env`-Datei.

    *Beispiel Header:*
    ```
    access_token: IHR_SICHERER_FASTAPI_API_SCHLÜSSEL
    ```

*   **Request Body:**
    *   Der Request muss den `Content-Type: application/json` Header haben.
    *   Der Body muss ein JSON-Objekt mit folgendem Aufbau sein:
        ```json
        {
          "key_phrase": "Ihr Thema oder Stichwort hier"
        }
        ```
        *   `key_phrase` (string, erforderlich): Das Thema oder Stichwort, zu dem Hook-Ideen generiert werden sollen.

*   **Beispiel mit `curl`:**

    ```bash
    curl -X POST "http://localhost:8000/generate-hook" \
    -H "Content-Type: application/json" \
    -H "access_token: IHR_SICHERER_FASTAPI_API_SCHLÜSSEL" \
    -d '{"key_phrase": "Künstliche Intelligenz im Marketing"}'
    ```

*   **Erfolgreiche Antwort (Status Code 200):**
    *   Die Antwort ist ein JSON-Objekt mit folgendem Aufbau:
        ```json
        {
          "hooks": [
            "Hook-Text 1",
            "Hook-Text 2",
            // ... weitere Hooks
          ],
          "key_phrase": "Das ursprünglich gesendete Thema"
        }
        ```
        *   `hooks` (array of strings): Eine Liste mit den generierten Hook-Texten.
        *   `key_phrase` (string): Die ursprünglich im Request übergebene `key_phrase`.

    *Beispiel Response Body:*
    ```json
    {
      "hooks": [
        "Ist KI der neue Marketing-Assistent, den Sie brauchen?",
        "Revolutionieren Sie Ihr Marketing mit dieser KI-Strategie!",
        "❌ Fehler, die Marketer mit KI machen (und wie Sie sie vermeiden)",
        "KI im Marketing: Hype oder die Zukunft?",
        "So nutzen Sie KI, um Ihre LinkedIn-Reichweite zu explodieren!"
      ],
      "key_phrase": "Künstliche Intelligenz im Marketing"
    }
    ```

*   **Fehlerhafte Antwort:**
    *   **403 Forbidden:** Wenn der `access_token` Header fehlt oder ungültig ist.
        ```json
        {
          "detail": "Could not validate credentials"
        }
        ```
    *   **422 Unprocessable Entity:** Wenn der Request Body ungültig ist (z.B. `key_phrase` fehlt).
    *   **500 Internal Server Error:** Wenn bei der Verarbeitung oder beim Aufruf der OpenAI API ein Fehler auftritt.
        ```json
        {
          "detail": "Fehler bei der Hook-Generierung: <Details zum Fehler>"
        }
        ```

## CORS

Die API erlaubt Anfragen von:
*   `http://localhost` (mit beliebigen Ports)
*   Allen Subdomains von `stefanai.de` (über `http` und `https`) 