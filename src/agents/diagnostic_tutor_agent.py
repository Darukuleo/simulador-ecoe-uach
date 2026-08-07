import os
import json
from google import genai

class DiagnosticTutorAgent:
    """
    Agente Tutor Diagnóstico para asistencia y feedback clínico.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def provide_guidance(self, case_info: dict, chat_history: list) -> str:
        return "Tutor clínico activo."
