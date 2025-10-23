from review_summarizer.reviewScrapper import scrape_reviews
from json import tool

search_function = {
    "name": "scrape_reviews",
    "description": "Obtiene un .json con las reviews de una película."
    "Llama a esta función cada vez que necesites las reviews (reseñas) de una película.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "El título de la película en español, sin tildes",
            },
        },
        "required":["title"],
        "additionalProperties": False
    },
}

tools = [{"type": "function", "function": search_function}]
