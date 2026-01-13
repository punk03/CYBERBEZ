# API Документация

## Базовый URL

```
http://localhost:8000/api/v1
```

## Аутентификация

Большинство endpoints требуют аутентификации через JWT токены.

```
Authorization: Bearer <token>
```

## Endpoints

### Health Checks

#### GET /health
Проверка здоровья системы

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "postgresql": {"status": "healthy"},
    "mongodb": {"status": "healthy"}
  }
}
```

### Logs

#### POST /logs
Отправка лога в систему

**Request**:
```json
{
  "log": "{\"message\": \"test\", \"level\": \"INFO\"}",
  "source": "api",
  "format": "json",
  "metadata": {}
}
```

#### GET /logs
Получение списка логов

**Query Parameters**:
- `limit` (int): Максимум логов (default: 100)
- `skip` (int): Пропустить N логов (default: 0)
- `source` (string): Фильтр по источнику

### Threats

#### GET /threats
Получение списка обнаруженных угроз

**Query Parameters**:
- `limit` (int): Максимум угроз
- `skip` (int): Пропустить N угроз
- `attack_type` (string): Фильтр по типу атаки
- `severity` (string): Фильтр по критичности

#### GET /threats/{threat_id}
Получение деталей конкретной угрозы

#### GET /threats/stats/summary
Статистика по угрозам

### Automation

#### POST /automation/execute
Выполнение автоматизации для угрозы

**Request**:
```json
{
  "detection": {...},
  "auto_approve": false
}
```

#### GET /automation/approvals
Получение ожидающих подтверждения запросов

#### POST /automation/approvals/{approval_id}/approve
Подтверждение действия

#### POST /automation/approvals/{approval_id}/reject
Отклонение действия

#### GET /automation/status
Статус системы автоматизации

### Alerts

#### POST /alerts
Создание и отправка алерта

**Request**:
```json
{
  "title": "Alert title",
  "message": "Alert message",
  "severity": "high",
  "source": "system",
  "channels": ["email", "slack"]
}
```

#### GET /alerts
Получение списка алертов

#### POST /alerts/{alert_id}/resolve
Отметить алерт как решенный

### Audit

#### GET /audit
Получение аудит логов (требует аутентификации)

**Query Parameters**:
- `user` (string): Фильтр по пользователю
- `action` (string): Фильтр по действию
- `resource` (string): Фильтр по ресурсу
- `limit` (int): Максимум логов

### Metrics

#### GET /metrics
Prometheus metrics endpoint

## Swagger Documentation

Интерактивная документация доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
