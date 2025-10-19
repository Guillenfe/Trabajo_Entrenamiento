#!/usr/bin/env python3
"""
rag_gemini.py

Ejemplo de RAG usando Gemini CLI con reseñas de IMDb.

Requisitos:
    - Tener Gemini CLI instalado y autenticado
    - Tener un archivo JSON de reseñas: pulpfiction_reviews.json

Uso:
    python rag_gemini.py
"""

import subprocess
import json

JSON_FILE = "pulpfiction_reviews.json"

# -------------------- CARGAR RESEÑAS --------------------
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

reviews = [r["content"] for r in data.get("reviews", []) if r.get("content")]

if not reviews:
    raise SystemExit("ERROR: No se encontraron reseñas en el JSON")

# -------------------- FUNCIONES --------------------
def realizar_consulta(pregunta: str) -> str:
    """
    Ejecuta Gemini CLI con la pregunta.
    Devuelve la respuesta generada.
    """
    try:
        resultado = subprocess.run(
            ["gemini", "query", pregunta],
            capture_output=True,
            text=True,
            check=True
        )
        return resultado.stdout
    except subprocess.CalledProcessError as e:
        return f"[ERROR] Gemini CLI falló:\n{e.stderr}"

# -------------------- INTERFAZ CLI --------------------
if __name__ == "__main__":
    print("RAG con Gemini CLI listo. Escribe tu pregunta o 'salir' para terminar.")

    while True:
        q = input("\nPregunta: ")
        if q.lower() in ("salir", "exit", "quit"):
            break

        # Crear contexto con las 5 reseñas más relevantes (simple)
        context = "\n".join(reviews[:5])
        prompt = f"Usando estas reseñas:\n{context}\n\nResponde la pregunta: {q}"

        respuesta = realizar_consulta(prompt)
        print("\nRespuesta RAG:\n", respuesta)
