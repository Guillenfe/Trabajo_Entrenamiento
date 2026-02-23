import asyncio
import httpx
import urllib.parse
from playwright.async_api import async_playwright
import gradio as gr

# API TMDB
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3NDJlOTEzZmU5M2Q4NTYwMDU5M2Q4NTYwOTA3YyIsInN1YiI6IjY5MjE5ZDI5ZWQyYmM5ZDg5ZGI3NDBmNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.s0NW5XITKPrGZ10MrE_eXqpo_ajtGPywNP2rTkaJTAk"
BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {TMDB_API_KEY}", "accept": "application/json"}

# ==========================================
# Funciones async
# ==========================================

async def search_movie(query: str):
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/search/movie?query={query}"
        response = await client.get(url, headers=HEADERS)
        data = response.json()

        if not data.get("results"):
            return "No encontré esa película"

        results = data["results"][:3]
        formatted = []
        for m in results:
            formatted.append(f"🎬 {m['title']} ({m.get('release_date','?')})\n{m['overview'][:300]}...\n")
        return "\n---\n".join(formatted)


async def check_movie_availability(movie_title: str, location: str, time: str = "") -> str:
    search_query = f"movie showtimes {movie_title} in {location} {time}"
    encoded_query = urllib.parse.quote(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            headless=True
        )
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            showtime_data = await page.query_selector_all("div")  # Más general
            if not showtime_data:
                return f"No encontré horarios de '{movie_title}' en {location}."
            results = [await entry.inner_text() for entry in showtime_data[:5]]
            return "\n".join([r.replace("\n"," ") for r in results])
        finally:
            await browser.close()


async def get_person_details(name: str):
    async with httpx.AsyncClient() as client:
        search_url = f"{BASE_URL}/search/person?query={name}"
        search_res = await client.get(search_url, headers=HEADERS)
        search_data = search_res.json()
        
        if not search_data.get("results"):
            return "Persona no encontrada "
        
        person_id = search_data["results"][0]["id"]
        detail_url = f"{BASE_URL}/person/{person_id}?append_to_response=combined_credits"
        detail_res = await client.get(detail_url, headers=HEADERS)
        p = detail_res.json()
        
        bio = p.get("biography", "No bio disponible.")
        dept = p.get("known_for_department", "Unknown")
        credits = p.get("combined_credits", {}).get("cast" if dept == "Acting" else "crew", [])
        top_works = ", ".join([c.get("title", c.get("name")) for c in credits[:5]])

        return f"👤 {p['name']}\nRole: {dept}\nBio: {bio[:500]}...\nNotable Works: {top_works}"


# ==========================================
# Wrappers para Gradio (para usar async)
# ==========================================

def wrapper_search_movie(query):
    return asyncio.run(search_movie(query))

def wrapper_check_showtimes(movie, location, time):
    return asyncio.run(check_movie_availability(movie, location, time))

def wrapper_person_details(name):
    return asyncio.run(get_person_details(name))


# ==========================================
# Interfaz Gradio
# ==========================================

with gr.Blocks() as demo:
    gr.Markdown("## 🎬 Cinema Checker")
    
    with gr.Tab("Buscar Película"):
        movie_input = gr.Textbox(label="Nombre de la película")
        movie_button = gr.Button("Buscar")
        movie_output = gr.Textbox(label="Resultados", lines=10)
        movie_button.click(wrapper_search_movie, inputs=movie_input, outputs=movie_output)
    
    with gr.Tab("Horarios"):
        movie_name = gr.Textbox(label="Nombre de la película")
        location = gr.Textbox(label="Ciudad")
        date = gr.Textbox(label="Fecha (opcional)")
        showtime_button = gr.Button("Buscar horarios")
        showtime_output = gr.Textbox(label="Resultados", lines=10)
        showtime_button.click(wrapper_check_showtimes, inputs=[movie_name, location, date], outputs=showtime_output)
    
    with gr.Tab("Actor / Director"):
        person_name = gr.Textbox(label="Nombre")
        person_button = gr.Button("Buscar")
        person_output = gr.Textbox(label="Resultados", lines=10)
        person_button.click(wrapper_person_details, inputs=person_name, outputs=person_output)

demo.launch()