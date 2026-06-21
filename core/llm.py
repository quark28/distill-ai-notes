import os
from dotenv import load_dotenv
from mistralai.client import Mistral
from .compressor import custom_compressor 

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None

SYSTEM_PROMPT = """Ты — умный RAG-ассистент. 
Отвечай на вопросы пользователя, используя ТОЛЬКО предоставленный контекст. 
Если в контексте нет информации для ответа, прямо скажи об этом."""

def ask_llm(query: str, raw_context_list: list[str]) -> str:
    if not raw_context_list:
        return "В базе нет подходящей информации."

    compressed_chunks = [custom_compressor(chunk) for chunk in raw_context_list]
    context_str = "\n\n".join(compressed_chunks)
    
    prompt = f"""
    Контекст:
    {context_str}
    
    Вопрос: {query}
    """
    
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        usage = response.usage
        print(f"[LLM LOG] Вход: {usage.prompt_tokens} | Выход: {usage.completion_tokens}")
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка LLM: {e}"