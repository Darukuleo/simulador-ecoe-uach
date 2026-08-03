import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class OSCEEvaluationReport(BaseModel):
    score_anamnesis: float = Field(description="Puntaje de Anamnesis (0 a 20)")
    score_physical_exam: float = Field(description="Puntaje de Examen Físico (0 a 20)")
    score_diagnostic_tests: float = Field(description="Puntaje de Exámenes Solicitados (0 a 20)")
    score_diagnosis_accuracy: float = Field(description="Puntaje de Precisión Diagnóstica (0 a 20)")
    score_clinical_management: float = Field(description="Puntaje de Conducta Táctica y Manejo (0 a 20)")
    total_score_percentage: float = Field(description="Puntaje Total Global (0 a 100%)")
    qualitative_feedback: str = Field(description="Feedback pedagógico detallado con aciertos, omisiones críticas y recomendación docente UACh")

class OSCEEvaluatorAgent:
    """
    Agente Tutor / Evaluador Docente UACh de Estaciones ECOE/OSCE.
    Audita la transcripción de la consulta médica realizada por el interno y asigna la rúbrica oficial.
    """
    def __init__(self, api_key=None, model_name="gemini-flash-latest"):
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        self.model_name = model_name

    def evaluate_simulation(self, ground_truth: dict, chat_history: list) -> dict:
        prompt = f"""
        Eres un Profesor de Medicina de la Universidad Austral de Chile y Evaluador Oficial de Estaciones ECOE (OSCE).
        Tu tarea es calificar con rigor académico la interacción de un interno de medicina con un Paciente Simulado.

        VERDAD DE TERRENO Y PAUTA OFICIAL DEL CASO (GROUND TRUTH):
        - Diagnóstico Indiscutible: {ground_truth.get('diagnostico_correcto', '')}
        - Anamnesis Esperada: {ground_truth.get('anamnesis_esperada', '')}
        - Examen Físico Requerido: {ground_truth.get('examen_fisico_esperado', '')}
        - Exámenes Indispensables: {ground_truth.get('examenes_indispensables', '')}
        - Manejo y Tratamiento Correcto: {ground_truth.get('conducta_correcta', '')}

        TRANSCRIPCIÓN COMPLETA DE LA CONSULTA DEL ALUMNO:
        {json.dumps(chat_history, ensure_ascii=False, indent=2)}

        Evalúa y asigna el puntaje en cada una de las 5 dimensiones (0 a 20 puntos cada una) y calcula el total de 0 a 100%. Redacta un feedback docente constructivo.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=OSCEEvaluationReport,
                    temperature=0.1
                )
            )
            
            if response.parsed:
                report = response.parsed
            else:
                data = json.loads(response.text)
                report = OSCEEvaluationReport(**data)
                
            return report.model_dump() if hasattr(report, "model_dump") else report.dict()
        except Exception as e:
            return {
                "score_anamnesis": 15.0,
                "score_physical_exam": 15.0,
                "score_diagnostic_tests": 15.0,
                "score_diagnosis_accuracy": 15.0,
                "score_clinical_management": 15.0,
                "total_score_percentage": 75.0,
                "qualitative_feedback": f"Evaluación por defecto (Error en IA de Evaluación: {str(e)})."
            }
