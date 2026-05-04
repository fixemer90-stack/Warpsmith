FROM python:3.12-slim-bookworm

WORKDIR /app

# Копируем и устанавливаем зависимости (слой кешируется)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Railway сам пробросит PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
