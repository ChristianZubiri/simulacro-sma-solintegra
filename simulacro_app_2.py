import streamlit as st
import time
import random
import json
import os
import requests
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
    
    # Borde exterior
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

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #1e1e1e; color: #e0e0e0; }
    .stButton>button { width: 100%; background-color: #333333; color: #ffcc00; border: 2px solid #ffcc00; border-radius: 5px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { background-color: #ffcc00; color: #1e1e1e; border: 2px solid #ffffff; }
    .inyeccion-box { background-color: #4d0000; border-left: 5px solid #ff4d4d; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .hipotesis-box { background-color: #003366; border-left: 5px solid #0099ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADOS ---
if 'paso' not in st.session_state:
    st.session_state.paso = 0
if 'nombre_usuario' not in st.session_state:
    st.session_state.nombre_usuario = ""
if 'tiempo_inicio' not in st.session_state:
    st.session_state.tiempo_inicio = 0
if 'estado_juego' not in st.session_state:
    st.session_state.estado_juego = "inicio" 
if 'razon_fin' not in st.session_state:
    st.session_state.razon_fin = ""
if 'sorpresas_disponibles' not in st.session_state:
    st.session_state.sorpresas_disponibles = []
if 'sorpresas_activas' not in st.session_state:
    st.session_state.sorpresas_activas = []
if 'sorpresa_mostrada_este_intento' not in st.session_state:
    st.session_state.sorpresa_mostrada_este_intento = False

# --- LÓGICA DE JUEGO ---
def iniciar_intento(nombre):
    st.session_state.nombre_usuario = nombre
    bd = cargar_bd()
    if nombre not in bd:
        bd[nombre] = {"intentos": 0, "completado": False}
    bd[nombre]["intentos"] += 1
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

def evaluar_respuesta(es_correcta, mensaje_error, limite_segundos):
    tiempo_transcurrido = time.time() - st.session_state.tiempo_inicio
    
    if tiempo_transcurrido > limite_segundos:
        st.session_state.estado_juego = "game_over"
        st.session_state.razon_fin = f"⏳ ¡TIEMPO AGOTADO! Tardaste {tiempo_transcurrido:.1f}s (Límite: {limite_segundos}s)."
    elif not es_correcta:
        st.session_state.estado_juego = "game_over"
        st.session_state.razon_fin = f"❌ ERROR CRÍTICO: {mensaje_error}"
    else:
        st.session_state.paso += 1
        st.session_state.tiempo_inicio = time.time()
        lanzar_sorpresa_aleatoria(st.session_state.paso)

def lanzar_sorpresa_aleatoria(paso_actual):
    if not st.session_state.sorpresas_disponibles:
        return

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
        <p>En el Taller de Hojalatería y Pintura, una camioneta de 3.5 toneladas impacta contra una estructura, provocando la ruptura total de su tanque de combustible con capacidad de 100 litros.</p>
        <p><strong>Misión:</strong> Contener el hidrocarburo antes de que llegue a la alcantarilla pluvial y al suelo natural. Las decisiones varían en dificultad; gestiona tu tiempo sabiamente.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("▶️ INICIAR SIMULACRO"):
        if nombre_input.strip() == "":
            st.error("Debes ingresar tu nombre para registrar la evaluación.")
        else:
            iniciar_intento(nombre_input.strip())
            st.rerun()

# --- MANEJO DE GAME OVER ---
elif st.session_state.estado_juego == "game_over":
    st.error(st.session_state.razon_fin)
    lottie_fail = cargar_animacion("https://lottie.host/46db3e67-ea88-4db9-8c90-95133df19f56/9kM8gYgG5d.json")
    if lottie_fail:
        st_lottie(lottie_fail, height=200, key="fail")
    st.warning("El simulacro se ha detenido por protocolo de seguridad. Debes iniciar desde el principio.")
    
    if st.button("🔄 Volver a la Hipótesis Principal"):
        st.session_state.paso = 0
        st.session_state.estado_juego = "inicio"
        st.rerun()

# --- MANEJO DE ÉXITO Y GENERACIÓN DE PDF ---
elif st.session_state.estado_juego == "completado":
    bd = cargar_bd()
    bd[st.session_state.nombre_usuario]["completado"] = True
    guardar_bd(bd)
    
    st.balloons()
    st.success(f"🏆 ¡FELICIDADES {st.session_state.nombre_usuario.upper()}! SIMULACRO SUPERADO.")
    anim_success = cargar_animacion("https://lottie.host/5a071a93-7df6-4f40-8abf-40e8b2ed33b6/T1g5y5yY3h.json")
    if anim_success: st_lottie(anim_success, height=250)
    
    st.write("Has demostrado un excelente dominio del protocolo de contención, protección ambiental y gestión de recursos.")
    
    # Generación y Botón de Descarga del PDF
    pdf_bytes = generar_pdf(st.session_state.nombre_usuario)
    
    st.download_button(
        label="📄 DESCARGAR CONSTANCIA (PDF)",
        data=pdf_bytes,
        file_name=f"Constancia_Simulacro_{st.session_state.nombre_usuario.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
    
    st.markdown("---")
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
        if anim_alert:
            st_lottie(anim_alert, height=100)

    # --- PASO 1 ---
    if st.session_state.paso == 1:
        limite = 10
        st.subheader("Fase 1: El Impacto")
        st.write("¡CRASH! Se rompe el tanque y 100 litros de combustible comienzan a escurrir rápido.")
        mostrar_temporizador(limite)
        
        if st.button("Evacuar área inmediata, apagar compresores y reportar a la supervisión operativa."):
            evaluar_respuesta(True, "", limite)
            st.rerun()
        if st.button("Correr inmediatamente hacia la unidad para intentar tapar la fuga con un trapo."):
            evaluar_respuesta(False, "Te expusiste a los vapores y generaste riesgo de explosión al no aislar el área.", limite)
            st.rerun()

    # --- PASO 2 ---
    elif st.session_state.paso == 2:
        limite = 15
        st.subheader("Fase 2: Evaluación")
        st.write("El charco crece rápidamente. Faltan pocos metros para que el combustible alcance la alcantarilla pluvial.")
        mostrar_temporizador(limite)
        
        if st.button("Consultar las 3 etiquetas de la HDS para determinar riesgo de ignición y EPP necesario."):
            evaluar_respuesta(True, "", limite)
            st.rerun()
        if st.button("Confiar en el operador, asumir que es diésel normal y mandar a la brigada sin equipo."):
            evaluar_respuesta(False, "Nunca asumas la toxicidad. La falta de consulta de la HDS puso en riesgo a la brigada.", limite)
            st.rerun()

    # --- PASO 3 ---
    elif st.session_state.paso == 3:
        limite = 10
        st.subheader("Fase 3: Movilización")
        st.write("Están equipados. Saben que no hay kit en Hojalatería y Pintura.")
        anim_run = cargar_animacion("https://lottie.host/3697e883-294b-48bf-a843-0f8cf807f794/RHTF8rA3qX.json")
        if anim_run: st_lottie(anim_run, height=150)
        mostrar_temporizador(limite)
        
        if st.button("Mandar a un brigadista al Taller Mecánico Diésel por el kit y arena."):
            evaluar_respuesta(True, "", limite)
            st.rerun()
        if st.button("Mandar a todos a buscar en los almacenes a ver quién encuentra algo útil."):
            evaluar_respuesta(False, "Desorganización operativa. Los kits tienen ubicaciones fijas que deben conocerse.", limite)
            st.rerun()

    # --- PASO 4 ---
    elif st.session_state.paso == 4:
        limite = 15
        st.subheader("Fase 4: Contención Primaria")
        st.write("Los insumos llegaron a la escena. El combustible está muy cerca de la coladera.")
        mostrar_temporizador(limite)
        
        if st.button("Usar la arena para crear un dique rodeando la alcantarilla pluvial ANTES de taponar el tanque."):
            evaluar_respuesta(True, "", limite)
            st.rerun()
        if st.button("Intentar taponar el tanque roto primero para evitar que siga saliendo combustible."):
            evaluar_respuesta(False, "DAÑO AMBIENTAL. Al ignorar la coladera, el hidrocarburo llegó al drenaje pluvial.", limite)
            st.rerun()

    # --- PASO 5 ---
    elif st.session_state.paso == 5:
        limite = 15
        st.subheader("Fase 5: Recolección")
        st.write("El derrame está contenido. Deben recoger la arena, pero recuerdan que NO cuentan con palas antichispa.")
        mostrar_temporizador(limite)
        
        if st.button("Evaluar recoger la arena en plástico grueso minimizando fricción y llevarla al Almacén de RP."):
            tiempo_transcurrido = time.time() - st.session_state.tiempo_inicio
            if tiempo_transcurrido > limite:
                st.session_state.estado_juego = "game_over"
                st.session_state.razon_fin = f"⏳ ¡TIEMPO AGOTADO! Tardaste {tiempo_transcurrido:.1f}s."
            else:
                st.session_state.estado_juego = "completado"
            st.rerun()
            
        if st.button("Usar palas convencionales despacio y con cuidado para terminar el trabajo."):
            evaluar_respuesta(False, "IGNICIÓN. Las herramientas convencionales generaron fricción estática, provocando un incendio por los vapores.", limite)
            st.rerun()
