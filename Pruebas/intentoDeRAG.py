#!/usr/bin/env python3
# Shebang: indica que se ejecute con Python 3 en sistemas tipo Unix/Linux (cof cof Mario cof cof)

"""
rag_gemini.py

Ejemplo de RAG (Retrieval-Augmented Generation) usando Gemini CLI con reseñas de IMDb.

Requisitos:
    - Tener Gemini CLI instalado y autenticado
    - Tener un archivo JSON de reseñas: pulpfiction_reviews.json

Uso:
    python rag_gemini.py
"""

# Importamos librerías necesarias
import subprocess  # Para ejecutar comandos externos (Gemini CLI)
import json        # Para cargar y manejar archivos JSON

# Definimos el archivo JSON que contiene las reseñas
JSON_FILE = "pulpfiction_reviews.json"

# -------------------- CARGAR RESEÑAS --------------------
with open(JSON_FILE, "r", encoding="utf-8") as f:
    # Abrimos el archivo JSON y lo cargamos en un diccionario de Python
    data = json.load(f)

# Extraemos solo el contenido de las reseñas que tengan texto
reviews = [r["content"] for r in data.get("reviews", []) if r.get("content")]

# Si no se encuentra ninguna reseña, salimos con un mensaje de error
if not reviews:
    raise SystemExit("ERROR: No se encontraron reseñas en el JSON")

# -------------------- FUNCIONES --------------------
def realizar_consulta(pregunta: str) -> str:
    """
    Ejecuta Gemini CLI con la pregunta proporcionada y devuelve la respuesta generada.
    """
    try:
        # Ejecuta el comando: gemini query <pregunta>
        resultado = subprocess.run(
            ["gemini", "query", pregunta],  # Comando y argumentos
            capture_output=True,            # Captura la salida estándar
            text=True,                      # Devuelve la salida como texto, no bytes
            check=True                      # Lanza excepción si el comando falla
        )
        return resultado.stdout  # Retorna la salida del comando (respuesta de Gemini)
    except subprocess.CalledProcessError as e:
        # Si hay un error al ejecutar Gemini CLI, devolvemos el mensaje de error
        return f"[ERROR] Gemini CLI falló:\n{e.stderr}"

# -------------------- INTERFAZ CLI --------------------
if __name__ == "__main__":
    # Solo se ejecuta si corremos este script directamente
    print("RAG con Gemini CLI listo. Escribe tu pregunta o 'salir' para terminar.")

    # Bucle principal para recibir preguntas del usuario
    while True:
        q = input("\nPregunta: ")  # Pedimos la pregunta al usuario
        if q.lower() in ("salir", "exit", "quit"):
            break  # Salimos del bucle si el usuario quiere terminar

        # Creamos un contexto simple con las 5 primeras reseñas (no quiero ampliarlo mas porque no me funciona lo otro asi que ni se si funciona este)
        context = "\n".join(reviews[:5])

        # Construimos el prompt que se le pasará a Gemini
        prompt = f"Usando estas reseñas:\n{context}\n\nResponde la pregunta: {q}"

        # Ejecutamos la consulta y obtenemos la respuesta
        respuesta = realizar_consulta(prompt)

        # Mostramos la respuesta en pantalla
        print("\nRespuesta RAG:\n", respuesta)
