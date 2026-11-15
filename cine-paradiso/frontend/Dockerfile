# Dockerfile para Frontend Cine Paradiso (Web Flask con Jinja2)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ ./frontend/
COPY .env.example .env

ENV PYTHONUNBUFFERED=1
ENV FRONTEND_HOST=0.0.0.0
ENV FRONTEND_PORT=5001
ENV BACKEND_API_URL=http://backend:5000

EXPOSE 5001

CMD ["python", "frontend/app.py"]
