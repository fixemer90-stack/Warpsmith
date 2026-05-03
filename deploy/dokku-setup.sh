#!/usr/bin/env bash
# deploy/dokku-setup.sh — настроить Dokku-приложение для Warpsmith
# Использование: ./deploy/dokku-setup.sh [domain]
set -euo pipefail

APP="warpsmith"
DOMAIN="${1:-warpsmith.example.com}"

echo "→ Создание приложения $APP..."
dokku apps:create "$APP" || true

echo "→ Настройка домена $DOMAIN..."
dokku domains:set "$APP" "$DOMAIN"
dokku letsencrypt:enable "$APP" || echo "⚠ letsencrypt не включён — возможно, не установлен плагин"

echo "→ Монтирование volume для SQLite..."
dokku storage:ensure-directory "$APP-data"
dokku storage:mount "$APP" /var/lib/dokku/data/storage/"$APP-data":/data

echo "→ Переменные окружения..."
dokku config:set "$APP" HOSTING=true DB_PATH=/data/simulator.db

echo "→ Dockerfile деплой..."
dokku builder:set "$APP" selected dockerfile

echo ""
echo "✓ Готово. Для деплоя выполни:"
echo "  git remote add dokku dokku@$DOMAIN:$APP"
echo "  git push dokku main"
