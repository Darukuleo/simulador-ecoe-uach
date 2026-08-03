import os
import json
import time
from google import genai

class StandardizedPatientAgent:
    """
    Agente Paciente Simulado Estandarizado (ECOE/OSCE).
    Responde en primera persona al interno de medicina de forma clínicamente coherente y realista.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.fallback_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]

    def respond_to_student(self, ground_truth: dict, chat_history: list, user_message: str) -> str:
        prompt = f"""
        Eres un Paciente Estandarizado en una Estación de Examen Clínico Objetivo Estructurado (ECOE).
        Estás siendo atendido por un interno de medicina.

        INFORMACIÓN SECRETA DE TU CASO (GROUND TRUTH):
        - Nombre y Edad: {ground_truth.get('paciente_nombre', 'Juan Pérez')}, {ground_truth.get('edad', '55')} años.
        - Motivo de Consulta Real: {ground_truth.get('motivo_consulta', 'Dolor abdominal')}
        - Historia de la Enfermedad Actual: {ground_truth.get('historia_clinica', '')}
        - Antecedentes Médicos y Quirúrgicos: {ground_truth.get('antecedentes', '')}
        - Hallazgos al Examen Físico (solo revelar si el médico dice 'Le examino el abdomen', 'Tomo presión', etc.): {ground_truth.get('examen_fisico', '')}
        - Exámenes de Laboratorio e Imágenes (solo revelar si el médico los solicita explícitamente): {ground_truth.get('examenes_laboratorio_imagenes', '')}

        REGLAS DE ACTUACIÓN:
        1. Habla en primera persona, como un paciente real en la consulta médica.
        2. No uses lenguaje médico técnico avanzado a menos que el paciente lo sepa por su antecedente.
        3. Revela solo la información que el estudiante pregunte específicamente en la anamnesis.
        4. Si el estudiante dice que va a realizar un examen físico o solicita un laboratorio/TAC, proporciónale de forma objetiva los hallazgos descritos en el secreto del caso.
        5. Mantén la coherencia emocional (preocupación, dolor o ansiedad moderada).

        HISTORIAL DE LA CONSULTA HASTA AHORA:
        {json.dumps(chat_history[-6:], ensure_ascii=False, indent=2)}

        MENSAJE ACTUAL DEL ESTUDIANTE:
        "{user_message}"

        Responde como el paciente:
        """
        
        last_error = ""
        for model in self.fallback_models:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    last_error = str(e)
                    time.sleep(0.5)
                    
        return f"Doctor(a), me siento muy mal por mi dolor. Disculpe, ¿me podría repetir lo que dijo? (Reintento automático por congestión de servidor)."
