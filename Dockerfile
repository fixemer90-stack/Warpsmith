FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

# JSON-форма с exec — сигналы доходят до uvicorn, ${PORT} раскрывается
CMD ["sh", "-c", "exec uvicorn main:app --host :: --port ${PORT} --log-level info --timeout-keep-alive 5"]
