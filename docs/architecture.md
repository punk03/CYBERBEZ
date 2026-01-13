# Архитектура системы PROKVANT

## Обзор

PROKVANT - это комплексная система для анализа логов и защиты энергосистем, построенная на микросервисной архитектуре.

## Архитектурные принципы

1. **Микросервисная архитектура** - независимые, масштабируемые компоненты
2. **Event-driven** - обработка событий в реальном времени
3. **Horizontal scaling** - горизонтальное масштабирование всех компонентов
4. **Fault tolerance** - устойчивость к сбоям
5. **Security by design** - безопасность на всех уровнях

## Компоненты системы

### 1. Data Ingestion Layer

**Назначение**: Сбор логов из различных источников

**Компоненты**:
- Syslog receiver (UDP порт 514)
- File watchers для мониторинга файлов
- API endpoints для приема логов
- Парсеры для различных форматов

**Технологии**: Python, asyncio, watchdog

### 2. Stream Processing Layer

**Назначение**: Обработка данных в реальном времени

**Компоненты**:
- Kafka для streaming
- Stream processors
- Enrichers (GeoIP, Threat Intel, Asset Info)
- Filters и aggregators

**Технологии**: Apache Kafka, aiokafka

### 3. Storage Layer

**Назначение**: Многоуровневое хранение данных

**Компоненты**:
- TimescaleDB для time-series данных
- MongoDB для структурированных логов
- Elasticsearch для поиска
- MinIO/S3 для cold storage

**Стратегия**: Hot/Warm/Cold storage

### 4. ML/AI Engine

**Назначение**: Обнаружение аномалий и классификация атак

**Компоненты**:
- Feature extraction
- Anomaly detection (Isolation Forest)
- Attack classification (Random Forest)
- Ensemble models
- Real-time inference

**Технологии**: scikit-learn, TensorFlow/PyTorch, MLflow

### 5. Attack Detection System

**Назначение**: Обнаружение различных типов атак

**Детекторы**:
- DDoS
- Malware
- SCADA attacks
- Insider threats
- Network intrusion
- APT
- Ransomware
- Zero-day

### 6. Automation Engine

**Назначение**: Автоматическое реагирование на угрозы

**Компоненты**:
- Network isolation
- Device quarantine
- Traffic blocking
- Failover activation
- Approval workflow

### 7. API Gateway

**Назначение**: REST API для доступа к системе

**Endpoints**:
- `/api/v1/logs` - работа с логами
- `/api/v1/threats` - управление угрозами
- `/api/v1/automation` - автоматизация
- `/api/v1/alerts` - алерты
- `/api/v1/audit` - аудит логи

### 8. Web Dashboard

**Назначение**: Пользовательский интерфейс

**Страницы**:
- Dashboard - обзор системы
- Threats - управление угрозами
- Logs - просмотр логов
- Automation - управление автоматизацией
- Settings - настройки

### 9. Alerting System

**Назначение**: Уведомления о событиях

**Каналы**:
- Email
- Slack
- Webhook
- Dashboard alerts

### 10. Monitoring

**Назначение**: Мониторинг системы

**Компоненты**:
- Prometheus метрики
- Health checks
- Distributed tracing (планируется)

## Поток данных

1. Логи поступают из источников
2. Коллекторы собирают и парсят логи
3. Данные нормализуются
4. Отправка в Kafka
5. Stream processing с обогащением
6. ML prediction
7. Attack detection
8. Automation (если требуется)
9. Alerting
10. Сохранение в БД

## Масштабирование

- **Горизонтальное**: Все компоненты могут масштабироваться
- **Вертикальное**: Увеличение ресурсов серверов
- **Auto-scaling**: Автоматическое масштабирование (планируется)

## Безопасность

- Шифрование данных
- Аутентификация и авторизация
- Аудит всех действий
- Соответствие стандартам (IEC 62443, NIST)

## Развертывание

- **Development**: Docker Compose
- **Production**: Kubernetes
- **Edge**: Edge computing для обработки на месте
