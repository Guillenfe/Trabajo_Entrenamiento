from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

import asyncio
import json
import httpx
import urllib.parse

# Initialize FastMCP server
mcp = FastMCP("CinemaChecker")

TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3NDJlOTEzZmU5NGVjMGRkMzYwMDU5M2Q4NTYwOTA3YyIsIm5iZiI6MTc2MzgxMDYwMS44NDksInN1YiI6IjY5MjE5ZDI5ZWQyYmM5ZDg5ZGI3NDBmNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.s0NW5XITKPrGZ10MrE_eXqpo_ajtGPywNP2rTkaJTAk"
BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "accept": "application/json"
}

@mcp.tool()
async def check_movie_availability(movie_title: str, location: str, time: str = "") -> str:
    """
    Checks cinema showtimes for a specific movie in a given city/location.
    """
    search_query = f"movie showtimes {movie_title} in {location} {time}"
    encoded_query = urllib.parse.quote(search_query)
    url = f"https://www.google.com/search?q={encoded_query}"

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./user_data",
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized"
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )

        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle")
            
            # Scrape the main showtime container elements
            showtime_data = await page.query_selector_all(".Evln0c")
            
            if not showtime_data:
                return f"I couldn't find specific showtime listings for '{movie_title}' in {location} on the main search page. You might want to check the official cinema website directly."

            results = []
            for entry in showtime_data[:5]: # Limit to top 5 results for brevity
                text = await entry.inner_text()
                clean_text = text.replace("\n", " ")
                results.append(f"- {clean_text}")

            return "\n".join(results)

        except Exception as e:
            return f"Error while checking showtimes: {str(e)}"
        finally:
            browser.close()

@mcp.tool()
async def search_movie(query: str):
    """Search for a movie by title to get its ID and overview."""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/search/movie?query={query}"
        response = await client.get(url, headers=HEADERS)
        data = response.json()
        
        if not data.get("results"):
            return "No movies found."
        
        results = data["results"][:3] # Return top 3 matches
        formatted = []
        for m in results:
            formatted.append(f"Title: {m['title']} (ID: {m['id']})\nRelease: {m.get('release_date')}\nOverview: {m['overview']}\n")
        return "\n---\n".join(formatted)

@mcp.tool()
async def get_person_details(name: str):
    """Get details about an actor or director by their name."""
    async with httpx.AsyncClient() as client:
        # Step 1: Search for the person to get ID
        search_url = f"{BASE_URL}/search/person?query={name}"
        search_res = await client.get(search_url, headers=HEADERS)
        search_data = search_res.json()
        
        if not search_data.get("results"):
            return "Person not found."
        
        person_id = search_data["results"][0]["id"]
        
        # Step 2: Get detailed bio and credits
        detail_url = f"{BASE_URL}/person/{person_id}?append_to_response=combined_credits"
        detail_res = await client.get(detail_url, headers=HEADERS)
        p = detail_res.json()
        
        bio = p.get("biography", "No bio available.")
        dept = p.get("known_for_department", "Unknown")
        credits = p.get("combined_credits", {}).get("cast" if dept == "Acting" else "crew", [])
        top_works = ", ".join([c.get("title", c.get("name")) for c in credits[:5]])

        return f"Name: {p['name']}\nRole: {dept}\nBio: {bio[:500]}...\nNotable Works: {top_works}"
    


async def test_manual(movie: str, location: str):
        """Función de prueba manual para verificar que el scraper y la API funcionan"""
        print(f"\n--- INICIANDO TEST PARA: {movie} en {location} ---")
        
        # 1. Probar búsqueda de info (TMDB)
        print("\n[1/2] Consultando información en TMDB...")
        info = await search_movie(movie)
        print(f"Resultado TMDB:\n{info}")
        
        # 2. Probar disponibilidad (Playwright/Google)
        print(f"\n[2/2] Buscando funciones en Google para {location}...")
        disponibilidad = await check_movie_availability(movie, location)
        print(f"Resultado Cartelera:\n{disponibilidad}")
        print("\n--- TEST FINALIZADO ---\n")

if __name__ == "__main__":
    # IMPORTANTE: Ejecutamos el test y LUEGO el servidor
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(test_manual("Scream 7", "Madrid"))
    
    print("Iniciando servidor MCP...")
    mcp.run()

# async def test(movie:str, location:str):
#     # Manually testing the tool function
#     print("Testing Movie Availability Tool...")
#     result = await check_movie_availability("wuthering heights", "Madrid", "feb 28")
#     print(f"\nResults:\n{result}")

# if __name__ == "__main__":
#     # asyncio.run(test("Wuthering Heights", "Madrid"))
#     mcp.run()