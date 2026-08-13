import os
import sys

sys.path.append(os.path.dirname(__file__))
from database import insert_caso_ecoe, db

STATIONS_DATA = [
    {
        'codigo': 'EST-301', 
        'titulo': 'Apendicitis Aguda Clásica', 
        'especialidad': 'Cirugía General', 
        'dificultad': 'Básico (Interno Medicina)', 
        'ground_truth': {
            'paciente_nombre': 'Javier Morales', 
            'edad': '22', 
            'motivo_consulta': 'Dolor abdominal que partió en la boca del estómago y ahora está abajo a la derecha.', 
            'historia_clinica': 'El cuadro inició hace 12 horas con un dolor sordo periumbilical y náuseas (vomitó una vez). Hace 4 horas el dolor migró y se localizó en la fosa ilíaca derecha, haciéndose punzante y continuo (intensidad 8/10). No tiene apetito. No ha tenido fiebre alta, solo sensación febril.', 
            'antecedentes': 'Sano, sin cirugías previas ni uso de medicamentos.', 
            'examen_fisico': 'PA 120/75, FC 98 bpm, T° 37.8 °C. Abdomen plano, RHA presentes. Sensibilidad exquisita en fosa ilíaca derecha. Signo de McBurney (+), Signo de Blumberg (+) franco en FID. Rovsing negativo.', 
            'examenes_laboratorio_imagenes': 'Hemograma: Leucocitosis de 14.500 con 85% PMN. PCR: 45 mg/L. Orina completa normal.', 
            'diagnostico_correcto': 'Apendicitis Aguda', 
            'anamnesis_esperada': 'Indagar cronología de Murphy (migración del dolor), síntomas asociados (anorexia, náuseas) y antecedentes quirúrgicos.', 
            'examen_fisico_esperado': 'Buscar signos de irritación peritoneal focalizada (Blumberg, McBurney).', 
            'examenes_indispensables': 'Hemograma, PCR y Orina completa (para descartar ITU).', 
            'conducta_correcta': 'Régimen cero, hidratación IV, analgesia IV (Paracetamol/AINEs), cobertura antibiótica profiláctica y preparación para Apendicectomía de urgencia.'
        }
    },
    {
        'codigo': 'EST-302', 
        'titulo': 'Colecistitis Aguda Calculosa', 
        'especialidad': 'Cirugía General', 
        'dificultad': 'Intermedio (Interno Medicina)', 
        'ground_truth': {
            'paciente_nombre': 'Rosaura Pinal', 
            'edad': '45', 
            'motivo_consulta': 'Dolor fuerte debajo de la costilla derecha y fiebre.', 
            'historia_clinica': 'Cuadro de 24 horas de evolución de dolor tipo cólico en hipocondrio derecho irradiado al dorso derecho. Inició tras comer empanadas fritas. Refiere que siempre le dolía un poco y pasaba, pero ahora el dolor es constante, no cede, y en la mañana presentó fiebre con escalofríos.', 
            'antecedentes': 'Multípara de 3, Obesidad leve. Sabía que tenía "piedras" en la vesícula pero no se quiso operar.', 
            'examen_fisico': 'PA 130/80, FC 90 bpm, T° 38.5 °C. Abdomen doloroso a la palpación en hipocondrio derecho. Signo de Murphy (+) claro (tope inspiratorio al palpar). Sin signos de irritación peritoneal difusa. No hay ictericia clínica.', 
            'examenes_laboratorio_imagenes': 'Leucocitos 13.000, PCR 80. Pruebas hepáticas (Bilirrubina, FA, GOT/GPT) normales. Ecografía: Vesícula biliar distendida de 11x5 cm, pared engrosada de 5 mm, múltiples cálculos en su interior, uno de 1.5 cm impactado en el bacinete. Coledoco normal.', 
            'diagnostico_correcto': 'Colecistitis Aguda Calculosa', 
            'anamnesis_esperada': 'Indagar tiempo de evolución (>6 hrs para Colecistitis), gatillante alimentario y antecedente de litiasis.', 
            'examen_fisico_esperado': 'Evaluación dirigida de hipocondrio derecho y búsqueda explícita del Signo de Murphy.', 
            'examenes_indispensables': 'Hemograma, PCR, Pruebas Hepáticas (para descartar coledocolitiasis) y Ecografía Abdominal.', 
            'conducta_correcta': 'Hospitalización, régimen cero, sueroterapia, analgesia, antibióticos IV (Ceftriaxona + Metronidazol o similar) y programación para Colecistectomía Laparoscópica.'
        }
    },
    {
        'codigo': 'EST-303', 
        'titulo': 'Obstrucción Intestinal por Bridas', 
        'especialidad': 'Cirugía General', 
        'dificultad': 'Intermedio (Interno Medicina)', 
        'ground_truth': {
            'paciente_nombre': 'Mario Gutiérrez', 
            'edad': '60', 
            'motivo_consulta': 'Me he hinchado como un globo y vomito todo lo que como.', 
            'historia_clinica': 'Hace 2 días comenzó con dolor cólico intermitente en todo el abdomen. Progresivamente notó que el vientre se inflaba. Hace 24 horas no elimina gases ni deposiciones y hoy ha vomitado 4 veces un líquido oscuro de muy mal olor (fecaloideo).', 
            'antecedentes': 'Apendicectomía complicada con peritonitis a los 30 años (laparotomía media).', 
            'examen_fisico': 'PA 110/65, FC 105 bpm, Sequedad de mucosas ++. Abdomen globuloso, muy distendido, asimétrico, cicatriz media infraumbilical. Timpanismo generalizado a la percusión. RHA aumentados, de timbre metálico. Dolor a la palpación profunda sin irritación peritoneal.', 
            'examenes_laboratorio_imagenes': 'BUN 35, Creatinina 1.3 (Deshidratación). Rx Abdomen Simple de pie: Niveles hidroaéreos en intestino delgado, imagen en "pila de monedas", ausencia de gas en la ampolla rectal.', 
            'diagnostico_correcto': 'Obstrucción Intestinal Alta de probable origen Adherencial (Bridas)', 
            'anamnesis_esperada': 'Preguntar por tránsito intestinal (gases/heces), características del vómito y antecedente de cirugías abdominales.', 
            'examen_fisico_esperado': 'Evaluar hidratación, percutir abdomen, auscultar RHA metálicos y buscar cicatrices.', 
            'examenes_indispensables': 'Radiografía de abdomen simple (o TAC), ELP y Función Renal.', 
            'conducta_correcta': 'Régimen cero, instalación de Sonda Nasogástrica a caída libre, reanimación hídrica vigorosa IV, corrección de ELP y observación estricta o derivación a Cirujano (prueba de contraste).'
        }
    },
    {
        'codigo': 'EST-304', 
        'titulo': 'Diverticulitis Aguda', 
        'especialidad': 'Cirugía General', 
        'dificultad': 'Avanzado (Interno Medicina)', 
        'ground_truth': {
            'paciente_nombre': 'Carlos Silva', 
            'edad': '68', 
            'motivo_consulta': 'Dolor constante en el lado izquierdo bajo y fiebre.', 
            'historia_clinica': 'Paciente consulta por cuadro de 3 días de dolor insidioso en fosa ilíaca izquierda, que se ha intensificado progresivamente. Refiere fiebre no cuantificada. Tiene constipación habitual que ha empeorado en los últimos días.', 
            'antecedentes': 'HTA crónica, constipación de larga data.', 
            'examen_fisico': 'PA 135/85, FC 92 bpm, T° 38.2 °C. Abdomen: Masa palpable de 4 cm muy dolorosa en fosa ilíaca izquierda (FII), con Blumberg localizado (+). No hay contractura abdominal generalizada.', 
            'examenes_laboratorio_imagenes': 'Leucocitos 15.000, PCR 120. TAC de Abdomen y Pelvis con contraste: Engrosamiento mural del colon sigmoides con múltiples divertículos, inflamación de la grasa pericólica (stranding) y una pequeña colección líquida de 2 cm (Hinchey Ib o II leve). Sin neumoperitoneo.', 
            'diagnostico_correcto': 'Diverticulitis Aguda (Hinchey I o II)', 
            'anamnesis_esperada': 'Historia de constipación, dolor en FII y descarte de síntomas urinarios.', 
            'examen_fisico_esperado': 'Palpación dirigida en FII buscando masa o irritación peritoneal focal.', 
            'examenes_indispensables': 'TAC de Abdomen y Pelvis con contraste (Gold Standard), Hemograma y PCR.', 
            'conducta_correcta': 'Hospitalización, reposo digestivo, antibióticos IV (Ej. Ceftriaxona + Metronidazol) e interconsulta a Cirugía para manejo médico (no requiere cirugía de urgencia inicial por colección pequeña).'
        }
    },
    {
        'codigo': 'EST-305', 
        'titulo': 'Gran Quemado (Trauma)', 
        'especialidad': 'Cirugía General / Plástica', 
        'dificultad': 'Intermedio (Interno Medicina)', 
        'ground_truth': {
            'paciente_nombre': 'Pedro Arancibia', 
            'edad': '35', 
            'motivo_consulta': 'Ingreso traído por ambulancia tras quedar atrapado en incendio de casa.', 
            'historia_clinica': 'Rescatado de estructura en llamas, expuesto a humo denso en ambiente cerrado por 10 minutos. Refiere mucho dolor en la cara y brazo, pero no siente dolor en el pecho.', 
            'antecedentes': 'Sin antecedentes. Pesa 70 kg.', 
            'examen_fisico': 'Vibrisas nasales quemadas, esputo carbonáceo. Ronquera leve. Quemaduras: Cara completa (4.5% - tipo AB), Tórax y Abdomen anterior (18% - tipo B/escaras secas indoloras), Brazo derecho completo (9% - tipo A/AB con flictenas). Total SCQ: ~31.5%.', 
            'examenes_laboratorio_imagenes': 'Gases arteriales iniciales: sospecha de intoxicación por CO. Fibrobroncoscopía (si la piden): Edema supraglótico moderado con hollín.', 
            'diagnostico_correcto': 'Gran Quemado (>20% SCQ) con Sospecha de Quemadura de Vía Aérea', 
            'anamnesis_esperada': 'Mecanismo de lesión (espacio cerrado vs abierto), tiempo de exposición, cálculo rápido de SCQ y peso del paciente para reanimación.', 
            'examen_fisico_esperado': 'Evaluación ABCDE. Buscar signos de quemadura de vía aérea (vibrisas, voz ronca) y aplicar Regla de los 9.', 
            'examenes_indispensables': 'Ninguno retrasa el manejo inicial. Gases arteriales / Carboxihemoglobina si disponible.', 
            'conducta_correcta': 'Asegurar Vía Aérea (Intubación Orotraqueal profiláctica inmediata por signos de vía aérea superior), O2 al 100%, 2 vías venosas periféricas e iniciar fluidoterapia vigorosa (Parkland o 2-4 ml/kg/%SCQ Ringer Lactato), analgesia agresiva IV y traslado a Unidad de Quemados (GES).'
        }
    },
    {
        'codigo': 'EST-306', 
        'titulo': 'Sospecha de Cáncer Colorectal (Sind. Anémico)', 
        'especialidad': 'Cirugía Oncológica / General', 
        'dificultad': 'Intermedio (Interno Medicina)', 
        'ground_truth': {
            'paciente_nombre': 'Luisa Fernández', 
            'edad': '72', 
            'motivo_consulta': 'Me canso mucho, estoy pálida y las heces a veces salen con sangre oscura.', 
            'historia_clinica': 'Consulta por cuadro de 4 meses de astenia profunda, fatiga al caminar y baja de peso de 6 kg involuntaria. Refiere que últimamente tiene episodios de diarrea que se alternan con días que no va al baño. Ha notado deposiciones de color burdeo/oscuro en ocasiones.', 
            'antecedentes': 'Hermano falleció de Cáncer de Colon a los 60 años.', 
            'examen_fisico': 'Pálida (+++). FC 100 bpm. Abdomen: Blando, indoloro, masa dura y móvil palpable en fosa ilíaca derecha. Tacto rectal: Ampolla rectal vacía, deposiciones oscuras en guante (Test de sangre oculta positivo).', 
            'examenes_laboratorio_imagenes': 'Hemograma: Hb 8.0 g/dL, VCM 72 fL (Anemia Microcítica Hipocrómica).', 
            'diagnostico_correcto': 'Cáncer de Colon Derecho (Síndrome Anémico Tumoral) / Sospecha', 
            'anamnesis_esperada': 'Búsqueda de síntomas B (baja de peso), cambio en hábito intestinal, antecedentes familiares oncológicos y caracterización del sangrado.', 
            'examen_fisico_esperado': 'Examen abdominal para buscar masas y solicitar explícitamente la realización del Tacto Rectal.', 
            'examenes_indispensables': 'Colonoscopía total con Biopsia (Examen confirmatorio). Hemograma (ya lo tiene, evidencia anemia férrica).', 
            'conducta_correcta': 'Notificación de Sospecha GES de Cáncer Colorectal, derivación prioritaria a Gastroenterología o Cirugía para Colonoscopía, prescripción de suplementación de fierro y control estricto.'
        }
    },
    {
        'codigo': 'EST-307', 
        'titulo': 'Hemotórax Masivo (Trauma Torácico)', 
        'especialidad': 'Cirugía General / Urgencias', 
        'dificultad': 'Avanzado (Interno Medicina)', 
        'ground_truth': {
            'paciente_nombre': 'Felipe Yáñez', 
            'edad': '28', 
            'motivo_consulta': 'Paciente traído por paramédicos con dificultad para respirar severa y presión muy baja tras sufrir herida punzante.', 
            'historia_clinica': 'Agredido hace 30 minutos con un arma blanca (destornillador) en hemitórax izquierdo, línea media clavicular en el 5to espacio intercostal. Llega sudoroso, pálido y obnubilado.', 
            'antecedentes': 'Joven, sin antecedentes.', 
            'examen_fisico': 'PA 70/40 mmHg (Shock grado III/IV), FC 130 bpm, SatO2 88%. Hemitórax izquierdo: Herida de 2 cm. Auscultación: Murmullo Pulmonar ABOLIDO en la base y campo medio izquierdo. Percusión: MATIDEZ franca en lado izquierdo. Venas del cuello planas.', 
            'examenes_laboratorio_imagenes': 'Fast-Eco (eFAST): Líquido abundante en cavidad pleural izquierda. NO mandar a Rx tórax si el paciente está inestable hemodinámicamente.', 
            'diagnostico_correcto': 'Hemotórax Masivo Izquierdo (Shock Hemorrágico clase III-IV)', 
            'anamnesis_esperada': 'Mecanismo de lesión penetrante torácico, estimación rápida de pérdida sanguínea.', 
            'examen_fisico_esperado': 'Evaluación ABCDE. Auscultación pulmonar y percusión (reconocer matidez vs timpanismo para diferenciar de Neumotórax a tensión).', 
            'examenes_indispensables': 'Eco-FAST. Hemoclasificación (Grupo y Rh) URGENTE para transfusión.', 
            'conducta_correcta': 'Reanimación con control de daños (sangre O- o específica, 1:1:1), instalación INMEDIATA de Tubo de Pleurostomía izquierdo (28-32 Fr) para drenar sangre. Si drenaje es >1500 ml o >200 ml/hr x 3 horas, activar protocolo para TORACOTOMÍA de Urgencia en pabellón.'
        }
    }
]

def clear_old_stations():
    if not db: 
        print("⚠️ No hay base de datos conectada para borrar.")
        return
    print("Borrando casos antiguos en Firestore...")
    casos_ref = db.collection('casos_ecoe').stream()
    for doc in casos_ref:
        doc.reference.delete()
        print(f" - Borrado {doc.id}")
    print("✅ Casos antiguos borrados.")

def import_all_stations():
    print("Importando 7 estaciones NUEVAS de Cirugía General UACh...")
    clear_old_stations()
    for st in STATIONS_DATA:
        cid = insert_caso_ecoe(
            codigo=st["codigo"],
            titulo=st["titulo"],
            especialidad=st["especialidad"],
            dificultad=st["dificultad"],
            ground_truth_data=st["ground_truth"]
        )
        print(f"✅ Estación [{st['codigo']}] {st['titulo']} cargada con ID {cid}.")
    print("🎉 ¡Todas las 7 estaciones nuevas registradas en Firestore!")

if __name__ == "__main__":
    import_all_stations()
