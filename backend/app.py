from flask import Flask, request, jsonify, render_template
from core.generation.OllamaGenerator import llama_response, mistral_response
from core.ingestion.process_pdf_with_status import process_pdf_with_status
import time

app = Flask(__name__,template_folder='../frontend/templates',static_folder='../frontend/static')

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
    file = request.files['file']
    path = save_file(file)

    # On définit un  générateur interne qui "consomme" le service
    def stream_updates():
        # On boucle sur ce que le service renvoie (ses yield)
        for message in process_pdf_with_status(path):
            # On formate pour le protocole SSE
            yield f"data: {message}\n\n"

    # On donne ce flux à la réponse
    return Response(stream_updates(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)