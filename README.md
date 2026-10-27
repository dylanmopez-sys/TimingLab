# Timing Lab

Demostración académica de un canal encubierto temporal sobre solicitudes HTTP.

## Ejecutar localmente

1. Instalar Python 3.
2. En una terminal dentro de esta carpeta ejecutar:

   ```bash
   python -m pip install -r requirements.txt
   python app.py
   ```

3. Abrir `http://127.0.0.1:8000`.

## Publicar en Render

1. Subí estos archivos a un repositorio de GitHub.
2. En Render, elegí **New + → Blueprint** y conectá el repositorio.
3. Render leerá `render.yaml` para instalar las dependencias y arrancar Flask.

También podés crear un Web Service manual con:
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`

## Limitaciones

- La versión web codifica bits con los intervalos entre solicitudes HTTP genéricas; no envía el texto completo en cada evento.
- La latencia y planificación de la red pueden introducir errores. La precisión se calcula comparando localmente los bits recuperados con el mensaje original.
- Las sesiones se guardan en memoria y se pierden si el proceso se reinicia. Está diseñado para una demostración corta, no para producción.
- El plan gratuito de Render puede suspenderse cuando no se usa.
- `emisor.py` y `receptor.py` son la prueba UDP local original. Un alojamiento web gratuito no garantiza recepción UDP arbitraria.
