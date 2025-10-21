import json
from colorama import Fore, Style
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Ejecutando Drivers
option = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=option)

# Funcion para buscar peliculas en IMDB
def search_imdb(movie_title):
    search_url = f"https://www.imdb.com/find/?q={movie_title.replace(' ', '+')}&s=tt"
    driver.get(search_url)

    try:
        # Esperar a que carguen los resultados
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.ipc-metadata-list li a"))
        )

        # Obtener el primer resultado de tipo título (tt)
        first_result = driver.find_element(By.CSS_SELECTOR, "ul.ipc-metadata-list li a[href*='/title/tt']")
        movie_link = first_result.get_attribute("href")

        # Extraer el ID (ejemplo: tt1375666)
        movie_id = movie_link.split("/title/")[1].split("/")[0]

        return movie_id

    except Exception as e:
        print(f"Error finding movie: {e}")
        return None

# Funcion para 'scrapear' detalles de la pelicula (todo lo que no son reseñas)
def scrape_movie(movie_id):
    movie_url = f"https://www.imdb.com/title/{movie_id}"
    driver.get(movie_url)

    # Esperar a que cargue el título
    WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

    title = driver.find_element(By.TAG_NAME, "h1").text.strip()

    # Extraer la valoracion sobre 10
    try:
        # Esperar a que el elemento de calificación esté presente
        rating_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span.ipc-rating-star--rating")
            )
        )
        rating = rating_elem.text.strip()
    except:
    # si la valoracion no existe , se devuelve N/A
        rating = "N/A"

    return title, rating


# Funcion para obtener las reseñas largas , evitando los apartados que pone "spoilers"
def scrap_long_reviews(movie_id, max_reviews=20):
    reviews_url = f"https://www.imdb.com/title/{movie_id}/reviews"
    driver.get(reviews_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Seleccionamos solo los divs de reseñas largas
        review_elements = driver.find_elements(By.CSS_SELECTOR, "div.ipc-html-content-inner-div[role='presentation']")

        reviews = []
        for review in review_elements:
            try:
                review_txt = driver.execute_script("return arguments[0].textContent;", review).strip()

                # Omitir reseñas que contengan spoilers
                if "spoiler" in review_txt.lower():
                    continue

                reviews.append(review_txt)
                if len(reviews) >= max_reviews:
                    break
            except:
                continue

        return reviews if reviews else ["No reviews found"]

    except Exception as e:
        print(f"Error while scraping long reviews: {e}")
        return ["No reviews found"]


# Programita para poder ejecutarlo en la bash de forma interactiva
movie_title = input("Introduzca película a buscar: ") #si no se quiere ejecutar en la bash, borrar el imput y poner aqui algun texto como "Pulp Fiction"
movie_id = search_imdb(movie_title)

if movie_id:
    title, rating = scrape_movie(movie_id)
    reviews = scrap_long_reviews(movie_id, max_reviews=20)

    # Guardar en formato JSON
    file_name_json = f"{title.replace(' ','_')}_Largas.json"
    reviews_dict = {f"review{i+1}": review for i, review in enumerate(reviews)}

    movie_data = {
        "title": title,
        "rating": rating,
        "reviews": reviews_dict
    }
    with open(file_name_json, "w", encoding="utf-8") as json_file:
        json.dump(movie_data, json_file, ensure_ascii=False, indent=4)

    # Mostrarlo en la bash con colorines , gracias a "colorama" , una libreria de python
    print(Fore.CYAN + "\n🎬  Movie: " + Fore.YELLOW + title + Style.RESET_ALL)
    print(Fore.GREEN + "⭐  IMDb Rating: " + Fore.YELLOW + rating + "/10" + Style.RESET_ALL)

    print(Fore.MAGENTA + "\n📝  Top 20 Reviews:" + Style.RESET_ALL)
    print(Fore.WHITE + "-----------------------------------" + Style.RESET_ALL)
    for i, review in enumerate(reviews[:20], start=1): #aquí se debería de igualar el numero de reseñas con el de arriba , para mostrar esas
        print(Fore.LIGHTBLUE_EX + f"💬  Review {i}: {review}" + Style.RESET_ALL)
    print(Fore.WHITE + "-----------------------------------" + Style.RESET_ALL)


else:
    print("Movie not found.")

driver.quit()
