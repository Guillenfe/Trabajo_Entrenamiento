from dotenv import load_dotenv
import os
import time
import json
from openai import OpenAI
import chromadb
import uuid

def connect_to_gemini():
    # Cargar API key
    load_dotenv(override=True)
    gemini_api_key = os.getenv('GOOGLE_API_KEY')

    # Conexión a Gemini
    chat_client = OpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    embedding_model = "text-embedding-004"
    chat_model = "gemini-2.5-flash-preview-05-20"

    return chat_client, embedding_model, chat_model

"""
# Pedir película
movie_name = input("Escribe el nombre de la película (ej: idiocracia): ").lower()
movie_id = search_imdb(movie_name)

if movie_id:
    title, rating = scrape_movie(movie_id)
    reviews = scrap_long_reviews(movie_id, 100)
    save_reviews_to_file(title.replace(' ','_'), rating, reviews)
else:
    print("ERROR")
    exit()
"""
def fileExists(file_path, timeout=30):
    start = time.time()
    while not os.path.exists(file_path):
        if time.time() - start > timeout:
            raise TimeoutError("File not found in time")
        time.sleep(0.5)
    return True 

def load_reviews(movie_name):
    movie_name = movie_name.replace(' ','_')
    json_path = f"./review_summarizer/movies/{movie_name}.json"

    # Esperamos por si el archivo se está escribiendo
    if fileExists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("reviews", {})

# Función para preparar texto y metadata
def prepare_reviews_for_embedding(reviews):
    reviews_text = []
    reviews_metadata = []

    # Coge el texto y metadata de la review y as guarda en arrays
    # que se usarán para hacer el embedding
    for review in reviews:
        text = review["text"]
        metadata = {"rating": review["rating"], "title": review["title"]}
        reviews_text.append(text)
        reviews_metadata.append(metadata)
    return reviews_text, reviews_metadata

# Generar embeddings de todas las reseñas
def get_embeddings(text_batch, chat_client: OpenAI, embedding_model):
    response = chat_client.embeddings.create(
        input=text_batch,
        model=embedding_model
    )
    return [item.embedding for item in response.data]

def make_embeddings_from_text(text, chat_client: OpenAI, embedding_model):
    reviews_embeddings = []
    batch_size = 100

    for i in range(0, len(text), batch_size):
        batch = text[i:i+batch_size]
        reviews_embeddings.extend(get_embeddings(batch, chat_client, embedding_model))
    return reviews_embeddings

def make_embedding_database(embeddings, text, metadata):
    # Configurar ChromaDB
    chroma_client = chromadb.PersistentClient(path="db/movies")
    collection_name = "reviews"

    # Borrar colección si ya existe
    if collection_name in [c.name for c in chroma_client.list_collections()]:
        chroma_client.delete_collection(name=collection_name)

    reviews_collection = chroma_client.create_collection(name=collection_name)

    # IDs únicos
    reviews_ids = [str(uuid.uuid4()) for _ in text]

    # Guardar embeddings en ChromaDB
    reviews_collection.add(
        ids=reviews_ids,
        embeddings=embeddings,
        documents=text,
        metadatas=metadata
    )

    return reviews_collection

# Función de búsqueda semántica, pasamos pregunta y db
def semantic_search(query, k, collection: chromadb.Collection, chat_client: OpenAI, embedding_model):
    query_embedding = get_embeddings([query], chat_client, embedding_model)[0]
    k = k
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    return results

# Función para mostrar reseñas en texto plano
def reviews_to_text(results):
    text_list = []

    for i in range(0, len(results['documents'][0])):
        # Metadatas tiene el título y nota
        metadata = results["metadatas"][0][i]
        # Document tiene el texto de la review
        document = results["documents"][0][i]

        print(metadata)
        title = metadata["title"]
        rating = metadata["rating"]

        text_list.append(f"Título:{title}, Nota:{rating}, Reseña: {document}")
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
No contestes preguntas que no sean sobre cine.
"""

# Función para generar respuesta
def generate_response(relevant_content, system_prompt, query, chat_client: OpenAI, chat_model):

    response = chat_client.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0
    )
    return response
"""
user_question = "Haz una resumen de la opinión general de la película basado en las críticas más profesionales."

# Obtener resultados semánticos
results = semantic_search(user_question, reviews_collection)
combined_content = "\n\n".join(results["documents"][0])

# Generar respuesta final usando el prompt del sistema
response = generate_response(combined_content)
print("\n")
print(response.choices[0].message.content)
print("\n")
"""