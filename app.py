import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from google import genai
from google.genai import types
import hashlib
import streamlit.components.v1 as components
import os
import sys
import json
import time
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

from database import (
    insert_caso_ecoe, get_casos_ecoe, insert_sesion_simulacion, insert_evaluacion, 
    get_evaluaciones_por_alumno, get_todas_evaluaciones, get_config_examen, update_config_examen,
    insert_encuesta_investigacion, get_todas_encuestas, export_all_data_json, import_all_data_json,
    calcular_nota_chile, append_permanent_log
)
from agents.patient_agent import StandardizedPatientAgent
from agents.evaluator_agent import OSCEEvaluatorAgent
try:
    from agents.voice_realism_studio import VoiceRealismStudio
except Exception:
    class VoiceRealismStudio:
        EMOTION_PROFILES = {}
from agents.diagnostic_tutor_agent import DiagnosticTutorAgent

st.set_page_config(
    page_title="Examen ECOE Virtual - UACh", 
    page_icon="🏥", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "logo_uach.png"))
PERMANENT_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "registros_permanentes.json"))

# CLAVE DE ACCESO DOCENTE
DOCENTE_PIN = os.environ.get("DOCENTE_PIN", "uach2026")

# DISEÑO EXPERTO EN DOCENCIA MÉDICA Y GARANTÍA DE BARRA LATERAL VISIBLE
st.markdown("""
    <style>
    .stApp {
        background-color: #F4F1EA !important;
        color: #0F172A !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }
    
    p, span, label, div, h1, h2, h3, h4, h5, h6, li {
        color: #0F172A !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #EAE5D9 !important;
        border-right: 2px solid #D6CEBE !important;
    }
    
    /* Garantizar que el botón de expandir/contraer la barra lateral SIEMPRE sea visible */
    [data-testid="stSidebarCollapseButton"], 
    [data-testid="stSidebarExpandButton"], 
    button[aria-label*="sidebar"], 
    button[aria-label*="Sidebar"],
    [data-testid="stHeader"] button {
        display: inline-flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        color: #1B365D !important;
    }
    
    div[data-testid="stRadio"] label {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        background-color: #E2DCCF !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        border: 1px solid #C4BAA9 !important;
    }
    
    h1, h2, h3, h4 {
        color: #1B365D !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stCaptionContainer"] p {
        color: #334155 !important;
        font-weight: 600 !important;
    }
    
    div.stAlert {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
        border-left: 6px solid #1B365D !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }
    div.stAlert p {
        color: #0F172A !important;
        font-size: 1.02rem !important;
    }
    
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stChatMessage"] p {
        color: #0F172A !important;
        font-size: 1.05rem !important;
        line-height: 1.5 !important;
    }
    
    .stButton>button {
        background-color: #1B365D !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        padding: 10px 20px !important;
        box-shadow: 0 2px 6px rgba(27, 54, 93, 0.2) !important;
    }
    .stButton>button p {
        color: #FFFFFF !important;
    }
    .stButton>button:hover {
        background-color: #0F2342 !important;
        box-shadow: 0 4px 12px rgba(15, 35, 66, 0.3) !important;
    }
    
    input, textarea {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #94A3B8 !important;
        border-radius: 6px !important;
        font-size: 1rem !important;
    }
    
    button[data-baseweb="tab"] p {
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        color: #1B365D !important;
    }
    
    .stExpander {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    
    /* Ocultar únicamente íconos de GitHub/Share/Edit */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    #MainMenu {
        display: none !important;
    }
    footer {
        display: none !important;
    }
    header button[title*="GitHub"], 
    header button[title*="Share"], 
    header a[href*="github.com"] {
        display: none !important;
    }
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

existing_cases = get_casos_ecoe()
if len(existing_cases) != 7:
    from src.importer import import_all_stations
    import_all_stations()
    existing_cases = get_casos_ecoe()

# INICIALIZACIÓN COMPLETA Y SEGURA DE SESSION_STATE
keys_defaults = {
    "chat_history": [],
    "patient_agent": None,
    "evaluator_agent": None,
    "last_evaluation": None,
    "station_start_time": None,
    "enable_tts": True,
    "docente_autenticado": False,
    "showing_inter_station_feedback": False,
    "last_station_feedback": None,
    "showing_survey": False,
    "survey_completed": False,
    "override_mode": None,
    "circuit_active": False,
    "circuit_current_index": 0,
    "circuit_student_name": "",
    "circuit_results": []
}
for key, val in keys_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def transcribe_audio_gemini(audio_bytes):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: API Key no encontrada."
        
    client = genai.Client(api_key=api_key)
    prompt = "Transcribe exactamente lo que dice este audio en español. No agregues nada más que la transcripción literal, no inventes texto."
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav'),
                prompt
            ]
        )
        return response.text.strip()
    except Exception as e:
        return f"Error al transcribir: {e}"


def render_voice_input_widget():
    st.caption("🎙️ **Control de Voz:** Puedes presionar el micrófono para hablarle al paciente o escribir abajo.")
    voice_html = """
    <div style="background-color: #E2E8F0; padding: 12px; border-radius: 8px; border: 1.5px solid #CBD5E1; text-align: center; margin-bottom: 10px;">
        <button id="micBtn" style="background-color: #DC2626; color: white; border: none; padding: 10px 18px; font-weight: bold; border-radius: 6px; cursor: pointer; font-size: 0.95rem;">
            🎙️ Hablar al Paciente (Presionar para Dictar)
        </button>
        <span id="statusTxt" style="margin-left: 10px; font-weight: 600; color: #1E293B;">Micrófono Listo.</span>
    </div>
    <script>
        const btn = document.getElementById('micBtn');
        const statusTxt = document.getElementById('statusTxt');
        
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.lang = 'es-CL';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            let isListening = false;
            
            btn.onclick = function() {
                if (!isListening) {
                    recognition.start();
                    isListening = true;
                    btn.style.backgroundColor = '#059669';
                    btn.innerHTML = '🔴 Escuchando... (Habla ahora)';
                    statusTxt.innerText = 'Escuchando tu voz...';
                } else {
                    recognition.stop();
                    isListening = false;
                    btn.style.backgroundColor = '#DC2626';
                    btn.innerHTML = '🎙️ Hablar al Paciente (Presionar para Dictar)';
                    statusTxt.innerText = 'Detenido.';
                }
            };
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                statusTxt.innerText = 'Enviando voz: "' + transcript + '"...';
                
                const chatInput = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (chatInput) {
                    // Seteo nativo para activar el estado de React en Streamlit
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    nativeInputValueSetter.call(chatInput, transcript);
                    chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                    chatInput.focus();
                    
                    // Simular envío automático (Enter)
                    setTimeout(() => {
                        const sendBtn = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                        if (sendBtn) {
                            sendBtn.click();
                        } else {
                            chatInput.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: true, keyCode: 13, key: 'Enter' }));
                        }
                    }, 300);
                }
                
                btn.style.backgroundColor = '#DC2626';
                btn.innerHTML = '🎙️ Hablar al Paciente (Presionar para Dictar)';
                isListening = false;
            };
            
            recognition.onerror = function(event) {
                statusTxt.innerText = 'Error de micrófono: ' + event.error;
                btn.style.backgroundColor = '#DC2626';
                btn.innerHTML = '🎙️ Hablar al Paciente (Presionar para Dictar)';
                isListening = false;
            };
        } else {
            statusTxt.innerText = 'Tu navegador no soporta reconocimiento por voz directo (Usar Chrome o Edge).';
        }
    </script>
    """
    components.html(voice_html, height=75)


def get_patient_avatar(gt_data):
    nombre = str(gt_data.get('paciente_nombre', '')).lower()
    edad = 50
    try:
        edad = int(gt_data.get('edad', 50))
    except:
        pass
    
    # Heurística simple para sexo basada en el nombre
    nombres_fem = ['maría', 'maria', 'ana', 'rosa', 'carmen', 'julia', 'marta', 'isabel', 'laura', 'paula', 'pía', 'antonia', 'fernanda']
    is_female = False
    for nf in nombres_fem:
        if nf in nombre:
            is_female = True
            break
            
    if edad > 60:
        return "👵" if is_female else "👴"
    elif edad < 15:
        return "👧" if is_female else "👦"
    else:
        return "👩" if is_female else "👨"

def render_patient_tts(text_to_speak, emotion_mode="🔴 Dolor Agudo / Agitado"):
    rate = 1.0
    pitch = 1.0
    prefix = ""
    
    if "Dolor Agudo" in emotion_mode:
        rate = 0.85
        pitch = 1.15
        prefix = "Ay... uff... "
    elif "Anciano" in emotion_mode:
        rate = 0.75
        pitch = 0.85
        prefix = "Mire doctor... "
    elif "Ansioso" in emotion_mode:
        rate = 1.2
        pitch = 1.25
        prefix = "¡Doctor, por favor! "
        
    full_text = prefix + text_to_speak if prefix and not text_to_speak.startswith(prefix.strip()) else text_to_speak
    clean_text = json.dumps(full_text)
    
    tts_html = f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance({clean_text});
            utterance.lang = 'es-CL';
            utterance.rate = {rate};
            utterance.pitch = {pitch};
            window.speechSynthesis.speak(utterance);
        }}
    </script>
    """
    components.html(tts_html, height=0)

