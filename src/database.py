import sqlite3
import os
import json

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ecoe.db"))

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, timeout=30.0)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla casos_ecoe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS casos_ecoe (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_estacion TEXT UNIQUE NOT NULL,
        titulo TEXT NOT NULL,
        especialidad TEXT NOT NULL,
        dificultad TEXT NOT NULL,
        ground_truth_json TEXT NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tabla sesiones_simulacion
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sesiones_simulacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caso_id INTEGER NOT NULL,
        alumno_nombre TEXT NOT NULL,
        transcripcion_chat_json TEXT NOT NULL,
        fecha_sesion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (caso_id) REFERENCES casos_ecoe (id)
    )
    """)
    
    # Tabla evaluaciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sesion_id INTEGER NOT NULL,
        puntaje_global REAL NOT NULL,
        puntaje_anamnesis REAL NOT NULL,
        puntaje_examen_fisico REAL NOT NULL,
        puntaje_examenes REAL NOT NULL,
        puntaje_diagnostico REAL NOT NULL,
        puntaje_conducta REAL NOT NULL,
        feedback_docente TEXT NOT NULL,
        fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sesion_id) REFERENCES sesiones_simulacion (id)
    )
    """)
    
    conn.commit()
    conn.close()

def insert_caso_ecoe(codigo: str, titulo: str, especialidad: str, dificultad: str, ground_truth_data: dict) -> int:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    gt_json = json.dumps(ground_truth_data, ensure_ascii=False)
    cursor.execute(
        "INSERT OR REPLACE INTO casos_ecoe (codigo_estacion, titulo, especialidad, dificultad, ground_truth_json) VALUES (?, ?, ?, ?, ?)",
        (codigo, titulo, especialidad, dificultad, gt_json)
    )
    caso_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return caso_id

def get_casos_ecoe() -> list:
    init_db()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo_estacion, titulo, especialidad, dificultad, ground_truth_json FROM casos_ecoe ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def insert_sesion_simulacion(caso_id: int, alumno_nombre: str, chat_history: list) -> int:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    chat_json = json.dumps(chat_history, ensure_ascii=False)
    cursor.execute(
        "INSERT INTO sesiones_simulacion (caso_id, alumno_nombre, transcripcion_chat_json) VALUES (?, ?, ?)",
        (caso_id, alumno_nombre, chat_json)
    )
    sesion_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return sesion_id

def insert_evaluacion(sesion_id: int, p_global: float, p_anamnesis: float, p_ef: float, p_exam: float, p_diag: float, p_conducta: float, feedback: str):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO evaluaciones (sesion_id, puntaje_global, puntaje_anamnesis, puntaje_examen_fisico, puntaje_examenes, puntaje_diagnostico, puntaje_conducta, feedback_docente) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (sesion_id, p_global, p_anamnesis, p_ef, p_exam, p_diag, p_conducta, feedback)
    )
    conn.commit()
    conn.close()

def get_evaluaciones_por_alumno(alumno_nombre: str) -> list:
    init_db()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id as sesion_id, c.codigo_estacion, c.titulo, c.especialidad, e.puntaje_global, e.puntaje_anamnesis, e.puntaje_examen_fisico, e.puntaje_examenes, e.puntaje_diagnostico, e.puntaje_conducta, e.feedback_docente, s.fecha_sesion
        FROM sesiones_simulacion s
        JOIN casos_ecoe c ON s.caso_id = c.id
        JOIN evaluaciones e ON e.sesion_id = s.id
        WHERE s.alumno_nombre = ?
        ORDER BY s.id ASC
    """, (alumno_nombre,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_todas_evaluaciones() -> list:
    init_db()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id as sesion_id, s.alumno_nombre, c.codigo_estacion, c.titulo, c.especialidad, e.puntaje_global, e.puntaje_anamnesis, e.puntaje_examen_fisico, e.puntaje_examenes, e.puntaje_diagnostico, e.puntaje_conducta, e.feedback_docente, s.fecha_sesion
        FROM sesiones_simulacion s
        JOIN casos_ecoe c ON s.caso_id = c.id
        JOIN evaluaciones e ON e.sesion_id = s.id
        ORDER BY s.id DESC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def init_config_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracion_examen (
            id INTEGER PRIMARY KEY DEFAULT 1,
            examen_habilitado INTEGER DEFAULT 1,
            modo_horario INTEGER DEFAULT 0,
            fecha_examen TEXT,
            hora_inicio TEXT,
            hora_fin TEXT
        );
    """)
    cursor.execute("SELECT COUNT(*) FROM configuracion_examen;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO configuracion_examen (id, examen_habilitado, modo_horario, fecha_examen, hora_inicio, hora_fin) VALUES (1, 1, 0, '', '08:00', '20:00');")
    conn.commit()
    conn.close()

