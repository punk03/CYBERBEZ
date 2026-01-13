"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Histogram, Gauge, Summary
from typing import Dict, Any

# Metrics for log processing
logs_processed_total = Counter(
    'prokvant_logs_processed_total',
    'Total number of logs processed',
    ['source', 'status']
)

log_processing_duration = Histogram(
    'prokvant_log_processing_duration_seconds',
    'Time spent processing logs',
    ['source']
)

# Metrics for threat detection
threats_detected_total = Counter(
    'prokvant_threats_detected_total',
    'Total number of threats detected',
    ['attack_type', 'severity']
)

threat_detection_duration = Histogram(
    'prokvant_threat_detection_duration_seconds',
    'Time spent detecting threats'
)

# Metrics for ML predictions
ml_predictions_total = Counter(
    'prokvant_ml_predictions_total',
    'Total number of ML predictions',
    ['model_type', 'result']
)

ml_prediction_duration = Histogram(
    'prokvant_ml_prediction_duration_seconds',
    'Time spent on ML predictions'
)

# Metrics for automation
automation_actions_total = Counter(
    'prokvant_automation_actions_total',
    'Total number of automation actions',
    ['action_type', 'status']
)

automation_action_duration = Histogram(
    'prokvant_automation_action_duration_seconds',
    'Time spent executing automation actions',
    ['action_type']
)

# Metrics for alerts
alerts_sent_total = Counter(
    'prokvant_alerts_sent_total',
    'Total number of alerts sent',
    ['channel', 'severity']
)

# System metrics
active_connections = Gauge(
    'prokvant_active_connections',
    'Number of active connections'
)

queue_depth = Gauge(
    'prokvant_queue_depth',
    'Depth of processing queue',
    ['queue_name']
)

kafka_messages_consumed = Counter(
    'prokvant_kafka_messages_consumed_total',
    'Total number of Kafka messages consumed',
    ['topic']
)

kafka_messages_produced = Counter(
    'prokvant_kafka_messages_produced_total',
    'Total number of Kafka messages produced',
    ['topic']
)

# Database metrics
db_operations_total = Counter(
    'prokvant_db_operations_total',
    'Total number of database operations',
    ['operation', 'database', 'status']
)

db_operation_duration = Histogram(
    'prokvant_db_operation_duration_seconds',
    'Time spent on database operations',
    ['operation', 'database']
)

# ML model metrics
ml_model_accuracy = Gauge(
    'prokvant_ml_model_accuracy',
    'ML model accuracy',
    ['model_name']
)

ml_model_false_positive_rate = Gauge(
    'prokvant_ml_model_false_positive_rate',
    'ML model false positive rate',
    ['model_name']
)


def record_log_processed(source: str, status: str, duration: float) -> None:
    """Record log processing metric."""
    logs_processed_total.labels(source=source, status=status).inc()
    log_processing_duration.labels(source=source).observe(duration)


def record_threat_detected(attack_type: str, severity: str, duration: float) -> None:
    """Record threat detection metric."""
    threats_detected_total.labels(attack_type=attack_type, severity=severity).inc()
    threat_detection_duration.observe(duration)


def record_ml_prediction(model_type: str, result: str, duration: float) -> None:
    """Record ML prediction metric."""
    ml_predictions_total.labels(model_type=model_type, result=result).inc()
    ml_prediction_duration.observe(duration)


def record_automation_action(action_type: str, status: str, duration: float) -> None:
    """Record automation action metric."""
    automation_actions_total.labels(action_type=action_type, status=status).inc()
    automation_action_duration.labels(action_type=action_type).observe(duration)


def record_alert_sent(channel: str, severity: str) -> None:
    """Record alert sent metric."""
    alerts_sent_total.labels(channel=channel, severity=severity).inc()


def update_queue_depth(queue_name: str, depth: int) -> None:
    """Update queue depth metric."""
    queue_depth.labels(queue_name=queue_name).set(depth)


def update_ml_model_metrics(model_name: str, accuracy: float, false_positive_rate: float) -> None:
    """Update ML model metrics."""
    ml_model_accuracy.labels(model_name=model_name).set(accuracy)
    ml_model_false_positive_rate.labels(model_name=model_name).set(false_positive_rate)