# Verificación de Horario y Apertura de Examen (Ajustado a Zona Horaria de Chile America/Santiago)
def is_exam_open_now():
    config = get_config_examen()
    if not config["examen_habilitado"]:
        return False, "El examen ha sido deshabilitado manualmente por el equipo docente."
    
    if config["modo_horario"]:
        try:
            now = datetime.now(ZoneInfo("America/Santiago"))
        except:
            now = datetime.now()
            
        current_time_str = now.strftime("%H:%M")
        
        if config["fecha_examen"]:
            current_date_str = now.strftime("%Y-%m-%d")
            if current_date_str != config["fecha_examen"]:
                return False, f"El examen está programado únicamente para la fecha: {config['fecha_examen']} (Hora actual Chile: {now.strftime('%H:%M')})."
                
        if current_time_str < config["hora_inicio"] or current_time_str > config["hora_fin"]:
            return False, f"El examen solo recibe respuestas entre las {config['hora_inicio']} y las {config['hora_fin']} hrs (Hora actual en Chile: {current_time_str} hrs)."
            
    return True, "Abierto"

# --- BARRA LATERAL CONFIGURACIÓN ---
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    
    st.title("🏥 SIMULADOR ECOE UACh")
    st.caption("Plataforma Oficial de Evaluación y Pacientes Virtuales")
    
    st.markdown("---")
    st.markdown("### 👤 Selecciona Modo de Uso:")
    
    default_role_idx = 0 if st.session_state.override_mode != "docente" else 1
    role_mode = st.radio(
        "Modo de Interfaz:", 
        ["🎓 Modo Interno (Examen Estudiante)", "👨‍🏫 Modo Docente / Administrador"],
        index=default_role_idx
    )
    
    st.markdown("---")
    st.session_state.enable_tts = st.checkbox("🔊 Activar Voz Hablada del Paciente (TTS)", value=st.session_state.enable_tts)
    if st.session_state.enable_tts:
        st.session_state.patient_emotion = st.selectbox(
            "🎭 Perfil Emocional del Paciente (ECOE-Voice-Realism):",
            ["🔴 Dolor Agudo / Agitado", "👴 Anciano / Pausado", "😰 Ansioso / Shock Inicial", "🟢 Tranquilo / Colaborativo"],
            index=0
        )
    else:
        st.session_state.patient_emotion = "🟢 Tranquilo / Colaborativo"
    
    # AUTO-CARGA SEGURA DE API KEY
    secret_key = None
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            secret_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass
    if not secret_key:
        secret_key = os.environ.get("GEMINI_API_KEY")
        
    if secret_key:
        os.environ["GEMINI_API_KEY"] = secret_key
        if not st.session_state.patient_agent:
            st.session_state.patient_agent = StandardizedPatientAgent(api_key=secret_key)
            st.session_state.evaluator_agent = OSCEEvaluatorAgent(api_key=secret_key)
        st.caption("🟢 Servidor IA Conectado y Seguro.")
    else:
        st.caption("🔴 Servidor IA sin conexión.")

    st.markdown("---")
    st.caption("UACh - Facultad de Medicina / Internado de Cirugía")

