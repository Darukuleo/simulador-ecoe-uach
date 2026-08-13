from datetime import datetime
import json
import os
try:
    from google.cloud import firestore
    # Intenta inicializar el cliente de Firestore (automático en Cloud Run)
    db = firestore.Client()
    print("✅ Conectado a Google Cloud Firestore exitosamente.")
except Exception as e:
    print(f"⚠️ Error inicializando Firestore: {e}. Asegúrese de tener Firestore Native habilitado.")
    db = None

# --- TABLA Y FUNCIONES DE CASOS ECOE ---

def insert_caso_ecoe(codigo: str, titulo: str, especialidad: str, dificultad: str, ground_truth_data: dict) -> str:
    if not db: return "local_id"
    
    gt_json = json.dumps(ground_truth_data, ensure_ascii=False)
    doc_ref = db.collection('casos_ecoe').document(codigo)
    
    doc_ref.set({
        'codigo_estacion': codigo,
        'titulo': titulo,
        'especialidad': especialidad,
        'dificultad': dificultad,
        'ground_truth_json': gt_json,
        'fecha_creacion': datetime.now().isoformat()
    })
    return codigo

def get_casos_ecoe() -> list:
    if not db: return []
    casos_ref = db.collection('casos_ecoe').stream()
    rows = []
    for doc in casos_ref:
        data = doc.to_dict()
        data['id'] = doc.id
        rows.append(data)
    # Ordenar por fecha (descendente simulado)
    rows.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)
    return rows

# --- TABLA Y FUNCIONES DE SESIÓN Y EVALUACIÓN ---

def insert_sesion_simulacion(caso_id: str, alumno_nombre: str, chat_history: list) -> str:
    if not db: return "local_sesion"
    
    chat_json = json.dumps(chat_history, ensure_ascii=False)
    
    # Obtener info del caso para desnormalizar y guardar junto a la sesión
    caso_ref = db.collection('casos_ecoe').document(str(caso_id)).get()
    caso_data = caso_ref.to_dict() if caso_ref.exists else {}
    
    _, doc_ref = db.collection('sesiones_simulacion').add({
        'caso_id': str(caso_id),
        'alumno_nombre': alumno_nombre,
        'transcripcion_chat_json': chat_json,
        'fecha_sesion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'caso_codigo': caso_data.get('codigo_estacion', ''),
        'caso_titulo': caso_data.get('titulo', ''),
        'caso_especialidad': caso_data.get('especialidad', '')
    })
    return doc_ref.id

