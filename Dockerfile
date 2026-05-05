FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

# Shell-форма — переменная раскроется
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT}"
