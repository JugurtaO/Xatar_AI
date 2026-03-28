import os, uuid
from flask import Flask, request, jsonify, render_template, Response
from werkzeug.utils import secure_filename
from backend.database.db import get_vector_db
from backend.core.generation.OllamaGenerator import llama_response, mistral_response
from backend.core.ingestion.process_pdf_with_status import process_pdf_with_status
import time

app = Flask(__name__,template_folder='frontend/templates',static_folder='frontend/static')

# Configuration du dossier d'upload (Minio sera l'étape d'après, restons simple pour tester le SSE)
UPLOAD_FOLDER = 'backend/data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

with app.app_context():
    try:
        get_vector_db() # On force la première connexion ici
        print("🚀 Serveur Flask prêt et connecté à ChromaDB")
    except Exception as e:
        print(f"❌ Impossible de joindre ChromaDB au démarrage : {e}")

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    user_message = data.get('message')
    model = data.get('model')
    #pdfs= si l'utilisatur décide d'en choisir certains  pour le LLM - TODO 
   
    if not user_message or not model:
        return jsonify({"error": "Missing message or model selection"}), 400
   
    system_prompt = "You are an AI assistant helping with customer inquiries. Provide a helpful and concise response."
   
    start_time = time.time()
   
    try:
        if model == 'llama':
            result = llama_response(system_prompt, user_message) #fonction à adpater 
        elif model == 'mistral':
            result = mistral_response(system_prompt, user_message)  #fonction à adpater 
        else:
            return jsonify({"error": "Invalid model selection"}), 400
       
        result['duration'] = time.time() - start_time
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ingest', methods=['POST'])
def ingest():
    if 'file' not in request.files:
        return "error:Aucun fichier reçu", 400
    
    file = request.files['file']
    if file.filename == '':
        return "error:Nom de fichier vide", 400

    unique_id = str(uuid.uuid4())[:8]
    filename = f"{unique_id}_{secure_filename(file.filename)}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    
    def stream_updates():
        try:
            # On consomme le générateur de ton service ingestion
            # process_pdf_with_status doit 'yielder' des chaînes comme "extracting:10"
            for status_message in process_pdf_with_status(path):
                yield f"data: {status_message}\n\n"
            
            # Message final pour dire au JS de passer en 'ready'
            yield "data: done:100\n\n"
        except Exception as e:
            yield f"data: error:{str(e)}\n\n"

    return Response(stream_updates(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)