def get_config_examen():
    init_config_table()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT examen_habilitado, modo_horario, fecha_examen, hora_inicio, hora_fin FROM configuracion_examen WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "examen_habilitado": bool(row[0]),
            "modo_horario": bool(row[1]),
            "fecha_examen": row[2],
            "hora_inicio": row[3],
            "hora_fin": row[4]
        }
    return {"examen_habilitado": True, "modo_horario": False, "fecha_examen": "", "hora_inicio": "08:00", "hora_fin": "20:00"}

def update_config_examen(examen_habilitado, modo_horario, fecha_examen, hora_inicio, hora_fin):
    init_config_table()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE configuracion_examen 
        SET examen_habilitado = ?, modo_horario = ?, fecha_examen = ?, hora_inicio = ?, hora_fin = ?
        WHERE id = 1;
    """, (1 if examen_habilitado else 0, 1 if modo_horario else 0, fecha_examen, hora_inicio, hora_fin))
    conn.commit()
    conn.close()


# --- TABLA Y FUNCIONES DE ENCUESTA DE INVESTIGACIÓN POST-ECOE ---
def init_encuesta_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS encuestas_investigacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_nombre TEXT NOT NULL,
            fidelidad_promedio REAL,
            usabilidad_promedio REAL,
            pedagogico_promedio REAL,
            voz_promedio REAL,
            respuestas_likert_json TEXT NOT NULL,
            respuestas_cualitativas_json TEXT NOT NULL,
            fecha_encuesta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def insert_encuesta_investigacion(alumno_nombre: str, likert_dict: dict, cualitativa_dict: dict):
    init_encuesta_table()
    conn = get_connection()
    cursor = conn.cursor()
    
    f_avg = (likert_dict.get("F1", 4) + likert_dict.get("F2", 4) + likert_dict.get("F3", 4) + likert_dict.get("F4", 4)) / 4.0
    u_avg = (likert_dict.get("U1", 4) + likert_dict.get("U2", 4) + likert_dict.get("U3", 4) + likert_dict.get("U4", 4)) / 4.0
    p_avg = (likert_dict.get("P1", 4) + likert_dict.get("P2", 4) + likert_dict.get("P3", 4) + likert_dict.get("P4", 4)) / 4.0
    v_avg = (likert_dict.get("V1", 4) + likert_dict.get("V2", 4)) / 2.0
    
    cursor.execute("""
        INSERT INTO encuestas_investigacion 
        (alumno_nombre, fidelidad_promedio, usabilidad_promedio, pedagogico_promedio, voz_promedio, respuestas_likert_json, respuestas_cualitativas_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (alumno_nombre, f_avg, u_avg, p_avg, v_avg, json.dumps(likert_dict, ensure_ascii=False), json.dumps(cualitativa_dict, ensure_ascii=False)))
    
    conn.commit()
    conn.close()

def get_todas_encuestas() -> list:
    init_encuesta_table()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, alumno_nombre, fidelidad_promedio, usabilidad_promedio, pedagogico_promedio, voz_promedio, respuestas_likert_json, respuestas_cualitativas_json, fecha_encuesta FROM encuestas_investigacion ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def export_all_data_json() -> str:
    evals = get_todas_evaluaciones()
    encuestas = get_todas_encuestas()
    casos = get_casos_ecoe()
    config = get_config_examen()
    
    backup = {
        "evaluaciones": evals,
        "encuestas": encuestas,
        "casos": casos,
        "configuracion": config
    }
    return json.dumps(backup, ensure_ascii=False, indent=2)

def import_all_data_json(json_str: str) -> bool:
    try:
        data = json.loads(json_str)
        conn = get_connection()
        cursor = conn.cursor()
        
        # Import encuestas
        if "encuestas" in data:
            init_encuesta_table()
            for enc in data["encuestas"]:
                cursor.execute("""
                    INSERT OR IGNORE INTO encuestas_investigacion 
                    (alumno_nombre, fidelidad_promedio, usabilidad_promedio, pedagogico_promedio, voz_promedio, respuestas_likert_json, respuestas_cualitativas_json, fecha_encuesta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (enc.get("alumno_nombre"), enc.get("fidelidad_promedio"), enc.get("usabilidad_promedio"), enc.get("pedagogico_promedio"), enc.get("voz_promedio"), enc.get("respuestas_likert_json"), enc.get("respuestas_cualitativas_json"), enc.get("fecha_encuesta")))
                
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al importar backup:", e)
        return False