def insert_evaluacion(sesion_id: str, p_global: float, p_anamnesis: float, p_ef: float, p_exam: float, p_diag: float, p_conducta: float, feedback: str):
    if not db: return
    # Guardamos la evaluación directamente dentro del documento de la sesión
    db.collection('sesiones_simulacion').document(str(sesion_id)).update({
        'evaluacion': {
            'puntaje_global': p_global,
            'puntaje_anamnesis': p_anamnesis,
            'puntaje_examen_fisico': p_ef,
            'puntaje_examenes': p_exam,
            'puntaje_diagnostico': p_diag,
            'puntaje_conducta': p_conducta,
            'feedback_docente': feedback,
            'fecha_evaluacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    })

def get_todas_evaluaciones() -> list:
    if not db: return []
    # Traemos todas las sesiones que tengan una evaluación anidada
    sesiones_ref = db.collection('sesiones_simulacion').stream()
    
    rows = []
    for doc in sesiones_ref:
        data = doc.to_dict()
        if 'evaluacion' in data:
            ev = data['evaluacion']
            row = {
                'sesion_id': doc.id,
                'alumno_nombre': data.get('alumno_nombre', ''),
                'codigo_estacion': data.get('caso_codigo', ''),
                'titulo': data.get('caso_titulo', ''),
                'especialidad': data.get('caso_especialidad', ''),
                'puntaje_global': ev.get('puntaje_global', 0),
                'puntaje_anamnesis': ev.get('puntaje_anamnesis', 0),
                'puntaje_examen_fisico': ev.get('puntaje_examen_fisico', 0),
                'puntaje_examenes': ev.get('puntaje_examenes', 0),
                'puntaje_diagnostico': ev.get('puntaje_diagnostico', 0),
                'puntaje_conducta': ev.get('puntaje_conducta', 0),
                'feedback_docente': ev.get('feedback_docente', ''),
                'fecha_sesion': data.get('fecha_sesion', '')
            }
            rows.append(row)
            
    rows.sort(key=lambda x: x['fecha_sesion'], reverse=True)
    return rows

def get_evaluaciones_por_alumno(alumno_nombre: str) -> list:
    todas = get_todas_evaluaciones()
    return [e for e in todas if e['alumno_nombre'] == alumno_nombre]

# --- TABLA DE CONFIGURACIÓN ---

def get_config_examen():
    if not db: return {"examen_habilitado": True, "modo_horario": False, "fecha_examen": "", "hora_inicio": "08:00", "hora_fin": "20:00"}
    doc_ref = db.collection('configuracion').document('examen')
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        default_config = {"examen_habilitado": True, "modo_horario": False, "fecha_examen": "", "hora_inicio": "08:00", "hora_fin": "20:00"}
        doc_ref.set(default_config)
        return default_config

def update_config_examen(examen_habilitado, modo_horario, fecha_examen, hora_inicio, hora_fin):
    if not db: return
    db.collection('configuracion').document('examen').set({
        "examen_habilitado": bool(examen_habilitado),
        "modo_horario": bool(modo_horario),
        "fecha_examen": fecha_examen,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin
    })

# --- TABLA Y FUNCIONES DE ENCUESTA ---

def insert_encuesta_investigacion(alumno_nombre: str, likert_dict: dict, cualitativa_dict: dict):
    if not db: return
    
    f_avg = (likert_dict.get("F1", 4) + likert_dict.get("F2", 4) + likert_dict.get("F3", 4) + likert_dict.get("F4", 4)) / 4.0
    u_avg = (likert_dict.get("U1", 4) + likert_dict.get("U2", 4) + likert_dict.get("U3", 4) + likert_dict.get("U4", 4)) / 4.0
    p_avg = (likert_dict.get("P1", 4) + likert_dict.get("P2", 4) + likert_dict.get("P3", 4) + likert_dict.get("P4", 4)) / 4.0
    v_avg = (likert_dict.get("V1", 4) + likert_dict.get("V2", 4)) / 2.0
    
    db.collection('encuestas_investigacion').add({
        'alumno_nombre': alumno_nombre,
        'fidelidad_promedio': f_avg,
        'usabilidad_promedio': u_avg,
        'pedagogico_promedio': p_avg,
        'voz_promedio': v_avg,
        'respuestas_likert_json': json.dumps(likert_dict, ensure_ascii=False),
        'respuestas_cualitativas_json': json.dumps(cualitativa_dict, ensure_ascii=False),
        'fecha_encuesta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def get_todas_encuestas() -> list:
    if not db: return []
    encuestas_ref = db.collection('encuestas_investigacion').stream()
    rows = []
    for doc in encuestas_ref:
        data = doc.to_dict()
        data['id'] = doc.id
        rows.append(data)
    rows.sort(key=lambda x: x.get('fecha_encuesta', ''), reverse=True)
    return rows

def export_all_data_json() -> str:
    evals = get_todas_evaluaciones()
    encuestas = get_todas_encuestas()
    casos = get_casos_ecoe()
    config = get_config_examen()
    
    backup = {
        "evaluaciones": evals,
        "encuestas": encuestas,
        "casos_ecoe": casos,
        "configuracion": config
    }
    return json.dumps(backup, ensure_ascii=False, indent=2)

def append_permanent_log(record_type: str, data: dict):
    if not db: return
    try:
        db.collection('registros_permanentes').add({
            'tipo': record_type,
            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'datos': data
        })
    except Exception as e:
        print("Error al escribir registro permanente en Firestore:", e)

def import_all_data_json(json_str: str) -> bool:
    # Restaurar backup en Firestore (Simplificado para evitar sobreescribir)
    print("Restore desde JSON no implementado de forma nativa para Firestore aún.")
    return False

def calcular_nota_chile(porcentaje: float) -> float:
    """Calcula la nota en escala chilena 1.0 a 7.0 con exigencia del 60%."""
    if porcentaje >= 60.0:
        nota = 4.0 + 3.0 * ((porcentaje - 60.0) / 40.0)
    else:
        nota = 1.0 + 3.0 * (porcentaje / 60.0)
    return round(max(1.0, min(7.0, nota)), 1)

