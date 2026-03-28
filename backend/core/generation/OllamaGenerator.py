from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# =========================
# JSON output structure
# =========================

class AIResponse(BaseModel):
    summary: str = Field(description="Summary of the user's message")
    sentiment: int = Field(description="Sentiment score from 0 (negative) to 100 (positive)")
    response: str = Field(description="Suggested response to the user")

json_parser = JsonOutputParser(pydantic_object=AIResponse)

# =========================
# Models (LOCAL)
# =========================

llama_llm = Ollama(model="llama3")
mistral_llm = Ollama(model="mistral")


# =========================
# Prompt templates
# =========================

base_template = PromptTemplate(
    template="""
SYSTEM:
{system_prompt}

FORMAT:
{format_prompt}

USER:
{user_prompt}

ASSISTANT:
""",
    input_variables=["system_prompt", "format_prompt", "user_prompt"]
)

# =========================
# Chain executor
# =========================

def get_ai_response(model, system_prompt, user_prompt):
    chain = base_template | model | json_parser
    return chain.invoke({
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "format_prompt": json_parser.get_format_instructions()
    })

# =========================
# Model-specific functions
# =========================

def llama_response(system_prompt, user_prompt):
    return get_ai_response(llama_llm, system_prompt, user_prompt)

def mistral_response(system_prompt, user_prompt):
    return get_ai_response(mistral_llm, system_prompt, user_prompt)


