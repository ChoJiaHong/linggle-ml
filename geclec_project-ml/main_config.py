import os

origins = ["https://gec-fe.s3.amazonaws.com", "https://w.linggle.com", "*"]

# Inference API 不載入模型，透過 Celery（RabbitMQ 當 broker）把實際推論工作
# 交給 local-gpu-worker；worker 算完的結果也是透過 RabbitMQ 的 rpc:// result
# backend 送回來（見 tasks.py／celery_app.py），呼叫端用 send_task() 拿到的
# task_id 去領結果——broker 跟結果回傳共用同一套 RabbitMQ，不用額外維護
# 第二套訊息系統，也不用自己管理 pub/sub。
rabbitmqHost = os.environ.get("RABBITMQ_HOST", "rabbitmq")
rabbitmqPort = int(os.environ.get("RABBITMQ_PORT", "5672"))
rabbitmqVhost = os.environ.get("RABBITMQ_VHOST", "/")
rabbitmqUser = os.environ.get("RABBITMQ_USER", "guest")
rabbitmqPassword = os.environ.get("RABBITMQ_PASSWORD", "guest")

celeryBrokerUrl = os.environ.get(
    "CELERY_BROKER_URL",
    f"amqp://{rabbitmqUser}:{rabbitmqPassword}@{rabbitmqHost}:{rabbitmqPort}/{rabbitmqVhost}",
)
celeryQueueName = os.environ.get("CELERY_QUEUE_NAME", "gec-inference")

# /predict、/predict_login 對外仍是同步 API：內部送一個 Celery task，用
# task_id 向 result backend 領結果，逾時就回 503。
predictSyncTimeoutSeconds = float(os.environ.get("PREDICT_SYNC_TIMEOUT_SECONDS", "20"))

# Distributed tracing：span 直接用 OTLP gRPC 送給 Tempo，見 tracing_config.py
otelExporterOtlpEndpoint = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.observability.svc.cluster.local:4317"
)
