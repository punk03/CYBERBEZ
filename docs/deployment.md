# Руководство по развертыванию PROKVANT

## Развертывание на Ubuntu Server 24.04

### Предварительные требования

1. **Системные требования**:
   - Ubuntu Server 24.04 LTS
   - Минимум 8GB RAM
   - Минимум 100GB свободного места
   - Минимум 4 CPU cores

2. **Установленные пакеты**:
   - Docker
   - Docker Compose
   - Python 3.11+
   - Git
   - PostgreSQL client tools
   - MongoDB client tools

### Установка зависимостей

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose-plugin -y

# Установка Python и зависимостей
sudo apt install python3.11 python3.11-venv python3-pip -y

# Установка клиентов БД
sudo apt install postgresql-client mongodb-clients -y
```

### Развертывание системы

1. **Клонирование репозитория**:
```bash
git clone https://github.com/punk03/CYBERBEZ.git
cd PROKVANT
```

2. **Настройка окружения**:
```bash
cp .env.example .env
# Отредактировать .env файл с нужными настройками
nano .env
```

3. **Запуск инфраструктуры**:
```bash
docker-compose up -d
```

4. **Ожидание готовности сервисов**:
```bash
# Проверить статус
docker-compose ps

# Проверить логи
docker-compose logs -f
```

5. **Применение миграций БД**:
```bash
# Подключиться к PostgreSQL
docker-compose exec postgres psql -U prokvant -d prokvant_db

# Применить миграции TimescaleDB
\i backend/storage/migrations/001_create_timescale_tables.sql
```

6. **Установка Python зависимостей**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

7. **Запуск приложения**:
```bash
# Backend API
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend (в другом терминале)
cd frontend
npm install
npm run dev
```

### Настройка как системного сервиса

Создать systemd service для backend:

```bash
sudo nano /etc/systemd/system/prokvant-api.service
```

```ini
[Unit]
Description=PROKVANT API Service
After=network.target

[Service]
Type=simple
User=prokvant
WorkingDirectory=/path/to/PROKVANT/backend
Environment="PATH=/path/to/PROKVANT/backend/venv/bin"
ExecStart=/path/to/PROKVANT/backend/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Активировать сервис:
```bash
sudo systemctl enable prokvant-api
sudo systemctl start prokvant-api
```

### Настройка Nginx (опционально)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Настройка SSL (опционально)

Использовать Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### Проверка развертывания

1. Проверить health check:
```bash
curl http://localhost:8000/api/v1/health
```

2. Проверить метрики:
```bash
curl http://localhost:8000/metrics
```

3. Открыть веб-интерфейс:
```
http://your-server:3000
```

## Обновление системы

1. Остановить сервисы
2. Создать бэкап
3. Обновить код: `git pull`
4. Обновить зависимости
5. Применить миграции (если есть)
6. Перезапустить сервисы

## Масштабирование

### Горизонтальное масштабирование

Запустить несколько экземпляров backend за load balancer.

### Вертикальное масштабирование

Увеличить ресурсы сервера (CPU, RAM, диск).

## Мониторинг развертывания

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (если настроена)
- Health checks: `http://localhost:8000/api/v1/health`
