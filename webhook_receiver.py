from flask import Flask, request, abort
import hmac
import hashlib
import subprocess
import os
from dotenv import load_dotenv # dotenv laden
# Lade Umgebungsvariablen (insbesondere für das Secret)
load_dotenv()
app = Flask(__name__)

    # Lade das Secret aus der .env Datei oder einer Umgebungsvariable
    # Es ist sicherer, es NICHT direkt im Code zu haben.
    # Füge GITHUB_WEBHOOK_SECRET="DEIN_SEHR_GEHEIMES_SECRET" zu deiner .env Datei hinzu!
WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
DEPLOY_SCRIPT_PATH = '/var/www/mrcomment_api/deploy.sh' # Pfad zum Deployment-Skript

def verify_signature(payload_body, secret_token, signature_header):
        """Verifiziert die GitHub Webhook Signatur."""
        if not signature_header:
            print("ERROR: X-Hub-Signature-256 header missing!")
            return False
        if not secret_token:
            print("ERROR: GITHUB_WEBHOOK_SECRET not configured on server!")
            return False # Nicht sicher ohne Secret!

        hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = "sha256=" + hash_object.hexdigest()
        if not hmac.compare_digest(expected_signature, signature_header):
            print(f"ERROR: Invalid signature. Expected: {expected_signature}, Got: {signature_header}")
            return False
        return True

@app.route('/webhook', methods=['POST'])
def webhook():
        signature = request.headers.get('X-Hub-Signature-256')

        # Signaturen-Verifizierung ist KRITISCH für Sicherheit!
        if not verify_signature(request.data, WEBHOOK_SECRET, signature):
            abort(403, description="Invalid signature") # Zugriff verweigern

        event = request.headers.get('X-GitHub-Event', 'ping')
        print(f"Received event: {event}") # Logging

        if event == 'ping':
            print("Received ping event.")
            return 'pong'
        elif event == 'push':
            payload = request.json
            ref = payload.get('ref', '')
            print(f"Received push event for ref: {ref}")
            # Nur bei Push zum main-Branch auslösen
            if ref == 'refs/heads/main':
                print("Push event to main branch detected. Running deployment script...")
                try:
                    # Führe das Deployment-Skript aus
                    # Timeout hinzufügen, falls Skript hängt
                    result = subprocess.run(
                        ['bash', DEPLOY_SCRIPT_PATH],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=120 # Timeout nach 2 Minuten
                    )
                    print("Deployment script executed successfully.")
                    print(f"Stdout:\n{result.stdout}")
                    print(f"Stderr:\n{result.stderr}") # Auch stderr loggen
                    return 'Deployment triggered successfully', 200
                except subprocess.CalledProcessError as e:
                    print(f"ERROR: Deployment script failed with exit code {e.returncode}")
                    print(f"Stderr:\n{e.stderr}")
                    print(f"Stdout:\n{e.stdout}")
                    # GitHub über Fehler informieren (wird als fehlerhafter Hook angezeigt)
                    abort(500, description=f"Deployment script failed: {e.stderr[:1000]}") # Gekürzte Fehlermeldung
                except subprocess.TimeoutExpired as e:
                    print(f"ERROR: Deployment script timed out after {e.timeout} seconds.")
                    print(f"Stderr:\n{e.stderr}")
                    print(f"Stdout:\n{e.stdout}")
                    abort(500, description="Deployment script timed out.")
                except Exception as e:
                    print(f"ERROR: An unexpected error occurred: {e}")
                    abort(500, description=f"An unexpected error occurred: {e}")
            else:
                print(f"Ignoring push event for non-main branch: {ref}")
                return 'Ignoring push event for non-main branch', 200
        else:
            print(f"Unhandled event type: {event}")
            return 'Unhandled event', 400

if __name__ == '__main__':
        if not WEBHOOK_SECRET:
            print("FATAL ERROR: GITHUB_WEBHOOK_SECRET is not set. Webhook receiver cannot start securely.")
             # Beenden oder unsicheren Modus vermeiden
        exit(1)
        print("Starting webhook receiver on port 9001...")
         # Lausche auf allen Interfaces, Port 9001
        app.run(host='0.0.0.0', port=9001, debug=False) # Debug=False für Produktion 