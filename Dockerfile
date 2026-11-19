# --- Stage 1: Frontend bauen ---
FROM node:22-alpine AS frontend
WORKDIR /fe
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- Stage 2: Backend + gebautes Frontend ---
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY templates ./templates
COPY --from=frontend /fe/dist ./web/dist
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]