from reviewScrapper import search_imdb, scrape_movie, scrap_long_reviews, save_reviews_to_file
from ragCreator import connect_to_gemini, load_reviews, prepare_reviews_for_embedding, make_embeddings_from_text
from ragCreator import make_embedding_database, semantic_search, reviews_to_text, generate_response
from json import tool
import json
import os, time

def scrape_reviews(input_title: str):
    movie_id = search_imdb(input_title)

    if movie_id:
        title, rating = scrape_movie(movie_id)
        print(title)

        # Si ya se ha scrappeado, no se repite
        if os.path.exists(f'./02_review_summarizer/movies/{title.replace(' ','_')}.json'):
            print("Movie already scrapped")
            return title
        
        reviews = scrap_long_reviews(movie_id, 20)
        save_reviews_to_file(title.replace(' ','_'), rating, reviews)
        return title
    else:
        raise Exception("Movie not found")
    
    
def get_relevant_reviews(movie_name: str, user_question: str):
    # Nos conectamos a Gemini
    chat_client, embedding_model, chat_model = connect_to_gemini()

    reviews = load_reviews(movie_name)
    # Obtenemos texto de las reviews y metadata para embedding
    reviews_text, reviews_metadata = prepare_reviews_for_embedding(reviews)
    # Transformamos el texto en embedding (vector)
    reviews_embeddings = make_embeddings_from_text(reviews_text, chat_client, embedding_model)
    # Guardamos los datos en una database de ChromaDB
    reviews_collection = make_embedding_database(reviews_embeddings, reviews_text, reviews_metadata)

    # Usando la pregunta del usuario, obtenemos las reviews relevantes
    relevant_reviews = semantic_search(user_question, 10, reviews_collection, chat_client, embedding_model)
    relevant_reviews_text = reviews_to_text(relevant_reviews)

    return relevant_reviews_text


def get_context(input_title: str, user_question: str):
    input_title = input_title.lower()
    realtitle = scrape_reviews(input_title) # Crea el json y devuelve el nombre real de la peli
    return get_relevant_reviews(realtitle, user_question)

get_review_context_function = {
    "name": "get_context",
    "description": "Obtiene las reviews de una película más relevantes para la pregunta del usuario."
    "Llama a esta función cada vez que necesites las reviews (reseñas) de una película.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "El título de la película en español",
            },
            "user_question": {
                "type": "string",
                "description": "La pregunta hecha por el usuario, sin tener en cuenta el título de la película",
            },
        },
        "required":["title", "user_question"],
        "additionalProperties": False
    },
}

tools = [{"type": "function", "function": get_review_context_function}]

def handle_tool_call(message):
    tool_call = message.tool_calls[0] # the first tool call
    arguments = json.loads(tool_call.function.arguments) # the arguments are a JSON string. json.loads() parses it to a dict
    title = arguments.get('title')
    user_question = arguments.get('user_question')
    review_context = get_context(title, user_question)
    response = {
        "role": "tool",
        "content": json.dumps({"title": title,"user_question": user_question}), # the content is a JSON string. json.dumps() converts a dict to a JSON string
        "tool_call_id": tool_call.id # the ID of the tool call. This is used to identify the tool call in the response
    }

    return response, review_context
