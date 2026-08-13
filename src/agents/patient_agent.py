import os
import json
import time
from google import genai

class StandardizedPatientAgent:
    """
    Agente Paciente Simulado Estandarizado (ECOE/OSCE).
    Responde en primera persona al interno de medicina de forma clínicamente coherente, realista y detallada.
    OPTIMIZADO PARA VELOCIDAD (Gemini Flash) Y RESPUESTAS CORTAS.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._client = None
        # Solo usamos FLASH para garantizar latencia mínima en chat en vivo
        import sys
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if root_dir not in sys.path:
            sys.path.append(root_dir)
        from antigravity_config import AntigravityConfig
        self.fallback_models = AntigravityConfig.FALLBACK_FLASH_MODELS

    @property
    def client(self):
        if self._client is None:
            self.api_key = self.api_key or os.environ.get("GEMINI_API_KEY")
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
        return self._client

    def respond_to_student(self, ground_truth: dict, chat_history: list, user_message: str) -> str:
        prompt = f"""
        Eres un Paciente Estandarizado en una Estación de Examen Clínico Objetivo Estructurado (ECOE).
        Estás siendo atendido por un interno de medicina.

        INFORMACIÓN SECRETA DE TU CASO (GROUND TRUTH):
        - Nombre y Edad: {ground_truth.get('paciente_nombre', 'Juan Pérez')}, {ground_truth.get('edad', '55')} años.
        - Motivo de Consulta Real: {ground_truth.get('motivo_consulta', 'Dolor abdominal')}
        - Historia de la Enfermedad Actual: {ground_truth.get('historia_clinica', '')}
        - Antecedentes Médicos y Quirúrgicos: {ground_truth.get('antecedentes', '')}
        - Hallazgos al Examen Físico: {ground_truth.get('examen_fisico', '')}

        REGLAS DE ACTUACIÓN (MUY ESTRICTAS):
        1. RESTRICCIÓN FÍSICA: Si tu condición es grave (ej. dolor agudo, shock), tus respuestas DEBEN ser cortadas, con quejidos o desorientadas.
        2. OCULTAMIENTO ACTIVO: JAMÁS reveles un síntoma clave o un antecedente si el médico no te pregunta específicamente por ello. Gánate la información.
        3. SI TE EXAMINAN: Si el alumno escribe explícitamente "Voy a examinar su abdomen" o similar, revélale de forma narrativa lo que siente (ej. "¡Ay, me dolió mucho cuando soltó la mano!").
        4. LONGITUD: Tus respuestas DEBEN ser MUY CORTAS. Máximo 2 o 3 oraciones cortas. (Para acelerar el tiempo de síntesis de voz).

        HISTORIAL RECIENTE:
        {json.dumps(chat_history[-6:], ensure_ascii=False, indent=2)}

        MÉDICO:
        "{user_message}"

        Responde como el paciente (recuerda: conciso y actuando tu estado físico):
        """
        
        for model in self.fallback_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                time.sleep(0.5)
                continue
                
        return f"Doctor(a), me siento mal. Disculpe, ¿me podría repetir lo que me dijo?"

    def respond_to_student_stream(self, ground_truth: dict, chat_history: list, user_message: str):
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
        2. Proporciona respuestas naturales, expresivas y clínicamente completas. Expresa tus inquietudes, temor o dolor con realismo.
        3. No uses lenguaje médico técnico avanzado a menos que el paciente lo sepa por su antecedente.
        4. Revela de forma fluida y colaborativa la información que el estudiante pregunte en la anamnesis.
        5. Si el estudiante dice que va a realizar un examen físico o solicita un laboratorio/TAC, proporciónale de forma objetiva y detallada los hallazgos descritos en el secreto del caso.
        6. Mantén la coherencia emocional adecuada a la patología.

        HISTORIAL DE LA CONSULTA HASTA AHORA:
        {json.dumps(chat_history[-6:], ensure_ascii=False, indent=2)}

        MENSAJE ACTUAL DEL ESTUDIANTE:
        "{user_message}"

        Responde como el paciente:
        """
        
        import time
        for model in self.fallback_models:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content_stream(
                        model=model,
                        contents=prompt
                    )
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                    return
                except Exception as e:
                    time.sleep(0.5)
                    
        yield f"Doctor(a), me siento mal por mi dolencia. Disculpe, ¿me podría repetir lo que me dijo?"
