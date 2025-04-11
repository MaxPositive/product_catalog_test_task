# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt
COPY requirements.txt ./

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY product_catalog/ ./product_catalog/
COPY alembic.ini ./
COPY docker.env ./.env
COPY run.sh ./


RUN chmod +x run.sh

RUN touch /app/product_catalog.db

# Установка переменной окружения PYTHONPATH
ENV PYTHONPATH=/app

# Открытие порта для FastAPI
EXPOSE 8000

# Команда по умолчанию (будет переопределена в docker-compose.yml)
CMD ["./run.sh"]