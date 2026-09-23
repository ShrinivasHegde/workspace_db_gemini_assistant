from google import genai
from google.genai import errors, types

from app.core.config import settings
from app.core.constants import SYSTEM_PROMPT
from app.exceptions import GeminiServiceError


def answer_question(schema: str, history: list[dict], question: str) -> str:
    if not settings.gemini_api_key:
        raise GeminiServiceError("GEMINI_API_KEY is missing. Add it to .env and restart the server.")
    
    # Format conversation history
    conversation = "\n".join(f"{item['role'].title()}: {item['content']}" for item in history[-12:])
    
    # User prompt containing database context and conversation history
    prompt = f"Database Schema & Metadata:\n{schema}\n\nRecent Conversation History:\n{conversation}\n\nUser Question:\n{question}"
    
    client = genai.Client(api_key=settings.gemini_api_key)
    
    # Configure generation parameters to allow long, detailed responses
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=8192,  # Ensures long responses are not cut off
        temperature=0.2,          # Keeps technical/SQL answers accurate and focused
    )
    
    model_names = (settings.gemini_model_name,) + tuple(
        name for name in settings.gemini_fallback_models if name != settings.gemini_model_name
    )
    
    try:
        for model_name in model_names:
            try:
                response = client.models.generate_content(
                    model=model_name, 
                    contents=prompt,
                    config=config
                )
                return response.text or "Gemini returned an empty response."
            except errors.ServerError:
                # Fall back to alternative models if the primary model is busy/congested
                continue
                
        raise GeminiServiceError("Gemini is temporarily unavailable (503) on every configured model. Please try again shortly.")
        
    except errors.ClientError as error:
        raise GeminiServiceError(f"Gemini request was rejected: {error.message}") from error
    except errors.APIError as error:
        raise GeminiServiceError(f"Gemini API error: {error}") from error