from dotenv import load_dotenv
import os
import json
from openai import OpenAI
import chromadb
import uuid

from reviewScrapping import search_imdb, scrape_movie, scrap_long_reviews, save_reviews_to_file

# 🔑 Cargar API key
load_dotenv(override=True)
gemini_api_key = os.getenv('GOOGLE_API_KEY')

# Conexión a Gemini
chat_client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
embedding_model = "text-embedding-004"
chat_model = "gemini-2.5-flash-preview-05-20"

# Pedir película
movie_name = input("Escribe el nombre de la película (ej: idiocracia): ").replace(' ','_').lower()
movie_id = search_imdb(movie_name)

if movie_id:
    title, rating = scrape_movie(movie_id)
    reviews = scrap_long_reviews(movie_id, 100)
    save_reviews_to_file(title, rating, reviews)
else:
    print("ERROR")
    exit()

# JSON de reseñas
#json_cortas_path = f"../Scrapping/movies/{movie_name}_cortas.json"
json_path = f"./Scrapping/movies/{movie_name}.json"

# Comprobar existencia
if not os.path.exists(json_path):
    print(f"No se encontraron el archivo {json_path}.")
    exit()

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)
reviews = data.get("reviews", {})

# Función para preparar texto y metadata
def prepare_review_for_embedding(review):
    text = review["text"]
    metadata = {"rating": review["rating"], "title": review["title"]}
    return text, metadata

reviews_text, reviews_metadata = map(list, zip(*(prepare_review_for_embedding(r) for r in reviews)))

# Generar embeddings de todas las reseñas
def get_embeddings(text_batch):
    response = chat_client.embeddings.create(
        input=text_batch,
        model=embedding_model
    )
    return [item.embedding for item in response.data]

reviews_embeddings = []
batch_size = 100
for i in range(0, len(reviews_text), batch_size):
    batch = reviews_text[i:i+batch_size]
    reviews_embeddings.extend(get_embeddings(batch))

# Configurar ChromaDB
chroma_client = chromadb.PersistentClient(path="db/movies")
collection_name = "reviews"

# Borrar colección si ya existe
if collection_name in [c.name for c in chroma_client.list_collections()]:
    chroma_client.delete_collection(name=collection_name)

reviews_collection = chroma_client.create_collection(name=collection_name)

# IDs únicos
reviews_ids = [str(uuid.uuid4()) for _ in reviews_text]

# Guardar embeddings en ChromaDB
reviews_collection.add(
    ids=reviews_ids,
    embeddings=reviews_embeddings,
    documents=reviews_text,
    metadatas=reviews_metadata
)

# Función de búsqueda semántica
def semantic_search(query):
    query_embedding = get_embeddings([query])[0]
    k = 10
    results = reviews_collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    return results

# Función para mostrar reseñas en texto plano
def reviews_to_text(documents):
    text_list = []
    for i, doc in enumerate(reversed(documents)):
        text_list.append(f"=== Reseña {i+1} ===\n{doc}")
    return "\n\n".join(text_list)

# Función de prompt del sistema adaptada a películas
def query_system_prompt(combined_content):
    return f"""
Eres un crítico de cine altamente experimentado y experto en análisis de películas.
Tu tarea principal es proporcionar información precisa y exacta sobre las reseñas proporcionadas.
Respondes directamente a la consulta utilizando solo la información proporcionada en las
siguientes reseñas: {combined_content}.
Si no sabes la respuesta, simplemente di que no lo sabes.
No agregues información que no esté en las reseñas.
"""

# Función para generar respuesta
def generate_response(combined_content):
    query = "¿Cuál es la opinión pública de la película?"

    response = chat_client.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": query_system_prompt(combined_content)},
            {"role": "user", "content": query}
        ],
        temperature=0
    )
    return response

user_question = "Haz una resumen de la opinión general de la película basado en las críticas más profesionales."

# Obtener resultados semánticos
results = semantic_search(user_question)
combined_content = "\n\n".join(results["documents"][0])

# Generar respuesta final usando el prompt del sistema
response = generate_response(combined_content)
print("\n")
print(response.choices[0].message.content)
print("\n")