# BOTÓN DE ACCESO RÁPIDO DOCENTE EN CABECERA DE PÁGINA SI SE REPLIEGA LA BARRA
col_top_a, col_top_b = st.columns([4, 1])
with col_top_b:
    if st.button("🔑 Acceso Docente (PIN)", help="Haz clic para abrir el Panel Docente"):
        st.session_state.override_mode = "docente"
        st.rerun()

# =============================================================================
# MODO INTERNO (EXAMEN Y PACIENTE SIMULADO)
# =============================================================================
if "🎓 Modo Interno" in role_mode and st.session_state.override_mode != "docente":
    c_head1, c_head2 = st.columns([1, 4])
    with c_head1:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)
    with c_head2:
        st.title("🏥 Box de Atención Virtual - Examen ECOE UACh")
        st.caption("Simulación clínica interactiva con Paciente Estandarizado de Inteligencia Artificial.")
    
    exam_open, open_reason = is_exam_open_now()
    
    if not exam_open:
        st.error(f"🔒 **RECEPCIÓN DE EXAMEN CERRADA / FUERA DE HORARIO**")
        st.info(f"📌 **Motivo:** {open_reason}\n\nSi eres docente o evaluador, presiona el botón **🔑 Acceso Docente (PIN)** arriba a la derecha.")
    else:
        exam_type = st.radio("Modalidad de Evaluación:", ["🏆 Circuito Completo de Estaciones", "🔄 Práctica de Estación Individual"], horizontal=True)
        
        casos = get_casos_ecoe()
        
        # --- MODALIDAD A: CIRCUITO COMPLETO DE ESTACIONES ---
        if "Circuito Completo" in exam_type:
            if not st.session_state.get("circuit_active", False) and not bool(st.session_state.get("circuit_results", [])) and not st.session_state.get("showing_inter_station_feedback", False) and not st.session_state.get("showing_survey", False):
                st.info("📌 **Bienvenido al Examen ECOE.** Realizarás las estaciones clínicas consecutivas (7 minutos por estación). Al finalizar el circuito completo, recibirás tu **Informe Oficial de Notas (1.0 a 7.0)** y responderás una breve Encuesta de Investigación Médica.")
                
                c_name, c_btn = st.columns([3, 1])
                with c_name:
                    student_input_name = st.text_input("Ingresa tu Nombre Completo (Interno/a):", value="")
                with c_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🚀 Iniciar Examen ECOE", type="primary"):
                        if not student_input_name.strip():
                            st.error("⚠️ Ingresa tu nombre antes de iniciar el examen.")
                        else:
                            st.session_state.circuit_active = True
                            st.session_state.circuit_current_index = 0
                            st.session_state.circuit_student_name = student_input_name.strip()
                            st.session_state.circuit_results = []
                            st.session_state.chat_history = []
                            st.session_state.station_start_time = time.time()
                            st.session_state.showing_inter_station_feedback = False
                            st.session_state.showing_survey = False
                            st.rerun()

            elif st.session_state.showing_inter_station_feedback:
                st.success("✅ **¡Estación Completada!**")
                fb_item = st.session_state.last_station_feedback
                nota_st = calcular_nota_chile(fb_item['porcentaje'])
                
                st.subheader(f"💡 Resumen Breve de Evaluación: {fb_item['estacion']}")
                st.write(f"Calificación Obtenida en esta Estación: **Nota {nota_st:.1f}** ({fb_item['porcentaje']:.1f}%)")
                st.info(f"**Observaciones del Evaluador:**\n\n{fb_item['feedback']}")
                
                st.markdown("---")
                if st.button("➡️ Avanzar Inmediatamente a la Siguiente Estación ➔", type="primary"):
                    st.session_state.showing_inter_station_feedback = False
                    st.session_state.circuit_active = True
                    st.session_state.chat_history = []
                    st.session_state.station_start_time = time.time()
                    st.rerun()

            elif st.session_state.circuit_active:
                idx = st.session_state.circuit_current_index
                total_st = len(casos)
                
                if idx < total_st:
                    current_caso = casos[idx]
                    gt_data = json.loads(current_caso["ground_truth_json"])
                    
                    col_st1, col_st2 = st.columns([3, 1])
                    with col_st1:
                        st.subheader(f"Estación N° {idx+1} de {total_st}: Box de Atención Virtual")
                        st.caption(f"Interno Evaluado: **{st.session_state.circuit_student_name}**")
                    with col_st2:
                        elapsed = time.time() - st.session_state.station_start_time
                        remaining = max(0, 420 - int(elapsed))
                        mins, secs = divmod(remaining, 60)
                        
                        timer_color = "#DC2626" if remaining <= 60 else "#1B365D"
                        timer_bg = "#FEE2E2" if remaining <= 60 else "#E2E8F0"
                        
                        # CRONÓMETRO FLOTANTE / STICKY SIEMPRE VISIBLE AL HACER SCROLL
                        st.markdown(f"""
                        <div style="
                            position: fixed;
                            top: 15px;
                            right: 25px;
                            z-index: 999999;
                            background-color: {timer_bg};
                            color: {timer_color};
                            border: 2.5px solid {timer_color};
                            padding: 8px 18px;
                            border-radius: 25px;
                            font-weight: 800;
                            font-size: 1.3rem;
                            box-shadow: 0 4px 14px rgba(0,0,0,0.18);
                            backdrop-filter: blur(8px);
                        ">
                            ⏱️ {mins:02d}:{secs:02d}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if remaining <= 60 and remaining > 0:
                            st.error("⚠️ ¡Queda 1 minuto para finalizar la estación!")

                    st.progress((idx + 1) / total_st)
                    
                    st.info(f"📋 **HOJA DE INSTRUCCIONES PARA EL INTERNO (DOOR SHEET):**\n\n* **Ubicación / Contexto:** {gt_data.get('motivo_consulta')}\n* **Paciente:** {gt_data.get('paciente_nombre')}, {gt_data.get('edad', '50')} años.\n* **Tareas:** Realice la anamnesis focalizada, indique si examina al paciente o solicite los exámenes de laboratorio/imágenes necesarios. Indique su manejo táctico inicial.")
                    
                    pat_avatar = get_patient_avatar(gt_data)
                    for msg in st.session_state.chat_history:
                        avatar = "🧑‍⚕️" if msg["role"] == "user" else pat_avatar
                        with st.chat_message(msg["role"], avatar=avatar):
                            st.markdown(msg["content"])

                    render_voice_input_widget()


                    if remaining <= 0:
                        st.error("⏰ ¡Tiempo agotado! Debes finalizar la estación.")
                        user_input = st.chat_input("Tiempo agotado", disabled=True)
                    else:
                        user_input = st.chat_input("Escribe tu pregunta o indicación al paciente (o usa el micrófono arriba)...")
                    
                    if user_input:
                        if not st.session_state.patient_agent:
                            st.error("⚠️ Ingrese su API Key en la barra lateral para conversar.")
                        else:
                            st.session_state.chat_history.append({"role": "user", "content": user_input})
                            
                            with st.chat_message("user", avatar="🧑‍⚕️"):
                                st.markdown(user_input)
                                
                            with st.chat_message("assistant", avatar=pat_avatar):
                                stream = st.session_state.patient_agent.respond_to_student_stream(gt_data, st.session_state.chat_history, user_input)
                                resp = st.write_stream(stream)
                                
                            st.session_state.chat_history.append({"role": "assistant", "content": resp})
                            
                            if st.session_state.enable_tts:
                                render_patient_tts(resp, st.session_state.get('patient_emotion', '🔴 Dolor Agudo / Agitado'))

                    st.markdown("---")
                    
                    if len(st.session_state.chat_history) < 2:
                        st.info("💬 Realiza al menos 1 pregunta al paciente para poder finalizar la estación.")
                        
                    col_b1, col_b2 = st.columns([1, 1])
                    with col_b2:
                        btn_disabled = len(st.session_state.chat_history) < 2
                        if st.button(f"🚪 SALIR DEL BOX Y FINALIZAR (No presionar para conversar)", type="secondary", disabled=btn_disabled, help="Haz clic aquí solo cuando hayas terminado toda tu atención médica."):
                            if not st.session_state.evaluator_agent:
                                st.error("⚠️ Requiere API Key para evaluar.")
                            else:
                                with st.spinner(f"Evaluando Estación {idx+1}..."):
                                    eval_rep = st.session_state.evaluator_agent.evaluate_simulation(gt_data, st.session_state.chat_history)
                                    s_id = insert_sesion_simulacion(current_caso["id"], st.session_state.circuit_student_name, st.session_state.chat_history)
                                    insert_evaluacion(
                                        sesion_id=s_id,
                                        p_global=eval_rep["total_score_percentage"],
                                        p_anamnesis=eval_rep["score_anamnesis"],
                                        p_ef=eval_rep["score_physical_exam"],
                                        p_exam=eval_rep["score_diagnostic_tests"],
                                        p_diag=eval_rep["score_diagnosis_accuracy"],
                                        p_conducta=eval_rep["score_clinical_management"],
                                        feedback=eval_rep["qualitative_feedback"]
                                    )
                                    
                                    # REGISTRO PERMANENTE DE SEGURIDAD
                                    append_permanent_log("evaluacion", {
                                        "alumno": st.session_state.circuit_student_name,
                                        "estacion": f"Estación N° {idx+1}",
                                        "codigo": current_caso["codigo_estacion"],
                                        "porcentaje": eval_rep["total_score_percentage"],
                                        "nota": calcular_nota_chile(eval_rep["total_score_percentage"]),
                                        "feedback": eval_rep["qualitative_feedback"]
                                    })
                                    
                                    fb_entry = {
                                        "estacion": f"Estación N° {idx+1}",
                                        "especialidad": current_caso["especialidad"],
                                        "porcentaje": eval_rep["total_score_percentage"],
                                        "nota": calcular_nota_chile(eval_rep["total_score_percentage"]),
                                        "feedback": eval_rep["qualitative_feedback"]
                                    }
                                    st.session_state.circuit_results.append(fb_entry)
                                    st.session_state.last_station_feedback = fb_entry
                                    
                                    st.session_state.circuit_current_index += 1
                                    
                                    if st.session_state.circuit_current_index >= total_st:
                                        st.session_state.circuit_active = False
                                        st.session_state.showing_inter_station_feedback = False
                                        st.session_state.showing_survey = True
                                    else:
                                        st.session_state.circuit_active = False
                                        st.session_state.showing_inter_station_feedback = True
                                        
                                    st.rerun()

            # PANTALLA DE ENCUESTA AUTOMÁTICA POST-ECOE
            elif st.session_state.showing_survey and not st.session_state.survey_completed:
                st.balloons()
                st.success("🎉 **¡CIRCUITO DE ESTACIONES FINALIZADO CON ÉXITO!**")
                st.subheader(f"📋 Cuestionario de Percepción e Investigación Pedagógica - {st.session_state.circuit_student_name}")
                st.caption("Por favor responde estas breves preguntas (1 a 5) para guardar oficialmente tus resultados en la plataforma.")
                
                with st.form("form_encuesta_investigacion"):
                    st.markdown("##### 🔹 Dimensión I: Fidelidad Clínica y Realismo")
                    f1 = st.slider("F1: El paciente de IA respondió de forma clínicamente coherente y realista.", 1, 5, 4)
                    f2 = st.slider("F2: El paciente mantuvo el tono emocional (dolor, preocupación, ansiedad) adecuado.", 1, 5, 4)
                    f3 = st.slider("F3: La entrega de hallazgos del examen físico y exámenes fue precisa.", 1, 5, 4)
                    f4 = st.slider("F4: Sentí que estaba interactuando con un paciente real en un box.", 1, 5, 4)
                    
                    st.markdown("---")
                    st.markdown("##### 🔹 Dimensión II: Usabilidad y Experiencia de Usuario")
                    u1 = st.slider("U1: La interfaz web fue clara, intuitiva y fácil de navegar.", 1, 5, 5)
                    u2 = st.slider("U2: El tiempo de 7 minutos por estación fue adecuado.", 1, 5, 4)
                    u3 = st.slider("U3: El reloj cronómetro en pantalla me ayudó a gestionar la consulta.", 1, 5, 4)
                    u4 = st.slider("U4: No experimenté dificultades técnicas que interfirieran.", 1, 5, 5)
                    
                    st.markdown("---")
                    st.markdown("##### 🔹 Dimensión III: Valor Pedagógico")
                    p1 = st.slider("P1: El examen me permitió probar mis competencias de razonamiento clínico.", 1, 5, 5)
                    p2 = st.slider("P2: El feedback breve al finalizar cada estación fue útil.", 1, 5, 5)
                    p3 = st.slider("P3: Esta modalidad con IA es valiosa para preparar mi examen de grado / EUNACOM.", 1, 5, 5)
                    p4 = st.slider("P4: Recomendaría incorporar este simulador de forma permanente en el Internado.", 1, 5, 5)
                    
                    st.markdown("---")
                    st.markdown("##### 🔹 Dimensión IV: Interacción por Voz")
                    v1 = st.slider("V1: Hablarle al paciente por el micrófono facilitó la fluidez de la consulta.", 1, 5, 4)
                    v2 = st.slider("V2: Escuchar la respuesta hablada del paciente aportó mayor realismo.", 1, 5, 4)
                    
                    st.markdown("---")
                    st.markdown("##### 🔹 Dimensión V: Comentarios Cualitativos")
                    q1 = st.text_area("1. ¿Qué fortalezas destacaría de realizar el ECOE con Pacientes Simulado de IA?", value="")
                    q2 = st.text_area("2. ¿Qué limitaciones o aspectos a mejorar identificó durante las estaciones?", value="")
                    q3 = st.text_area("3. En comparación con un ECOE tradicional con actores humanos, ¿qué ventajas/desventajas percibe?", value="")
                    
                    btn_survey = st.form_submit_button("💾 Guardar Encuesta y Ver Mi Certificado de Notas ➔", type="primary")
                    if btn_survey:
                        likert_dict = {"F1": f1, "F2": f2, "F3": f3, "F4": f4, "U1": u1, "U2": u2, "U3": u3, "U4": u4, "P1": p1, "P2": p2, "P3": p3, "P4": p4, "V1": v1, "V2": v2}
                        qual_dict = {"Q1": q1.strip(), "Q2": q2.strip(), "Q3": q3.strip()}
                        insert_encuesta_investigacion(st.session_state.circuit_student_name, likert_dict, qual_dict)
                        
                        append_permanent_log("encuesta", {
                            "alumno": st.session_state.circuit_student_name,
                            "likert": likert_dict,
                            "cualitativa": qual_dict
                        })
                        
                        st.session_state.survey_completed = True
                        st.session_state.showing_survey = False
                        st.rerun()

            elif st.session_state.circuit_results and not st.session_state.circuit_active and not st.session_state.showing_inter_station_feedback:
                st.balloons()
                st.success(f"🎓 **¡INFORMES Y CERTIFICADO OFICIAL DE NOTAS ECOE UACh!**")
                st.subheader(f"📜 Informe de Calificaciones - Alumno/a: {st.session_state.circuit_student_name}")
                
                res = st.session_state.circuit_results
                pct_prom = sum(r["porcentaje"] for r in res) / len(res) if res else 0.0
                nota_global = calcular_nota_chile(pct_prom)
                
                k1, k2, k3 = st.columns(3)
                k1.metric("Nota Final Global Examen (1.0 - 7.0)", f"Nota {nota_global:.1f}")
                k2.metric("Puntaje Global Cumplido", f"{pct_prom:.1f}%")
                k3.metric("Estado Final Examen", "🟢 APROBADO" if nota_global >= 4.0 else "🔴 REPROBADO")
                
                st.markdown("---")
                st.markdown("### 📋 Desglose de Calificaciones por Estación:")
                
                for idx, r in enumerate(res, 1):
                    n_st = r.get("nota", calcular_nota_chile(r["porcentaje"]))
                    badge = "🟢 APROBADO" if n_st >= 4.0 else "🔴 REPROBADO"
                    with st.expander(f"📌 {r['estacion']} | NOTA: {n_st:.1f} ({r['porcentaje']:.1f}%) | Status: {badge}"):
                        st.info(f"**Observaciones Docentes:**\n\n{r['feedback']}")
                
                st.markdown("---")
                if st.button("🔄 Rendir Nuevo Examen"):
                    st.session_state.circuit_active = False
                    st.session_state.circuit_current_index = 0
                    st.session_state.circuit_results = []
                    st.session_state.showing_inter_station_feedback = False
                    st.session_state.showing_survey = False
                    st.session_state.survey_completed = False
                    st.rerun()

        # --- MODALIDAD B: PRÁCTICA INDIVIDUAL ---
        else:
            st.subheader("🔄 Modulo de Práctica Individual de Estación")
            
            c_sel, c_al = st.columns([2, 1])
            with c_sel:
                caso_opts = {c["id"]: f"[{c['codigo_estacion']}] Estación de Evaluación ({c['dificultad']})" for c in casos}
                sel_id = st.selectbox("Selecciona la Estación:", options=list(caso_opts.keys()), format_func=lambda x: caso_opts[x])
                curr_c = next((c for c in casos if c["id"] == sel_id), None)
                gt = json.loads(curr_c["ground_truth_json"]) if curr_c else {}
            with c_al:
                st_name = st.text_input("Tu Nombre:", value="Interno/a de Medicina")
                if st.button("🔄 Reiniciar Esta Estación"):
                    st.session_state.chat_history = []
                    st.session_state.last_evaluation = None
                    st.rerun()
                    
            st.info(f"📋 **HOJA DEL ALUMNO (DOOR SHEET):**\n\n* **Motivo de Consulta:** {gt.get('motivo_consulta')}\n* **Paciente:** {gt.get('paciente_nombre')}, {gt.get('edad', '50')} años.\n* **Tareas:** Realiza la anamnesis, examen físico o pide exámenes. Cuentas con 7 minutos.")

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            render_voice_input_widget()

            u_input = st.chat_input("Escribe tu pregunta o indicación al paciente (o usa el micrófono arriba)...")
            if u_input:
                if not st.session_state.patient_agent:
                    st.error("⚠️ Clave API requerida en la barra lateral.")
                else:
                    st.session_state.chat_history.append({"role": "user", "content": u_input})
                    with st.spinner("El paciente está respondiendo..."):
                        r_text = st.session_state.patient_agent.respond_to_student(gt, st.session_state.chat_history, u_input)
                        st.session_state.chat_history.append({"role": "assistant", "content": r_text})
                        
                        if st.session_state.enable_tts:
                            render_patient_tts(r_text, st.session_state.get('patient_emotion', '🔴 Dolor Agudo / Agitado'))
                            
                        st.rerun()

            if len(st.session_state.chat_history) >= 2:
                st.markdown("---")
                if st.button("🏁 Finalizar Estación y Obtener Calificación", type="primary"):
                    if not st.session_state.evaluator_agent:
                        st.error("⚠️ Clave API requerida.")
                    else:
                        with st.spinner("El Profesor Evaluador está calificando la sesión..."):
                            report = st.session_state.evaluator_agent.evaluate_simulation(gt, st.session_state.chat_history)
                            st.session_state.last_evaluation = report
                            s_id = insert_sesion_simulacion(sel_id, st_name, st.session_state.chat_history)
                            insert_evaluacion(
                                sesion_id=s_id,
                                p_global=report["total_score_percentage"],
                                p_anamnesis=report["score_anamnesis"],
                                p_ef=report["score_physical_exam"],
                                p_exam=report["score_diagnostic_tests"],
                                p_diag=report["score_diagnosis_accuracy"],
                                p_conducta=report["score_clinical_management"],
                                feedback=report["qualitative_feedback"]
                            )
                            
                            n_ind = calcular_nota_chile(report["total_score_percentage"])
                            st.success(f"🎉 ¡Evaluación completada! Obuviste **Nota {n_ind:.1f}** ({report['total_score_percentage']:.1f}%)")
                            st.info(f"**Feedback Docente:** {report['qualitative_feedback']}")

# =============================================================================
# MODO DOCENTE / ADMINISTRADOR (PROTEGIDO POR CONTRASEÑA/PIN)
# =============================================================================
else:
    c_ad1, c_ad2 = st.columns([1, 4])
    with c_ad1:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)
    with c_ad2:
        st.title("👨‍🏫 Panel Docente y Administración ECOE UACh")
        st.caption("Gestión confidencial de estaciones, pautas secretas, horario, notas e investigación.")
    
    if not st.session_state.docente_autenticado:
        st.warning("🔒 **Acceso Protegido solo para Profesores y Evaluadores.**")
        pass_input = st.text_input("Ingresa la Clave de Docente (PIN):", type="password")
        if st.button("🔑 Ingresar al Panel Docente", type="primary"):
            if pass_input == DOCENTE_PIN:
                st.session_state.docente_autenticado = True
                st.success("🔓 Autenticación Exitosa.")
                st.rerun()
            else:
                st.error("❌ Clave incorrecta. Acceso denegado.")
    else:
        if st.button("🔒 Cerrar Sesión Docente"):
            st.session_state.docente_autenticado = False
            st.session_state.override_mode = None
            st.rerun()
            
        t1, t2, t3, t4, t5, t6 = st.tabs([
            "📊 Notas de Alumnos", 
            "🔬 Resultados Investigación", 
            "💾 Respaldos Permanentes", 
            "⏰ Control de Horario", 
            "📚 Banco Estaciones", 
            "➕ Crear Estación"
        ])
        
        with t1:
            st.subheader("📊 Histórico de Evaluaciones y Calificaciones de Alumnos")
            
            c_bk1, c_bk2 = st.columns(2)
            with c_bk1:
                json_backup_str = export_all_data_json()
                st.download_button(
                    label="💾 Descargar Copia de Seguridad de Notas y Encuestas (JSON)",
                    data=json_backup_str,
                    file_name=f"ecoe_respuestas_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    type="primary"
                )
            with c_bk2:
                uploaded_backup = st.file_uploader("📤 Restaurar Backup (JSON):", type=["json"])
                if uploaded_backup is not None:
                    content_str = uploaded_backup.read().decode("utf-8")
                    if import_all_data_json(content_str):
                        st.success("🎉 Backup restaurado con éxito.")
                        st.rerun()
                        
            st.markdown("---")
            evals = get_todas_evaluaciones()
            
            if evals:
                st.write(f"Total de Sesiones Evaluadas: **{len(evals)}**")
                for ev_item in evals:
                    pct = ev_item["puntaje_global"]
                    nota = calcular_nota_chile(pct)
                    
                    with st.expander(f"👤 Alumno: {ev_item['alumno_nombre']} | [{ev_item['codigo_estacion']}] {ev_item['titulo']} | NOTA: {nota:.1f} ({pct:.1f}%)"):
                        st.write(f"**Fecha y Hora:** {ev_item['fecha_sesion']}")
                        st.write(f"**Desglose Puntajes:** Anamnesis {ev_item.get('puntaje_anamnesis', 15)}/20 | Examen Físico {ev_item.get('puntaje_examen_fisico', 15)}/20 | Exámenes {ev_item.get('puntaje_examenes', 15)}/20 | Diagnóstico {ev_item.get('puntaje_diagnostico', 15)}/20 | Conducta {ev_item.get('puntaje_conducta', 15)}/20")
                        st.info(f"**Feedback Docente:** {ev_item['feedback_docente']}")
            else:
                st.info("Aún no hay evaluaciones registradas en la base de datos local.")

        with t2:
            st.subheader("🔬 Resultados y Datos de Investigación Médica (Encuestas Post-ECOE)")
            encuestas = get_todas_encuestas()
            
            if encuestas:
                st.write(f"Total de Encuestas Respondidas: **{len(encuestas)}**")
                
                f_prom = sum(e["fidelidad_promedio"] for e in encuestas) / len(encuestas)
                u_prom = sum(e["usabilidad_promedio"] for e in encuestas) / len(encuestas)
                p_prom = sum(e["pedagogico_promedio"] for e in encuestas) / len(encuestas)
                v_prom = sum(e["voz_promedio"] for e in encuestas) / len(encuestas)
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Fidelidad Clínica Promedio", f"{f_prom:.2f} / 5.0")
                m2.metric("Usabilidad Promedio (TAM)", f"{u_prom:.2f} / 5.0")
                m3.metric("Valor Pedagógico Promedio", f"{p_prom:.2f} / 5.0")
                m4.metric("Interacción por Voz Promedio", f"{v_prom:.2f} / 5.0")
                
                st.markdown("---")
                st.markdown("##### 📝 Respuestas Cualitativas de Internos para Publicación:")
                for enc in encuestas:
                    q_dict = json.loads(enc["respuestas_cualitativas_json"])
                    with st.expander(f"👤 Interno/a: {enc['alumno_nombre']} ({enc['fecha_encuesta']})"):
                        st.write(f"**Fortalezas destacadas:** {q_dict.get('Q1', 'Sin respuesta')}")
                        st.write(f"**Aspectos a mejorar:** {q_dict.get('Q2', 'Sin respuesta')}")
                        st.write(f"**Comparación con ECOE tradicional:** {q_dict.get('Q3', 'Sin respuesta')}")
            else:
                st.info("Aún no hay encuestas registradas en la base de datos local.")

        with t3:
            st.subheader("💾 Registros de Seguridad Anti-Pérdida (Bitácora de Servidor)")
            st.caption("Esta sección guarda un respaldo histórico redundante en disco para que ningún examen se pierda tras reinicios de la nube.")
            
            if os.path.exists(PERMANENT_LOG_PATH):
                try:
                    with open(PERMANENT_LOG_PATH, "r", encoding="utf-8") as f:
                        perm_records = json.load(f)
                    
                    st.write(f"Total de Registros Guardados en Bitácora: **{len(perm_records)}**")
                    st.download_button(
                        label="📥 Descargar Bitácora Histórica Completa (JSON)",
                        data=json.dumps(perm_records, ensure_ascii=False, indent=2),
                        file_name="bitacora_permanente_ecoe.json",
                        mime="application/json"
                    )
                    
                    st.json(perm_records)
                except Exception as ex_log:
                    st.error(f"Error al leer la bitácora: {ex_log}")
            else:
                st.info("Aún no se han generado registros en la bitácora permanente de disco.")

        with t4:
            st.subheader("⏰ Control de Recepción y Horario del Examen")
            cfg = get_config_examen()
            
            st.markdown("##### 1. Apertura / Cierre Inmediato (Interruptor de Rendición)")
            col_sw1, col_sw2 = st.columns([2, 1])
            with col_sw1:
                sw_estado = st.toggle("🟢 Habilitar Recepción de Examen (Abierto para alumnos)", value=cfg["examen_habilitado"])
            
            st.markdown("---")
            st.markdown("##### 2. Ventana de Horario Automatizada por Hora Oficial de Chile")
            sw_horario = st.checkbox("⏰ Activar Restricción por Horario de Inicio y Cierre (Hora Oficial de Chile)", value=cfg["modo_horario"])
            
            c_h1, c_h2, c_h3 = st.columns(3)
            with c_h1:
                inp_fecha = st.text_input("Fecha del Examen (AAAA-MM-DD):", value=cfg["fecha_examen"], help="Dejar vacío si aplica para cualquier día")
            with c_h2:
                inp_inicio = st.text_input("Hora de Inicio (HH:MM):", value=cfg["hora_inicio"])
            with c_h3:
                inp_fin = st.text_input("Hora de Cierre (HH:MM):", value=cfg["hora_fin"])
                
            if st.button("💾 Guardar Configuración de Horario", type="primary"):
                update_config_examen(sw_estado, sw_horario, inp_fecha.strip(), inp_inicio.strip(), inp_fin.strip())
                st.success("🎉 Configuración de horario actualizada correctamente.")
                st.rerun()

        with t5:
            st.subheader("⚙️ Banco de Estaciones ECOE en SQLite")
            casos = get_casos_ecoe()
            st.write(f"Total de Estaciones Activas: **{len(casos)}**")
            
            for c in casos:
                gt = json.loads(c["ground_truth_json"])
                with st.expander(f"📌 [{c['codigo_estacion']}] {c['titulo']} - {c['especialidad']} ({c['dificultad']})"):
                    st.markdown(f"**Paciente:** {gt.get('paciente_nombre')}, {gt.get('edad', '50')} años")
                    st.markdown(f"**Motivo de Consulta:** {gt.get('motivo_consulta')}")
                    st.markdown(f"**Historia Clínica:** {gt.get('historia_clinica')}")
                    st.markdown(f"**Diagnóstico Indiscutible:** {gt.get('diagnostico_correcto')}")
                    st.markdown(f"**Conducta Esperada:** {gt.get('conducta_correcta')}")
                    
        with t6:
            st.subheader("➕ Agregar Nueva Estación ECOE al Banco")
            
            with st.form("form_nuevo_caso"):
                c_code = st.text_input("Código Estación (ej. EST-301):", value=f"EST-{len(get_casos_ecoe())+201}")
                c_tit = st.text_input("Título del Caso / Patología:", value="")
                c_esp = st.selectbox("Especialidad:", ["Cirugía General", "Cirugía de Urgencias", "Cirugía Digestiva", "Cirugía Vascular", "Cirugía Torácica", "Coloproctología", "Cirugía Oncológica", "Traumatología", "Medicina Interna"])
                c_dif = st.selectbox("Dificultad:", ["Básico (7mo Año)", "Intermedio (Interno Medicina)", "Avanzado"])
                
                st.markdown("---")
                st.markdown("##### Secreto del Caso y Pauta de Evaluación (Ground Truth):")
                p_nom = st.text_input("Nombre del Paciente Simulado:", value="Juan Pérez")
                p_edad = st.text_input("Edad:", value="50")
                p_mot = st.text_area("Motivo de Consulta (Visible al alumno):", value="")
                p_hist = st.text_area("Historia Clínica Completa (Guion del paciente):", value="")
                p_ef = st.text_area("Hallazgos al Examen Físico (Solo revelar si el alumno examina):", value="")
                p_ex = st.text_area("Exámenes de Laboratorio e Imágenes (Solo revelar si los pide):", value="")
                p_diag = st.text_input("Diagnóstico Correcto (Indiscutible):", value="")
                p_cond = st.text_area("Conducta y Manejo Táctico Correcto:", value="")
                
                btn_save = st.form_submit_button("💾 Guardar Estación en SQLite", type="primary")
                if btn_save:
                    gt_dict = {
                        "paciente_nombre": p_nom,
                        "edad": p_edad,
                        "motivo_consulta": p_mot,
                        "historia_clinica": p_hist,
                        "examen_fisico": p_ef,
                        "examenes_laboratorio_imagenes": p_ex,
                        "diagnostico_correcto": p_diag,
                        "conducta_correcta": p_cond
                    }
                    insert_caso_ecoe(c_code, c_tit, c_esp, c_dif, gt_dict)
                    st.success(f"🎉 Estación [{c_code}] {c_tit} guardada correctamente.")
                    st.rerun()
