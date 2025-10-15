#!/usr/bin/env python3
"""
ScriptScrapping.py

Obtiene reseñas de títulos IMDb usando un provider en RapidAPI (host configurable).
Lee RAPIDAPI_KEY y RAPIDAPI_HOST desde .env en la misma carpeta.

Guarda un JSON con:
{
  "meta": { ... },
  "count": N,
  "reviews": [ {id, author, date, rating, content, source}, ... ],
  "raw_example": <ejemplo de respuesta original (recortada) si se desea>
}

Uso:
  1) Crea .env en la misma carpeta con:
       RAPIDAPI_KEY=tu_rapidapi_key
       RAPIDAPI_HOST=imdb8.p.rapidapi.com
  2) Instala dependencias:
       pip install python-dotenv requests
  3) Ejecuta:
       python ScriptScrapping.py tt0110912 --max 500 --out pulpfiction_reviews.json
    (donde tt0110912 es el ID IMDb del título o un texto de búsqueda)

Notas:
- Revisa en RapidAPI (Playground) el host exacto y el endpoint que tu suscripción permite.
- Algunos providers usan rutas ligeramente diferentes; el script intenta varios nombres comunes.
- Respeta los límites de RapidAPI y tu plan (rate limits).
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests

# -------------------- CARGAR .env --------------------
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    raise SystemExit("ERROR: No se encontró el fichero .env. Crea uno en la misma carpeta con RAPIDAPI_KEY y RAPIDAPI_HOST.")

# carga variables de .env
load_dotenv(dotenv_path=env_path)
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
    raise SystemExit("ERROR: Faltan variables en .env. Asegúrate de tener RAPIDAPI_KEY y RAPIDAPI_HOST.")

# -------------------- ENDPOINTS POSIBLES --------------------
# Lista de endpoints que suelen ofrecer providers de IMDb en RapidAPI.
# El script los probará en orden hasta encontrar datos útiles.
COMMON_ENDPOINTS = [
    # (method, path, param_name)  where param_name is "tconst" or "q" or custom
    ("GET", "/title/get-user-reviews", "tconst"),
    ("GET", "/title/get-reviews", "tconst"),
    ("GET", "/title/get-critic-reviews", "tconst"),
    ("GET", "/title/get-critics-review-summary", "tconst"),
    ("GET", "/title/find", "q"),  # fallback: búsqueda por texto
]

# -------------------- HELPERS --------------------
def call_rapidapi(path: str, params: dict = None, method: str = "GET", timeout: int = 15):
    """
    Llama a https://{RAPIDAPI_HOST}{path} con headers x-rapidapi-key/host.
    Devuelve JSON (si status OK) o dict con '__error__' en caso de fallo.
    """
    base = f"https://{RAPIDAPI_HOST}"
    url = base + path
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        else:
            resp = requests.post(url, headers=headers, data=params, timeout=timeout)
        resp.raise_for_status()
        # intentar parsear JSON; si no es JSON, devolver texto en __error__
        try:
            return resp.json()
        except ValueError:
            return {"__error__": "Respuesta no JSON", "__text__": resp.text[:200]}
    except requests.RequestException as e:
        # incluir código HTTP si está disponible
        status = None
        text = None
        if e.response is not None:
            status = e.response.status_code
            try:
                text = e.response.text[:400]
            except Exception:
                text = None
        return {"__error__": str(e), "__status__": status, "__text__": text}

def extract_reviews_from_response(obj):
    """
    Heurística para extraer reseñas de distintas formas de respuesta.
    Devuelve lista de dicts normalizados: {id, author, date, rating, content, source}
    """
    reviews = []

    # Si la respuesta es lista -> iterar y mapear campos comunes
    if isinstance(obj, list):
        for item in obj:
            if not isinstance(item, dict):
                continue
            r = {
                "id": item.get("id") or item.get("reviewId") or item.get("uuid"),
                "author": item.get("author") or item.get("username") or item.get("reviewer") or item.get("displayName"),
                "date": item.get("date") or item.get("createdAt") or item.get("reviewDate"),
                "rating": item.get("rating") or item.get("score"),
                "content": item.get("content") or item.get("reviewText") or item.get("body") or item.get("plainText"),
                "source": item.get("source") or None
            }
            if r["content"] or r["author"]:
                reviews.append(r)
        if reviews:
            return reviews

    # Si es dict, buscar claves típicas
    if isinstance(obj, dict):
        # claves candidatas que suelen contener listas de reviews
        for key in ("reviews", "items", "results", "data", "entries"):
            val = obj.get(key)
            if isinstance(val, list):
                rlist = extract_reviews_from_response(val)
                if rlist:
                    return rlist
            if isinstance(val, dict):
                # si es mapa id->obj, convertir a lista
                rlist = extract_reviews_from_response(list(val.values()))
                if rlist:
                    return rlist

        # Si no encontramos listas, buscar strings largos en el JSON (posibles reviews embebidas)
        def find_long_strings(x):
            found = []
            if isinstance(x, dict):
                for v in x.values():
                    found.extend(find_long_strings(v))
            elif isinstance(x, list):
                for itm in x:
                    found.extend(find_long_strings(itm))
            elif isinstance(x, str):
                if len(x) > 120:
                    found.append({"id": None, "author": None, "date": None, "rating": None, "content": x, "source": None})
            return found

        found = find_long_strings(obj)
        if found:
            return found

    return []

# -------------------- LÓGICA PRINCIPAL --------------------
def try_endpoints(imdb_id_or_query: str, max_reviews: int = 500):
    """
    Prueba los endpoints definidos en COMMON_ENDPOINTS, pasando imdb_id_or_query
    como valor para el parámetro correspondiente (tconst o q).
    Devuelve dict con meta y reviews normalizados (limitados a max_reviews).
    """
    meta = {
        "queried": imdb_id_or_query,
        "host": RAPIDAPI_HOST,
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "tried": []
    }

    for method, path, paramname in COMMON_ENDPOINTS:
        # prepara parámetros
        params = {}
        params[paramname] = imdb_id_or_query

        meta["tried"].append({"path": path, "method": method, "params": params})
        print(f"[INFO] Probando {method} {path} con params {params} ...")

        resp = call_rapidapi(path, params=params, method=method)
        # si hay error de llamada, mostrar y continuar
        if isinstance(resp, dict) and resp.get("__error__"):
            print(f"[WARN] Endpoint {path} devolvió error: {resp.get('__error__')} (status {resp.get('__status__')})")
            # guardamos un ejemplo bruto por si quieres inspeccionar
            meta.setdefault("errors", []).append({"path": path, "error": resp.get("__error__"), "status": resp.get("__status__")})
            continue

        # extraer reseñas
        reviews = extract_reviews_from_response(resp)
        if reviews:
            # guardamos un ejemplo bruto corto para diagnóstico
            raw_example = resp if isinstance(resp, (dict, list)) else None
            # limitar
            reviews = reviews[:max_reviews]
            return {
                "meta": meta,
                "count": len(reviews),
                "reviews": reviews,
                "raw_example": (raw_example if raw_example is None else (raw_example if isinstance(raw_example, list) else (dict(list(raw_example.items())[:5]))))
            }

        # si no encuentra reviews, seguir probando con siguiente endpoint
        print(f"[INFO] Ninguna review encontrada en {path} (seguiré probando).")

    # si llegamos aquí, no encontramos reseñas
    return {"meta": meta, "count": 0, "reviews": [], "raw_example": None}

# -------------------- CLI --------------------
def main():
    parser = argparse.ArgumentParser(description="Obtener reseñas vía RapidAPI (IMDb providers). Lee .env para RAPIDAPI_KEY y RAPIDAPI_HOST.")
    parser.add_argument("imdb_id_or_query", help="ID IMDb (tt...) o texto de búsqueda (título)")
    parser.add_argument("--max", type=int, default=500, help="Máximo reseñas a guardar")
    parser.add_argument("--out", type=str, default=None, help="Fichero JSON de salida")
    args = parser.parse_args()

    result = try_endpoints(args.imdb_id_or_query, max_reviews=args.max)

    # nombre de salida por defecto
    outname = args.out or f"{args.imdb_id_or_query}_rapidapi_reviews.json"
    with open(outname, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Guardadas {result.get('count',0)} reseñas en {outname}")
    if result.get("count", 0) == 0:
        print("[INFO] No se encontraron reseñas. Revisa el Playground del provider en RapidAPI")
        print(f"[INFO] Host usado: {RAPIDAPI_HOST}")
        # si hay ejemplos de error, mostrarlos
        if result.get("meta", {}).get("errors"):
            print("[INFO] Errores detectados en llamadas previas (ver .json para detalles).")

if __name__ == "__main__":
    main()
