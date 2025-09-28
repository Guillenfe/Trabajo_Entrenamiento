# 🎬 Sistema de Perfilado de Usuario para Recomendación de Películas

Este proyecto construyemos un **perfil de usuario basado en ratings de películas**, con el objetivo de identificar los géneros y características más relevantes.  
Está pensado como un paso inicial hacia un **sistema de recomendación de películas**.

---

## 📂 Datos

- `movies_curated.csv`: información de películas (título, año, géneros, directores, guionistas).  
- `ratings.csv`: calificaciones del usuario (película, año, rating).  

---

## ⚙️ Proceso

1. Limpieza y preparación de datos.  
2. Codificación de géneros y equipo con *one-hot encoding*.  
3. Construcción de un vector de usuario a partir de sus ratings.  
4. Normalización y ordenamiento de características.  
5. Visualización de los **géneros más representativos** en una gráfica.  

---

## 📊 Resultado

El notebook muestra una **gráfica de barras** con los géneros que mejor describen el perfil del usuario según sus calificaciones.  

---

## 🚀 Requisitos

Este proyecto usa [uv](https://github.com/astral-sh/uv) para la gestión de dependencias en Python.  

Instalar dependencias:  

```bash
uv pip install pandas numpy scikit-learn scipy matplotlib
