import sys
import os
import json
from google import genai
from google.genai import types

# Integración con AntigravityConfig
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
try:
    from antigravity_config import AntigravityConfig
    DEFAULT_MODEL = AntigravityConfig.GEMINI_FLASH_MODEL
    FALLBACK_FLASH = AntigravityConfig.FALLBACK_FLASH_MODELS
except Exception:
    DEFAULT_MODEL = "gemini-3.7-flash"
    FALLBACK_FLASH = ["gemini-3.7-flash", "gemini-3.6-flash"]

class DiagnosticTutorAgent:
    """
    Agente Tutor Diagnóstico Inteligente para feedback formativo en tiempo real (ECOE).
    Optimizado con Gemini 3.7 Flash.
    """
    def __init__(self, api_key=None, model_name=DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY="):
                            self.api_key = line.strip().split("=", 1)[1].strip('"').strip("'")
                            break
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.fallback_models = FALLBACK_FLASH

    def provide_guidance(self, case_info: dict, chat_history: list) -> str:
        prompt = f"""
        Eres un Tutor Clínico Docente. Revisa la interacción alumno-paciente y entrega una pista pedagógica o retroalimentación formativa breve sin revelar el diagnóstico directamente:
        
        CASO CLÍNICO:
        {json.dumps(case_info, ensure_ascii=False, indent=2)}
        
        HISTORIAL DE CONSULTA:
        {json.dumps(chat_history[-6:], ensure_ascii=False, indent=2)}
        
        Entrega un comentario pedagógico conciso (máximo 2 párrafos).
        """
        for model in self.fallback_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                if response and response.text:
                    return response.text.strip()
            except Exception:
                continue
        return "Continúa explorando la anamnesis remota y los signos de alarma."
