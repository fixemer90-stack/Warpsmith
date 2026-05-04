FROM python:3.12-slim-bookworm

WORKDIR /app

# Копируем и устанавливаем зависимости (слой кешируется)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Railway пробрасывает PORT через railway.json startCommand
# Для локального запуска — явный порт
ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
