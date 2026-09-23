from google import genai
from google.genai import errors

from app.core.config import settings
from app.core.constants import SYSTEM_PROMPT
from app.exceptions import GeminiServiceError


def answer_question(schema: str, history: list[dict], question: str) -> str:
    if not settings.gemini_api_key:
        raise GeminiServiceError("GEMINI_API_KEY is missing. Add it to .env and restart the server.")
    conversation = "\n".join(f"{item['role'].title()}: {item['content']}" for item in history[-12:])
    prompt = f"{SYSTEM_PROMPT}\n\n{schema}\n\nConversation:\n{conversation}\n\nUser: {question}"
    client = genai.Client(api_key=settings.gemini_api_key)
    model_names = (settings.gemini_model_name,) + tuple(
        name for name in settings.gemini_fallback_models if name != settings.gemini_model_name
    )
    try:
        for model_name in model_names:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                return response.text or "Gemini returned an empty response."
            except errors.ServerError:
                # A second, configured model can be less congested. Do not fall back
                # for client errors; those require correcting configuration or the key.
                continue
        raise GeminiServiceError("Gemini is temporarily unavailable (503) on every configured model. Please try again shortly.")
    except errors.ClientError as error:
        raise GeminiServiceError(f"Gemini request was rejected: {error.message}") from error
    except errors.APIError as error:
        raise GeminiServiceError(f"Gemini API error: {error}") from error
