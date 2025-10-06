from playwright.sync_api import sync_playwright
import json

def scrape_filmaffinity(movie_url):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(movie_url)

        # Ejemplo: extraer datos clave de la película
        title = page.locator("h1").inner_text()
        synopsis = page.locator(".synopsis p").inner_text()
        rating = page.locator(".avg-rating").inner_text()
        cast = [el.inner_text() for el in page.locator(".cast-wrapper a").all()[:10]]

        browser.close()

        return {
            "title": title,
            "synopsis": synopsis,
            "rating": rating,
            "cast": cast
        }

if __name__ == "__main__":
    url = "https://www.filmaffinity.com/es/film444796.html"
    data = scrape_filmaffinity(url)
    print(json.dumps(data, indent=2, ensure_ascii=False))
