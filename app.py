import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
import paho.mqtt.client as paho
import json
from gtts import gTTS
from googletrans import Translator

# --- CSS PESADILLA GÓTICA (Referencia Bloodborne: Azul Oscuro, Bronce, Tinta y Sangre) ---
base_css = """
<style>
/* ---------------------------------------------------- */
/* RESET Y FONDO AMBIENTAL */
/* ---------------------------------------------------- */
.stApp {
    /* Color de la noche de Yharnam o la Pesadilla: Azul/Negro muy oscuro. */
    background-color: #0F0F1A; 
    color: #C0C0C0; /* Texto de pergamino antiguo */
    font-family: 'Georgia', serif; 
}

/* ---------------------------------------------------- */
/* TIPOGRAFÍA Y ENCABEZADOS */
/* ---------------------------------------------------- */
h1 {
    /* Titular: Bronce envejecido o Oro oscuro */
    color: #9C7E4F; 
    text-align: center;
    /* Borde inferior como una reja forjada */
    border-bottom: 3px solid #4F4A5E; 
    padding-bottom: 10px;
    margin-bottom: 40px;
    font-size: 2.5em;
    letter-spacing: 3px;
    text-shadow: 1px 1px 5px #000000;
}

h3 {
    /* Subtítulos: Gris pizarra o plata mate */
    color: #A9A9A9; 
    margin-top: 25px;
    font-weight: normal;
    border-left: 4px solid #B22222; /* Acento Sangre */
    padding-left: 10px;
    font-size: 1.5em;
}

/* ---------------------------------------------------- */
/* BOTONES (Sello de Invocación) */
/* ---------------------------------------------------- */
.stButton>button, .bk-root .bk-btn {
    /* Acero oscuro, base de la Rueda de la Convocación */
    background-color: #383850 !important; 
    /* Texto: Letras rúnicas en rojo sangre */
    color: #B22222 !important; 
    /* Borde: Acento de metal forjado */
    border: 2px solid #9C7E4F !important; 
    padding: 10px 20px !important;
    font-weight: bold;
    border-radius: 10px;
    transition: all 0.3s;
    /* Sombra profunda */
    box-shadow: 0 6px #1A1A2A; 
    letter-spacing: 1px;
}

.stButton>button:hover, .bk-root .bk-btn:hover {
    background-color: #4F4F6A !important; 
    box-shadow: 0 10px #0F0F1A;
    transform: translateY(-3px);
}

.stButton>button:active, .bk-root .bk-btn:active {
    box-shadow: 0 3px #0F0F1A;
    transform: translateY(3px);
}

/* ---------------------------------------------------- */
/* MENSAJES DE ESTADO */
/* ---------------------------------------------------- */
.stSuccess, .stWarning, .stError {
    border-radius: 5px;
    padding: 10px;
}
.stSuccess {
    background-color: #1A2A1A; /* Verde oscuro místico */
    color: #A3D9A3;
    border-left: 4px solid #4CAF50;
}
.stError {
    background-color: #3A1A1A; /* Rojo oscuro de sangre */
    color: #FF6666;
    border-left: 4px solid #B22222;
}

</style>
"""
st.markdown(base_css, unsafe_allow_html=True)


# --- Funciones de MQTT y Utilidad ---
def on_publish(client,userdata,result): #create function for callback
    print("El comando arcano ha sido publicado. \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received=str(message.payload.decode("utf-8"))
    st.write(message_received)

broker="broker.mqttdashboard.com"
port=1883
client1= paho.Client("GIT-HUBC")
client1.on_message = on_message


# --- Configuración de la Interfaz con nueva narrativa ---
st.title("🎙️ LA VOZ DE LA RUNA: CONTROL ARCANO")
st.subheader("La Invocación del Comando")

# NOTA: La imagen 'voice_ctrl.jpg' debe estar disponible para cargarla.
try:
    image = Image.open('voice_ctrl.jpg')
    st.image(image, width=200, caption="El Sello de la Cacería")
except FileNotFoundError:
    st.markdown("---")
    st.warning("⚠️ Sello Arcano ('voice_ctrl.jpg') no encontrado. Se necesita el icono de invocación.")


st.markdown("---")
st.markdown("### Pronuncia el **Comando Secreto** para transmitir la orden a través del Cosmos (MQTT).")

# --- Botón de Reconocimiento de Voz (utiliza Bokeh y Web Speech API) ---
stt_button = Button(label=" ¡INICIAR RITO DE VOZ! ", width=300)

stt_button.js_on_event("button_click", CustomJS(code="""
    // Inicializa el reconocimiento de voz. Usa 'es-ES' para español.
    var recognition = new webkitSpeechRecognition();
    recognition.lang = 'es-ES'; 
    recognition.continuous = false; // Queremos una frase corta, no una conversación continua
    recognition.interimResults = false; // Solo resultados finales
    
    // Mensaje de inicio para el usuario
    document.dispatchEvent(new CustomEvent("STATUS_UPDATE", {detail: "Esperando la palabra arcana..."}));
    
    recognition.onresult = function (e) {
        var value = "";
        // Se itera para obtener el resultado final (normalmente solo hay uno si continuous=false)
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
            // Envía la transcripción a Python
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    
    recognition.onerror = function(event) {
        document.dispatchEvent(new CustomEvent("STATUS_UPDATE", {detail: "Error al escuchar: " + event.error}));
    }
    
    recognition.onend = function() {
        // Opcional: indicar que el reconocimiento ha terminado
        // document.dispatchEvent(new CustomEvent("STATUS_UPDATE", {detail: "Rito de escucha finalizado."}));
    }

    recognition.start();
    """))

# Handler para el estado (opcional, para feedback inmediato al usuario)
status_placeholder = st.empty()
status_result = streamlit_bokeh_events(
    CustomJS(code=""), # No se necesita un botón visible para este
    events="STATUS_UPDATE",
    key="status_listen",
    refresh_on_update=False,
    debounce_time=0)

if status_result:
    if "STATUS_UPDATE" in status_result:
        status_placeholder.info(status_result.get("STATUS_UPDATE"))


# Manejador principal para el resultado de voz
result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0) # Reducir el debounce para mejor respuesta


if result:
    if "GET_TEXT" in result:
        transcribed_text = result.get("GET_TEXT")
        
        st.markdown(f"### 📖 Transcripción Arcaica:")
        st.markdown(f"**El Oráculo escuchó:** *“{transcribed_text}”*")
        
        # --- Lógica de Publicación MQTT (Envío de la Runa) ---
        client1.on_publish = on_publish 
        try:
            client1.connect(broker,port) 
            message = json.dumps({"Act1": transcribed_text.strip()})
            ret = client1.publish("voice_ctrl", message)
            st.success(f"**Éxito:** El Comando fue transmitido al canal cósmico **'voice_ctrl'**.")
            
        except Exception as e:
            st.error(f"**Fallo en la Conexión:** No se pudo contactar al Nexus Cósmico (MQTT Broker): {e}")

        # --- Creación de Directorio (Según el código original) ---
        try:
            os.mkdir("temp")
        except FileExistsError:
            pass
        except Exception as e:
            print(f"Error creando el refugio 'temp': {e}")
