import gradio as gr
import requests
import json
import os
from dotenv import load_dotenv

# -------------------- CARGA DE CONFIG --------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REVIEWS_FILE = "Idiocracia_largas.json"

MODEL = "gemini-2.0-flash"

# -------------------- CARGAR JSON --------------------
def cargar_reseñas():
    """Carga reseñas desde el JSON exportado"""
    try:
        with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        reviews = [r for r in data.get("reviews", []) if r.get("content")]
        return reviews
    except Exception as e:
        return [f"[ERROR] No se pudieron cargar reseñas: {e}"]

REVIEWS = cargar_reseñas()

# -------------------- TOOLS --------------------
def buscar_pelicula(nombre: str):
    # Busca el título de una película dentro del JSON de reseñas y muestra reseñas completas
    if not nombre:
        return "❗ Ingresa el nombre de una película."

    nombre = nombre.lower()
    coincidencias = []

    # Por cada review se busca coincidencia de texto y se guarda en array
    for r in REVIEWS:
        content = r.get("content", "")
        if nombre in content.lower():
            author = r.get("author", {}).get("displayName", "Anónimo")
            coincidencias.append(f"👤 {author}:\n{content.strip()}\n" + "-"*80)

    if not coincidencias:
        return "No se encontraron coincidencias en las reseñas."

    # Muestra las primeras 5 reseñas completas
    return "\n\n".join(coincidencias[:5])


def traducir_texto(texto: str, target_lang="es"):
    # Traduce texto (de inglés a target_lang)
    if not texto:
        return "❗ Ingresa un texto para traducir."

    url = "https://api.mymemory.translated.net/get"
    MAX_LEN = 500

    # --- Dividir texto largo en fragmentos seguros ---
    partes = [texto[i:i + MAX_LEN] for i in range(0, len(texto), MAX_LEN)]
    traduccion_final = ""

    # Se traduce cada parte del texto
    for parte in partes:
        params = {"q": parte, "langpair": f"en|{target_lang}"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        traduccion = data.get("responseData", {}).get("translatedText", parte)
        traduccion_final += traduccion + " "

    return traduccion_final.strip()

# -------------------- GEMINI --------------------
def gemini_generate(prompt: str):
    if not GEMINI_API_KEY:
        return "[ERROR] Falta tu GEMINI_API_KEY en .env"

    # Especificamos modelo compatible con nuestro proyecto
    MODEL = "gemini-2.0-flash"
    url = "https://generativelanguage.googleapis.com/v1/models/"+ MODEL +":generateContent"

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    resp = requests.post(url, headers=headers, params=params, json=body, timeout=30)

    # Si la respuesta no es 200, mostramos el texto de error
    if resp.status_code != 200:
        return f"[HTTP {resp.status_code}] {resp.text}"

    data = resp.json()

    # Si hay texto válido
    if "candidates" in data and len(data["candidates"]) > 0:
        parts = data["candidates"][0].get("content", {}).get("parts", [])
        if parts and "text" in parts[0]:
            return parts[0]["text"]

    # Si no hay texto válido
    return f"[ERROR] Respuesta inesperada: {json.dumps(data, ensure_ascii=False, indent=2)}"

# -------------------- LÓGICA DE INTERFAZ --------------------
def analizar_reseñas(pregunta: str, traducir=False):
    if not REVIEWS or "ERROR" in REVIEWS[0]:
        return REVIEWS[0]

    # Tomamos solo el texto de las primeras 10 reseñas
    contexto = "\n".join([r["content"] for r in REVIEWS[:10]])
    prompt = f"Basándote en estas reseñas de IMDb:\n{contexto}\n\nResponde: {pregunta}"

    respuesta = gemini_generate(prompt)

    if traducir:
        respuesta = traducir_texto(respuesta, "es")

    return respuesta

# -------------------- INTERFAZ GRADIO --------------------
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎥 Gradio App con Tools y Gemini API\nExplora reseñas y usa tus herramientas")

    # Pongo estilos para interfaz
    with gr.Tab("💬 Analizar Reseñas"):
        pregunta = gr.Textbox(label="Haz una pregunta sobre las reseñas",
                              placeholder="¿Qué opinan sobre la dirección?",
                              lines=2)
        traducir = gr.Checkbox(label="Traducir respuesta al español", value=False)
        btn_analizar = gr.Button("Analizar con Gemini")
        salida = gr.Textbox(label="Respuesta", interactive=False, lines=15)

        btn_analizar.click(fn=analizar_reseñas, inputs=[pregunta, traducir], outputs=salida)

    with gr.Tab("🔍 Buscar Reseñas Película"):
        nombre_peli = gr.Textbox(label="Nombre de la película a ver", placeholder="Ej: Inception", lines=1)
        btn_buscar = gr.Button("Buscar")
        salida_buscar = gr.Textbox(label="Reseñas", interactive=False, lines=10)
        btn_buscar.click(fn=buscar_pelicula, inputs=nombre_peli, outputs=salida_buscar)

    with gr.Tab("🌐 Traducir Texto"):
        texto_in = gr.Textbox(label="Texto a traducir (EN → ES)", lines=5)
        btn_traducir = gr.Button("Traducir")
        texto_out = gr.Textbox(label="Traducción", interactive=False, lines=10)
        btn_traducir.click(fn=traducir_texto, inputs=texto_in, outputs=texto_out)

# Lanzar app
if __name__ == "__main__":
    demo.launch()
