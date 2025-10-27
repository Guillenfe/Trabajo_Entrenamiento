import gradio as gr
import os
from dotenv import load_dotenv
from tools import tools, handle_tool_call
from openai import OpenAI

# Cargar API key
load_dotenv(override=True)
gemini_api_key = os.getenv('GOOGLE_API_KEY')

# Conexión a Gemini
chat_client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
chat_model = "gemini-2.5-flash-preview-05-20"

# Lógica de la interfaz
def analyze_reviews(pregunta: str):

    user_prompt = pregunta
    system_prompt = f"""
    Eres un crítico de cine altamente experimentado y experto en análisis de películas.
    Tu tarea principal es proporcionar información precisa y exacta basada en las reseñas proporcionadas.
    Respondes directamente a la consulta utilizando solo la información proporcionada en las reseñas,
    pero si hay algo en inglés, lo traducirás al español.
    Responderás con un párrafo, no muy largo.
    Si no sabes la respuesta, simplemente di que no lo sabes.
    No agregues información que no esté en las reseñas.
    No contestes preguntas que no sean sobre cine.
    No citarás las reseñas, sino que elaborarás una respuesta propia.
    """
    msgs = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]
    res = chat_client.chat.completions.create(
        model=chat_model,
        messages=msgs,
        tools=tools
    )
    
    # Salta si se activa una tool
    if res.choices[0].finish_reason=="tool_calls":
        message = res.choices[0].message
        response, review_context = handle_tool_call(message)
        context_msg = {
            "role": "system",
            "content": review_context
            }
        msgs.append(context_msg)
        res = chat_client.chat.completions.create(model=chat_model, messages=msgs)
    return res.choices[0].message.content


# Interfaz de gradio
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Pregunta sobre películas\nExplora reseñas y pregunta a nuestro bot crítico")

    pregunta = gr.Textbox(label="Haz una pregunta sobre las reseñas",
                            placeholder="¿Qué opinan sobre la dirección?",
                            lines=2)
    traducir = gr.Checkbox(label="Traducir respuesta al español", value=False)
    btn_analizar = gr.Button("Analizar con Gemini")
    salida = gr.Textbox(label="Respuesta", interactive=False, lines=15)

    btn_analizar.click(fn=analyze_reviews, inputs=[pregunta], outputs=salida)


# Lanzar app
if __name__ == "__main__":
    demo.launch()
