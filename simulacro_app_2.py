import streamlit as st
import time
import random
import json
import os
import requests
import pandas as pd
from streamlit_lottie import st_lottie
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURACIÓN Y BASE DE DATOS LOCAL ---
st.set_page_config(page_title="Simulador SMA", page_icon="☢️", layout="centered")
DB_FILE = "registro_brigadistas.json"

def cargar_bd():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_bd(bd):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(bd, f, indent=4)

def cargar_animacion(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def generar_pdf(nombre):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_draw_color(0, 51, 102)
    pdf.set_line_width(1)
    pdf.rect(10, 10, 190, 277)
    pdf.set_font("Arial", 'B', 18)
    pdf.ln(20)
    pdf.cell(0, 10, txt="CONSTANCIA DE CAPACITACION", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt="El Departamento de SMA (Seguridad Industrial y Medio Ambiente)", ln=True, align='C')
    pdf.cell(0, 10, txt="de Solintegra certifica que:", ln=True, align='C')
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=nombre.upper(), ln=True, align='C')
    pdf.ln(15)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt="Ha completado con exito el Simulacro de Gabinete interactivo:", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="DERRAME DE SUSTANCIA QUIMICA", ln=True, align='C')
    pdf.ln(25)
    pdf.set_font("Arial", '', 10)
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(0, 10, txt=f"Fecha y hora de acreditacion: {fecha_actual}", ln=True, align='C')
    pdf.cell(0, 10, txt="Base Panuco I - Poza Rica, Veracruz", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

def enviar_a_google_sheets(nombre, bd_usuario):
    # ¡Pega aquí la URL larga que te dio Google Apps Script para el reporte de derrames!
    url_webhook = "https://script.google.com/macros/s/AKfycbwo_eRW8kGl95uf14U98xreqhQDD0GKJtdxauM3fi8Pi_50acfUuJ3DMXuq4yBdkOzRHw/exec" 
    
    payload = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nombre": nombre,
        "intentos": bd_usuario.get("Intentos Totales", 1),
        "completado": str(bd_usuario.get("Completado", True)),
        "fase1": bd_usuario.get("1_Evacuacion_Inicial", ""),
        "fase2": bd_usuario.get("2_Evaluacion_HDS", ""),
        "fase3": bd_usuario.get("3_Movilizacion_Recursos", ""),
        "fase4": bd_usuario.get("4_Contencion_Dique", ""),
        "fase5": bd_usuario.get("5_Recoleccion_Antichispa", "")
    }
    
    try:
        requests.post(url_webhook, json=payload)
    except Exception as e:
        pass

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; color: #e0e0e0; }
    .stButton>button { width: 100%; background-color: #333333; color: #ffcc00; border: 2px solid #ffcc00; border-radius: 5px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { background-color: #ffcc00; color: #1e1e1e; border: 2px solid #ffffff; }
    .inyeccion-box { background-color: #4d0000; border-left: 5px solid #ff4d4d; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .hipotesis-box { background-color: #003366; border-left: 5px solid #0099ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .recuperacion-box { background-color: #422006; border-left: 5px solid #f59e0b; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADOS ---
if 'paso' not in st.session_state: st.session_state.paso = 0
if 'nombre_usuario' not in st.session_state: st.session_state.nombre_usuario = ""
if 'tiempo_inicio' not in st.session_state: st.session_state.tiempo_inicio = 0
if 'estado_juego' not in st.session_state: st.session_state.estado_juego = "inicio" 
if 'razon_fin' not in st.session_state: st.session_state.razon_fin = ""
if 'datos_recuperacion' not in st.session_state: st.session_state.datos_recuperacion = {}
if 'metrica_actual' not in st.session_state: st.session_state.metrica_actual = ""
if 'sorpresas_disponibles' not in st.session_state: st.session_state.sorpresas_disponibles = []
if 'sorpresas_activas' not in st.session_state: st.session_state.sorpresas_activas = []
if 'sorpresa_mostrada_este_intento' not in st.session_state: st.session_state.sorpresa_mostrada_este_intento = False

# --- LÓGICA DE JUEGO ---
def iniciar_intento(nombre):
    st.session_state.nombre_usuario = nombre
    bd = cargar_bd()
    if nombre not in bd:
        bd[nombre] = {
            "Intentos Totales": 0,
            "Completado": False,
            "1_Evacuacion_Inicial": "No evaluado",
            "2_Evaluacion_HDS": "No evaluado",
            "3_Movilizacion_Recursos": "No evaluado",
            "4_Contencion_Dique": "No evaluado",
            "5_Recoleccion_Antichispa": "No evaluado"
        }
    bd[nombre]["Intentos Totales"] += 1
    guardar_bd(bd)
    
    st.session_state.paso = 1
    st.session_state.estado_juego = "jugando"
    st.session_state.razon_fin = ""
    st.session_state.sorpresas_activas = []
    st.session_state.sorpresa_mostrada_este_intento = False
    st.session_state.sorpresas_disponibles = [
        {"id": 1, "titulo": "📻 FALLA DE COMUNICACIÓN", "texto": "El radio se quedó sin batería. La alarma aún no suena en la base."},
        {"id": 2, "titulo": "🧰 RECURSOS INCOMPLETOS", "texto": "El kit no tiene calcetines absorbentes. Solo cuentas con arena y tapetes planos."},
        {"id": 3, "titulo": "☀️ FACTOR CLIMATOLÓGICO", "texto": "Temperatura alta, gasificación severa y el viento sopla directo hacia el Comedor."}
    ]
    st.session_state.tiempo_inicio = time.time()

def procesar_respuesta(es_correcta, limite_segundos, pregunta_recuperacion=None, nombre_metrica=""):
    tiempo_transcurrido = time.time() - st.session_state.tiempo_inicio
    
    if tiempo_transcurrido > limite_segundos:
        st.session_state.estado_juego = "game_over"
        st.session_state.razon_fin = f"⏳ ¡TIEMPO AGOTADO! Tardaste {tiempo_transcurrido:.1f}s. El químico sigue avanzando."
    elif not es_correcta:
        bd = cargar_bd()
        bd[st.session_state.nombre_usuario][nombre_metrica] = "Requirió Recuperación"
        guardar_bd(bd)
        
        st.session_state.metrica_actual = nombre_metrica
        st.session_state.estado_juego = "recuperacion"
        st.session_state.datos_recuperacion = pregunta_recuperacion
    else:
        bd = cargar_bd()
        if bd[st.session_state.nombre_usuario].get(nombre_metrica) != "Requirió Recuperación":
            bd[st.session_state.nombre_usuario][nombre_metrica] = "Correcto a la primera"
        guardar_bd(bd)
        
        st.session_state.paso += 1
        st.session_state.tiempo_inicio = time.time()
        lanzar_sorpresa_aleatoria(st.session_state.paso)

def evaluar_recuperacion(es_correcta):
    if es_correcta:
        if st.session_state.paso == 5:
            st.session_state.estado_juego = "completado"
        else:
            st.session_state.paso += 1
            st.session_state.estado_juego = "jugando"
            st.session_state.tiempo_inicio = time.time()
            lanzar_sorpresa_aleatoria(st.session_state.paso)
    else:
        bd = cargar_bd()
        bd[st.session_state.nombre_usuario][st.session_state.metrica_actual] = "Falla Crítica"
        guardar_bd(bd)
        st.session_state.estado_juego = "game_over"
        st.session_state.razon_fin = "❌ ERROR FATAL. No superaste la pregunta de recuperación. Protocolo vulnerado."

def lanzar_sorpresa_aleatoria(paso_actual):
    if not st.session_state.sorpresas_disponibles: return
    probabilidad = 0.35
    forzar = (paso_actual == 4 and not st.session_state.sorpresa_mostrada_este_intento)
    
    if forzar or random.random() < probabilidad:
        sorpresa = random.choice(st.session_state.sorpresas_disponibles)
        st.session_state.sorpresas_disponibles.remove(sorpresa)
        st.session_state.sorpresas_activas = [sorpresa]
        st.session_state.sorpresa_mostrada_este_intento = True
    else:
        st.session_state.sorpresas_activas = []

def mostrar_temporizador(segundos):
    st.warning(f"⏱️ **Límite de tiempo:** {segundos} segundos a partir de ahora.")

# --- PANTALLA PRINCIPAL ---
st.title("☢️ Simulador Operativo SMA")

if st.session_state.estado_juego == "inicio" or st.session_state.paso == 0:
    st.markdown("### Registro de Brigadistas")
    nombre_input = st.text_input("Ingresa tu Nombre Completo para el registro oficial:")
    
    st.markdown("""
    <div class="hipotesis-box">
        <h3>📍 Hipótesis del Ejercicio</h3>
        <p><strong>Derrame de Sustancia Química</strong></p>
        <p>En el Taller de Hojalatería y Pintura, una camioneta de 3.5 toneladas impacta contra una estructura, provocando la ruptura total de su tanque de combustible (100 litros).</p>
        <p><strong>Misión:</strong> Contener el hidrocarburo antes de que llegue a la alcantarilla pluvial y al suelo natural.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("▶️ INICIAR SIMULACRO"):
        if nombre_input.strip() == "":
            st.error("Debes ingresar tu nombre para registrar la evaluación.")
        else:
            iniciar_intento(nombre_input.strip())
            st.rerun()

    # --- PANEL DE EXTRACCIÓN DE DATA ---
    with st.expander("📊 Extracción de Data / Criterios de Evaluación (Jefatura SMA)"):
        st.write("Métricas de desempeño para la evaluación del simulacro de derrame.")
        bd_actual = cargar_bd()
        if bd_actual:
            df = pd.DataFrame.from_dict(bd_actual, orient='index')
            df.index.name = 'Colaborador'
            st.dataframe(df)
            csv = df.to_csv().encode('utf-8')
            st.download_button(
                label="📥 Descargar Data (CSV)",
                data=csv,
                file_name=f"Data_Simulacro_Derrame_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.write("Aún no hay registros.")

# --- ESTADO DE RECUPERACIÓN ---
elif st.session_state.estado_juego == "recuperacion":
    anim_alert = cargar_animacion("https://lottie.host/7724a872-9ea9-42b4-84c4-7db3eec90204/jFmG5t4r5X.json")
    if anim_alert: st_lottie(anim_alert, height=120)

    datos = st.session_state.datos_recuperacion
    st.markdown(f"""
    <div class="recuperacion-box">
        <h4>⚠️ ALERTA DE PROCEDIMIENTO: {datos['contexto_error']}</h4>
        <p>Para continuar en el simulacro, debes resolver esta <strong>Pregunta de Recuperación</strong>:</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader(datos['pregunta'])
    
    if st.button(datos['opcion_correcta']):
        evaluar_recuperacion(True)
        st.rerun()
    if st.button(datos['opcion_incorrecta']):
        evaluar_recuperacion(False)
        st.rerun()

# --- MANEJO DE GAME OVER ---
elif st.session_state.estado_juego == "game_over":
    st.error(st.session_state.razon_fin)
    lottie_fail = cargar_animacion("https://lottie.host/46db3e67-ea88-4db9-8c90-95133df19f56/9kM8gYgG5d.json")
    if lottie_fail: st_lottie(lottie_fail, height=200, key="fail")
    st.warning("El simulacro se ha detenido por protocolo de seguridad. Inicia desde el principio.")
    if st.button("🔄 Volver a la Hipótesis Principal"):
        st.session_state.paso = 0
        st.session_state.estado_juego = "inicio"
        st.rerun()

# --- MANEJO DE ÉXITO ---
elif st.session_state.estado_juego == "completado":
    bd = cargar_bd()
    bd[st.session_state.nombre_usuario]["Completado"] = True
    guardar_bd(bd)
    
    enviar_a_google_sheets(st.session_state.nombre_usuario, bd[st.session_state.nombre_usuario])
    
    st.balloons()
    st.success(f"🏆 ¡FELICIDADES {st.session_state.nombre_usuario.upper()}! SIMULACRO SUPERADO.")
    anim_success = cargar_animacion("https://lottie.host/5a071a93-7df6-4f40-8abf-40e8b2ed33b6/T1g5y5yY3h.json")
    if anim_success: st_lottie(anim_success, height=250)
    
    pdf_bytes = generar_pdf(st.session_state.nombre_usuario)
    st.download_button(
        label="📄 DESCARGAR CONSTANCIA (PDF)",
        data=pdf_bytes,
        file_name=f"Constancia_Simulacro_{st.session_state.nombre_usuario.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    if st.button("🏁 Cerrar Sesión y Volver al Inicio"):
        st.session_state.paso = 0
        st.session_state.estado_juego = "inicio"
        st.session_state.nombre_usuario = ""
        st.rerun()

# --- FLUJO DEL JUEGO (PASOS 1 AL 5) ---
elif st.session_state.estado_juego == "jugando":
    
    if st.session_state.sorpresas_activas:
        sorpresa = st.session_state.sorpresas_activas[0]
        st.markdown(f"""
        <div class="inyeccion-box">
            <h4>{sorpresa['titulo']}</h4>
            <p>{sorpresa['texto']}</p>
        </div>
        """, unsafe_allow_html=True)
        anim_alert = cargar_animacion("https://lottie.host/7724a872-9ea9-42b4-84c4-7db3eec90204/jFmG5t4r5X.json")
        if anim_alert: st_lottie(anim_alert, height=100)

    # El límite de tiempo ahora es 25s en todas las fases (como en el segundo simulacro)
    limite = 25 

    # --- PASO 1 ---
    if st.session_state.paso == 1:
        st.subheader("Fase 1: El Impacto")
        st.write("¡CRASH! Se rompe el tanque y 100 litros de combustible comienzan a escurrir rápido.")
        mostrar_temporizador(limite)
        
        if st.button("Evacuar área inmediata, apagar compresores y reportar a la supervisión operativa."):
            procesar_respuesta(True, limite, nombre_metrica="1_Evacuacion_Inicial")
            st.rerun()
        if st.button("Correr inmediatamente hacia la unidad para intentar tapar la fuga con un trapo."):
            rec = {
                "contexto_error": "Te expusiste a los vapores y generaste riesgo de explosión al no aislar el área.",
                "pregunta": "¿Cuál es el riesgo principal de acercarse a un derrame de hidrocarburo sin identificar y sin equipo respiratorio?",
                "opcion_correcta": "Inhalación severa de vapores tóxicos e ignición súbita.",
                "opcion_incorrecta": "Mancharse gravemente el uniforme de trabajo."
            }
            procesar_respuesta(False, limite, rec, "1_Evacuacion_Inicial")
            st.rerun()

    # --- PASO 2 ---
    elif st.session_state.paso == 2:
        st.subheader("Fase 2: Evaluación")
        st.write("El charco crece rápidamente. Faltan pocos metros para que el combustible alcance la alcantarilla pluvial.")
        mostrar_temporizador(limite)
        
        if st.button("Consultar las 3 etiquetas de la HDS para determinar riesgo de ignición y EPP necesario."):
            procesar_respuesta(True, limite, nombre_metrica="2_Evaluacion_HDS")
            st.rerun()
        if st.button("Confiar en el operador, asumir que es diésel normal y mandar a la brigada sin equipo."):
            rec = {
                "contexto_error": "Nunca asumas la toxicidad. Exponer a la brigada sin equipo es negligencia.",
                "pregunta": "¿Para qué sirve exactamente consultar las etiquetas de la Hoja de Datos de Seguridad (HDS)?",
                "opcion_correcta": "Para conocer los riesgos a la salud, inflamabilidad y definir el EPP adecuado.",
                "opcion_incorrecta": "Para saber quién es el fabricante y proveedor del producto."
            }
            procesar_respuesta(False, limite, rec, "2_Evaluacion_HDS")
            st.rerun()

    # --- PASO 3 ---
    elif st.session_state.paso == 3:
        st.subheader("Fase 3: Movilización")
        st.write("Están equipados. Saben que no hay kit en Hojalatería y Pintura.")
        anim_run = cargar_animacion("https://lottie.host/3697e883-294b-48bf-a843-0f8cf807f794/RHTF8rA3qX.json")
        if anim_run: st_lottie(anim_run, height=150)
        mostrar_temporizador(limite)
        
        if st.button("Mandar a un brigadista al Taller Mecánico Diésel por el kit y arena."):
            procesar_respuesta(True, limite, nombre_metrica="3_Movilizacion_Recursos")
            st.rerun()
        if st.button("Mandar a todos a buscar en los almacenes a ver quién encuentra algo útil."):
            rec = {
                "contexto_error": "Desorganización operativa. El tiempo es crítico y nadie sabe a dónde ir.",
                "pregunta": "¿Por qué es crucial que todo el personal conozca la ubicación exacta de los kits antiderrame?",
                "opcion_correcta": "Para minimizar el tiempo de respuesta y evitar la propagación incontrolable del químico.",
                "opcion_incorrecta": "Para que los auditores vean que el personal tiene buena memoria."
            }
            procesar_respuesta(False, limite, rec, "3_Movilizacion_Recursos")
            st.rerun()

    # --- PASO 4 ---
    elif st.session_state.paso == 4:
        st.subheader("Fase 4: Contención Primaria")
        st.write("Los insumos llegaron a la escena. El combustible está muy cerca de la coladera.")
        mostrar_temporizador(limite)
        
        if st.button("Usar la arena para crear un dique rodeando la alcantarilla pluvial ANTES de taponar el tanque."):
            procesar_respuesta(True, limite, nombre_metrica="4_Contencion_Dique")
            st.rerun()
        if st.button("Intentar taponar el tanque roto primero para evitar que siga saliendo combustible."):
            rec = {
                "contexto_error": "DAÑO AMBIENTAL. Al ignorar la coladera, el hidrocarburo llegó al drenaje pluvial.",
                "pregunta": "En un escenario de derrame en exteriores, ¿cuál es la máxima prioridad física de contención?",
                "opcion_correcta": "Bloquear las vías de agua, coladeras o drenajes para evitar la contaminación del manto freático.",
                "opcion_incorrecta": "Salvar el combustible restante dentro del tanque roto."
            }
            procesar_respuesta(False, limite, rec, "4_Contencion_Dique")
            st.rerun()

    # --- PASO 5 ---
    elif st.session_state.paso == 5:
        st.subheader("Fase 5: Recolección")
        st.write("El derrame está contenido. Deben recoger la arena, pero recuerdan que NO cuentan con palas antichispa.")
        mostrar_temporizador(limite)
        
        if st.button("Evaluar recoger la arena en plástico grueso minimizando fricción y llevarla al Almacén de RP."):
            procesar_respuesta(True, limite, nombre_metrica="5_Recoleccion_Antichispa")
            st.session_state.estado_juego = "completado"
            st.rerun()
            
        if st.button("Usar palas convencionales despacio y con cuidado para terminar el trabajo."):
            rec = {
                "contexto_error": "IGNICIÓN. Las palas convencionales generaron fricción estática, provocando un incendio por vapores.",
                "pregunta": "¿Qué tipo de herramienta es OBLIGATORIA para recoger materiales impregnados con hidrocarburos volátiles?",
                "opcion_correcta": "Herramienta antichispa (como palas de bronce o plástico antiestático).",
                "opcion_incorrecta": "Palas de acero inoxidable pulido."
            }
            procesar_respuesta(False, limite, rec, "5_Recoleccion_Antichispa")
            st.rerun()
