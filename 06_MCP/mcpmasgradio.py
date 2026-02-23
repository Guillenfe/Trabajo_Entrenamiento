import asyncio
import httpx
import urllib.parse
import threading
import gradio as gr
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

# 1. Creamos la instancia del Servidor MCP
mcp = FastMCP("CinemaChecker")

TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3NDJlOTEzZmU5NGVjMGRkMzYwMDU5M2Q4NTYwOTA3YyIsIm5iZiI6MTc2MzgxMDYwMS44NDksInN1YiI6IjY5MjE5ZDI5ZWQyYmM5ZDg5ZGI3NDBmNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.s0NW5XITKPrGZ10MrE_eXqpo_ajtGPywNP2rTkaJTAk"
BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "accept": "application/json"
}

# ==========================================
# HERRAMIENTAS MCP (Las que verá Claude)
# ==========================================

@mcp.tool()
async def search_movie(query: str) -> str:
    """Busca una película por título para obtener su ID y sinopsis."""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/search/movie?query={query}"
        response = await client.get(url, headers=HEADERS)
        data = response.json()
        if not data.get("results"):
            return "No se encontraron películas."
        
        m = data["results"][0]
        return f"Título: {m['title']} (ID: {m['id']})\nEstreno: {m.get('release_date')}\nSinopsis: {m['overview']}"

@mcp.tool()
async def check_movie_availability(movie_title: str, location: str) -> str:
    """Consulta horarios de cine reales en Google usando Playwright."""
    search_query = f"movie showtimes {movie_title} in {location}"
    encoded_query = urllib.parse.quote(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    async with async_playwright() as p:
        # Usamos tu configuración persistente que evita bloqueos
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            showtime_data = await page.query_selector_all(".Evln0c")
            
            if not showtime_data:
                return f"No se encontraron horarios para '{movie_title}' en {location}."

            results = [f"- {(await entry.inner_text()).replace(chr(10), ' ')}" for entry in showtime_data[:5]]
            return "\n".join(results)
        finally:
            await browser.close()

# ==========================================
# INTERFAZ GRADIO (La "ventana" del MCP)
# ==========================================

def launch_gradio_interface():
    with gr.Blocks(title="Cinema MCP UI") as demo:
        gr.Markdown("# 🎬 Cinema MCP Server Interface")
        
        with gr.Tab("Buscador TMDB"):
            movie_in = gr.Textbox(label="Película")
            movie_out = gr.Textbox(label="Info de la Herramienta MCP", lines=5)
            btn_movie = gr.Button("Ejecutar Herramienta")
            # Llamamos a la lógica asíncrona dentro de Gradio
            btn_movie.click(lambda q: asyncio.run(search_movie(q)), inputs=movie_in, outputs=movie_out)
            
        with gr.Tab("Horarios Google"):
            with gr.Row():
                name_in = gr.Textbox(label="Película")
                loc_in = gr.Textbox(label="Ciudad")
            show_out = gr.Textbox(label="Resultado del Scraper MCP", lines=5)
            btn_show = gr.Button("Consultar Disponibilidad")
            btn_show.click(lambda m, l: asyncio.run(check_movie_availability(m, l)), inputs=[name_in, loc_in], outputs=show_out)

    # prevent_thread_lock=True es CLAVE para que el servidor MCP pueda iniciar
    demo.launch(prevent_thread_lock=True, server_port=7860)

# ==========================================
# INICIO DEL SERVIDOR
# ==========================================

if __name__ == "__main__":
    # 1. Lanzamos Gradio en el fondo
    print("Iniciando Interfaz Gradio en http://localhost:7860...")
    launch_gradio_interface()
    
    # 2. Iniciamos el servidor MCP (esto bloquea y queda a la escucha de Claude)
    print("Servidor MCP activo. Listo para conectar con Claude Desktop.")
    mcp.run()