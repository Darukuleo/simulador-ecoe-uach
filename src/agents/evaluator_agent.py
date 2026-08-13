import os
import json
import time
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
    critical_errors_missed: list[str] = Field(description="Lista de RED FLAGS o errores críticos que el alumno cometió (ej. no preguntar alergias, obviar un signo vital de shock)")
    clinical_reasoning_assessment: str = Field(description="Evaluación cualitativa del razonamiento clínico. ¿Por qué falló o acertó?")
    qualitative_feedback: str = Field(description="Feedback pedagógico detallado con aciertos, omisiones críticas y recomendación docente UACh final")

class OSCEEvaluatorAgent:
    """
    Agente Tutor / Evaluador Docente UACh de Estaciones ECOE/OSCE.
    OPTIMIZADO PARA RIGOR (Gemini Pro).
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._client = None
        # Usamos PRO si está disponible, sino usamos FLASH (que sabemos que funciona)
        self.fallback_models = ["gemini-3.6-pro", "gemini-3.6-flash", "gemini-3.5-flash"]

    @property
    def client(self):
        if self._client is None:
            self.api_key = self.api_key or os.environ.get("GEMINI_API_KEY")
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
        return self._client

    def evaluate_simulation(self, ground_truth: dict, chat_history: list) -> dict:
        prompt = f"""
        Eres un Profesor Titular de Medicina de la Universidad Austral de Chile y Evaluador Oficial de Estaciones ECOE (OSCE).
        Tu tarea es calificar con EXTREMO RIGOR ACADÉMICO la interacción de un interno de medicina con un Paciente Simulado.

        VERDAD DE TERRENO Y PAUTA OFICIAL DEL CASO (GROUND TRUTH):
        - Diagnóstico Indiscutible: {ground_truth.get('diagnostico_correcto', '')}
        - Anamnesis Esperada: {ground_truth.get('anamnesis_esperada', '')}
        - Examen Físico Requerido: {ground_truth.get('examen_fisico_esperado', '')}
        - Exámenes Indispensables: {ground_truth.get('examenes_indispensables', '')}
        - Manejo y Tratamiento Correcto: {ground_truth.get('conducta_correcta', '')}

        TRANSCRIPCIÓN COMPLETA DE LA CONSULTA DEL ALUMNO:
        {json.dumps(chat_history, ensure_ascii=False, indent=2)}

        INSTRUCCIONES:
        1. Eres inclemente con los errores de seguridad del paciente. Si olvida alergias, no toma signos vitales en un paciente grave, o receta mal, debes incluirlo en `critical_errors_missed`.
        2. Asigna puntajes de 0 a 20 de manera realista. Un alumno promedio saca 14, uno excelente 18.
        3. Detalla en `clinical_reasoning_assessment` qué sesgo cognitivo o fallo tuvo el alumno.
        4. REGLA CONSTITUCIONAL (INTEGRIDAD CLÍNICA): Si la transcripción está vacía, manifiestamente incompleta o es incomprensible, NO alucines un puntaje. Debes incluir obligatoriamente el tag "[REQUIERE ACLARACIÓN CLÍNICA]" en tu `qualitative_feedback` y evaluar con puntaje 0.
        """
        
        last_error = ""
        for model in self.fallback_models:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=OSCEEvaluationReport,
                        )
                    )
                    
                    if response.parsed:
                        report = response.parsed
                    else:
                        data = json.loads(response.text)
                        report = OSCEEvaluationReport(**data)
                        
                    return report.model_dump() if hasattr(report, "model_dump") else report.dict()
                except Exception as e:
                    last_error = str(e)
                    time.sleep(0.5)
                    
        return {
            "score_anamnesis": 0.0,
            "score_physical_exam": 0.0,
            "score_diagnostic_tests": 0.0,
            "score_diagnosis_accuracy": 0.0,
            "score_clinical_management": 0.0,
            "total_score_percentage": 0.0,
            "critical_errors_missed": ["Error del sistema al evaluar"],
            "clinical_reasoning_assessment": "No se pudo completar.",
            "qualitative_feedback": f"Error del sistema evaluador: {last_error}"
        }
