import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Funcion para buscar peliculas en IMDB
def search_imdb(movie_title):
    # Ejecutando Drivers
    option = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=option)

    search_url = f"https://www.imdb.com/find/?q={movie_title.replace(' ', '+')}&s=tt&ttype=ft&ref_=fn_mov"
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

        driver.quit()
        return movie_id

    except Exception as e:
        driver.quit()
        print(f"Error finding movie: {e}")
        return None

# Funcion para 'scrapear' título y puntuación en IMDB de la película
def scrape_movie(movie_id):
    # Ejecutando Drivers
    option = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=option)

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
        
    driver.quit()
    return title, rating


# Funcion para obtener las reseñas largas , evitando los apartados que pone "spoilers"
def scrap_long_reviews(movie_id, max_reviews=20):
    # Ejecutando Drivers
    option = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=option)

    reviews_url = f"https://www.imdb.com/title/{movie_id}/reviews"
    driver.get(reviews_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Expandimos las reviews para ver todas
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.icb-btn[data-testid='accept-button']"))
        )

        try:
            see_more_btn = driver.find_element(By.XPATH, "//span[contains(@class,'chained-see-more-button')]/button")
            
            cookies_btn = driver.find_element(By.CSS_SELECTOR, "button.icb-btn[data-testid='accept-button']")
            cookies_banner = driver.find_element(By.CSS_SELECTOR, "div[data-testid='consent-banner']")
            cookies_btn.click()

            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element(cookies_banner)
            )

            driver.execute_script("arguments[0].scrollIntoView(true);", see_more_btn)

            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(see_more_btn)
            )

            # El botón de ver más falla al hacer click la primera vez
            # Clickamos varias veces hasta que funcione 
            for i in range(0, 10):
                try:
                    see_more_btn.click()
                    # Si funciona, se sale del bucle
                    break
                except:
                    print("Click of 'show more reviews' button FAILED")

            # Esperamos unos segundos a que carguen más reviews
            time.sleep(5)
        except Exception as e:
            driver.quit()
            print("No 'show more reviews' button found")

        # Seleccionamos solo los divs de reseñas largas
        # review_elements = driver.find_elements(By.CSS_SELECTOR, "div.ipc-html-content-inner-div[role='presentation']")
        review_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='review-card-parent']")

        reviews = []
        for review in review_elements:
            try:
                # review_txt = driver.execute_script("return arguments[0].textContent;", review).strip()
                review_rating = review.find_element(By.CSS_SELECTOR, "span.ipc-rating-star--rating").text
                review_title = review.find_element(By.CSS_SELECTOR, "h3.ipc-title__text").text
                review_txt = review.find_element(By.CSS_SELECTOR, "div.ipc-html-content-inner-div[role='presentation']").text

                # Omitir reseñas que contengan spoilers
                if "spoiler" in review_txt.lower():
                    continue

                review_data = {
                    "rating": review_rating,
                    "title": review_title,
                    "text": review_txt
                }

                reviews.append(review_data)
                if len(reviews) >= max_reviews:
                    break
            except:
                continue
        
        review_count = len(reviews)
        print(f"{review_count} reviews found")
        driver.quit()
        return reviews if reviews else ["No reviews found"]

    except Exception as e:
        driver.quit()
        print(f"Error while scraping long reviews: {e}")
        return ["No reviews found"]

def save_reviews_to_file(title, rating, reviews):
    try:
        file_route = "./02_review_summarizer/movies/"
        file_name_json = f"{title.replace(' ','_').lower()}.json"
        file = f"{file_route}{file_name_json}"

        movie_data = {
        "title": title,
        "rating": rating,
        "reviews": reviews
        }

        with open(file, "w", encoding="utf-8") as json_file:
            json.dump(movie_data, json_file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error while saving reviews to file: {e}")
    return False