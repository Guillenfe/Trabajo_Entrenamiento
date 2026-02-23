import asyncio
import gradio as gr
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["server.py"], 
)

async def call_mcp_tool(tool_name, arguments):
    """Se conecta al servidor, ejecuta la herramienta y devuelve el resultado."""
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # Llamada oficial al protocolo MCP
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text
    except Exception as e:
        return f"Error de conexión con el servidor MCP: {str(e)}"

def search_movie_handler(query):
    return asyncio.run(call_mcp_tool("search_movie", {"query": query}))

def check_availability_handler(movie, location):
    return asyncio.run(call_mcp_tool("check_movie_availability", {
        "movie_title": movie, 
        "location": location
    }))

def get_person_handler(name):
    return asyncio.run(call_mcp_tool("get_person_details", {"name": name}))

with gr.Blocks(title="Cinema MCP Client", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Cinema Checker - MCP Client")
    gr.Markdown("Este Gradio actúa como cliente del servidor `server.py` usando el protocolo MCP.")
    
    with gr.Tab("Buscador de Películas"):
        with gr.Row():
            movie_q = gr.Textbox(label="Título", placeholder="Ej: Scream 7")
            btn_movie = gr.Button("Consultar Servidor", variant="primary")
        out_movie = gr.Textbox(label="Respuesta del MCP", lines=8)
        btn_movie.click(search_movie_handler, inputs=movie_q, outputs=out_movie)

    with gr.Tab("Cartelera Local"):
        with gr.Row():
            c_name = gr.Textbox(label="Película")
            c_loc = gr.Textbox(label="Ciudad")
        btn_show = gr.Button("Rastrear Horarios", variant="primary")
        out_show = gr.Textbox(label="Resultados de Playwright", lines=8)
        btn_show.click(check_availability_handler, inputs=[c_name, c_loc], outputs=out_show)

    with gr.Tab("Personas (Cast/Crew)"):
        p_name = gr.Textbox(label="Nombre del Actor/Director")
        btn_p = gr.Button("Obtener Bio")
        out_p = gr.Textbox(label="Info Detallada", lines=8)
        btn_p.click(get_person_handler, inputs=p_name, outputs=out_p)

if __name__ == "__main__":
    print("Lanzando Cliente Gradio...")
    demo.launch()