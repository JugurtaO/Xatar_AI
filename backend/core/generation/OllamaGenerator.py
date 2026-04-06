from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import os, re, json

ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

# On enrichit la structure JSON pour inclure les citations
class AIResponse(BaseModel):
    summary: str = Field(description="Résumé de la question")
    response: str = Field(description="Réponse basée UNIQUEMENT sur les extraits")
    citations: list = Field(description="Liste des sources utilisées (ex: ['doc1.pdf, p.2'])")

json_parser = JsonOutputParser(pydantic_object=AIResponse)
llama_llm = OllamaLLM(
    base_url=ollama_url,
    model="llama3.2:1b",
    temperature=0.1,
    num_thread=8,
    num_ctx=2048,
    num_predict=400
    ) # Température basse pour plus de fidélité
mistral_llm = OllamaLLM(
    base_url="http://localhost:11434",
    model="mistral", 
    temperature=0.1,
    num_thread=8,
    num_ctx=2048,
    num_predict=400
    )

# Template spécial RAG
rag_template = PromptTemplate(
    template="""
SYSTEM:
Tu es Xatar AI, un assistant expert en analyse de documents.
Utilise les extraits fournis pour répondre de manière complète et structurée.
Tu es un robot d'extraction de données STRICT. 
Ta mission est de répondre à la question UNIQUEMENT en utilisant les EXTRAITS fournis ci-dessous.

RÈGLES CRITIQUES :
1. Si l'information n'est pas explicitement écrite dans les EXTRAITS, réponds : "Désolé, cette information n'est pas présente dans le document."
2. Interdiction d'utiliser tes connaissances personnelles sur l'histoire ou le monde.
3. Ne mentionne pas de faits, de dates ou de noms qui ne figurent pas dans le texte reçu.
4. Réponds UNIQUEMENT au format JSON.
Ne commence jamais ta réponse par un tiret, une introduction ou une phrase de politesse.

EXTRAITS DE DOCUMENTS:
{context}

FORMAT DE RÉPONSE:
{format_prompt}

USER QUESTION:
{user_prompt}

ASSISTANT:
""",
    input_variables=["context", "format_prompt", "user_prompt"]
)

def get_rag_response(model, user_prompt, context_text):
    print("INSIDE GET_RAG_RESPONSE")
    if not context_text:
        return {
            "summary": "Aucun document trouvé",
            "response": "Désolé, je n'ai trouvé aucune information dans les documents pour répondre à votre question.",
            "citations": []
    }
    print("--- CONTENU ENVOYÉ AU LLM ---")
    print(context_text)
    print("--------------------------------------------------------------")
    chain = rag_template | model 
    raw_output= chain.invoke({
        "context": context_text,
        "user_prompt": user_prompt,
        "format_prompt": json_parser.get_format_instructions()
    })
    try:
        # Tentative de parsing standard
        return json_parser.parse(raw_output)
    except Exception:
        # SECOURS : On cherche le premier '{' et le dernier '}' pour extraire le JSON pur
        try:
            match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if match:
                clean_json = match.group(0)
                return json.loads(clean_json)
            raise ValueError("Aucun JSON trouvé dans la réponse")
        except Exception as e:
            print(f"Erreur fatale de parsing : {raw_output}")
            return {
                "summary": "Erreur de formatage",
                "response": raw_output, # On renvoie au moins le texte brut
                "citations": []
            }

def llama_response(user_prompt, context_text):
    print("INSIDE LLAM_RESPONSE")
    return get_rag_response(llama_llm, user_prompt, context_text)

def mistral_response(user_prompt, context_text):
    return get_rag_response(mistral_llm,user_prompt,context_text)
