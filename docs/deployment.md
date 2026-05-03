# Deployment

Warpsmith поддерживает 3 сценария развёртывания: **Dokku**, **Railway** и **self-host (bare-metal)**.

---

## 1. Dokku

Dokku — минималистичный PaaS на Docker. Деплой через `git push`.

### Предварительно

- Сервер с Dokku (ubuntu + `wget -qO- https://dokku.com/install | bash`)
- Домен, направленный на сервер
- Letsencrypt плагин: `dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git`

### Настройка

```bash
# Скрипт автоматической настройки
./deploy/dokku-setup.sh warpsmith.example.com

# Или вручную:
git remote add dokku dokku@warpsmith.example.com:warpsmith
git push dokku main
```

Скрипт сделает:
- Создаст приложение `warpsmith`
- Настроит домен и SSL (letsencrypt)
- Смонтирует volume `/data` для SQLite
- Установит переменные HOSTING, DB_PATH

---

## 2. Railway

Railway — serverless платформа с интеграцией GitHub.

### Настройка

1. Создай аккаунт на [railway.app](https://railway.app)
2. Нажми **New Project → Deploy from GitHub repo**
3. Выбери `fixemer90-stack/Warpsmith`
4. Railway сам обнаружит `Procfile` и `Dockerfile`

### Переменные окружения (Railway Dashboard → Variables)

| Variable    | Value  |
|------------|--------|
| `HOSTING`  | `true` |
| `DB_PATH`  | `/data/simulator.db` |

Railway использует `deploy/railway.json` для конфигурации: Dockerfile build, healthcheck на `/`, restart on failure.

---

## 3. Self-host (bare-metal)

### Требования

- Ubuntu 22.04+ / Debian 12+
- Python 3.12+
- Nginx
- Certbot (Let's Encrypt)

### Установка

```bash
# Создать пользователя
sudo useradd -r -s /bin/bash -m warpsmith

# Скопировать проект
sudo mkdir /opt/warpsmith
sudo chown warpsmith:warpsmith /opt/warpsmith
sudo -u warpsmith git clone https://github.com/fixemer90-stack/Warpsmith.git /opt/warpsmith

# Виртуальное окружение
sudo -u warpsmith python3 -m venv /opt/warpsmith/.venv
sudo -u warpsmith /opt/warpsmith/.venv/bin/pip install -e /opt/warpsmith

# Директория для БД
sudo -u warpsmith mkdir -p /var/lib/warpsmith
```

### Systemd

```bash
sudo cp deploy/systemd.service /etc/systemd/system/warpsmith.service
sudo systemctl daemon-reload
sudo systemctl enable --now warpsmith.service
sudo systemctl status warpsmith.service
```

### Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name warpsmith.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo certbot --nginx -d warpsmith.example.com
```

---

## Переменные окружения

| Переменная | Описание | Production значение |
|-----------|----------|-------------------|
| `HOSTING` | Включает production-режим (отключает reload) | `true` |
| `DB_PATH` | Путь к SQLite базе | `/data/simulator.db` (volume) |
| `PORT` | Порт HTTP-сервера | `8000` |
| `ALLOWED_ORIGINS` | CORS origins (через запятую) | `https://ваш-домен.com` |
| `JWT_SECRET` | Секрет для JWT токенов | `openssl rand -hex 32` |

---

## Безопасность

- `JWT_SECRET` обязательно сменить: `openssl rand -hex 32`
- HTTPS через letsencrypt (Dokku) или certbot + nginx (self-host)
- SQLite volume монтируется отдельно, не в слое контейнера
- CORS ограничен через `ALLOWED_ORIGINS`
- Пользователь `warpsmith` без shell-доступа (systemd)

---

## Healthcheck и мониторинг

Dockerfile содержит встроенный healthcheck:
```
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

Логи:
```bash
# Dokku
dokku logs warpsmith -t

# Systemd
journalctl -u warpsmith.service -f

# Railway
Railway Dashboard → Deploy Logs
```

Uptime мониторинг: [uptimerobot.com](https://uptimerobot.com) — бесплатно до 50 мониторов.
