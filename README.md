# 🎬 Sistema de Perfilado de Usuario para Recomendación de Películas

Este proyecto construyemos un **perfil de usuario basado en ratings de películas**, con el objetivo de identificar los géneros y características más relevantes.  
Está pensado como un paso inicial hacia un **sistema de recomendación de películas** , el cuál integraremos como parte de una página web de películas y series como 
servicio .

---

## 📂 Datos

- `movies_curated.csv`: información de películas (título, año, géneros, directores, guionistas).  
- `ratings.csv`: calificaciones del usuario (película, año, rating).  

---

## ⚙️ Proceso

1. Limpieza y preparación de datos.  
2. Codificación de géneros y equipo con *one-hot encoding* para convertir categorías en vectores numéricos.  
3. Construcción de un vector de usuario a partir de sus ratings.  
4. Normalización y ordenamiento de características.  
5. Visualización de los **géneros más representativos** en una gráfica.  

---

## 📊 Resultados

Gráficas que muestran los géneros más representativos del usuario según sus calificaciones.

Un modelo inicial de recomendación de películas basado en similitud de características.

---

## 🚀 Requisitos

Este proyecto usa [uv](https://github.com/astral-sh/uv) para la gestión de dependencias en Python.  

Instalar dependencias:  

```bash
uv pip install pandas numpy scikit-learn scipy matplotlib
```

Clonar el repo: 

```bash
git clone https://github.com/Guillenfe/Trabajo_Entrenamiento.git
cd Trabajo_Entrenamiento
```
Instala las dependencias con uv:

```bash
uv sync
```




