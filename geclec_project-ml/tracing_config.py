"""共用的 OpenTelemetry tracing 設定，API process（main.py）跟 worker
process（celery_app.py）都呼叫 `configure_tracing(service_name)`，把 span
用 OTLP gRPC 直接送給 Tempo（見 main_config.otelExporterOtlpEndpoint），
不經過額外的 OpenTelemetry Collector。

context propagation 跨 process 的部分：FastAPI 進來的 HTTP 請求靠
FastAPIInstrumentor 自動處理（標準 W3C traceparent header）；但 API
process 送 Celery task 給 worker process 是透過 RabbitMQ 訊息、不是 HTTP
呼叫，context 不會自動帶過去——這裡需要 opentelemetry-instrumentation-celery
（CeleryInstrumentor），它會在 task 送出時把目前的 trace context 寫進
Celery message header，worker 收到後從 header 還原 context，兩邊的 span
才會屬於同一個 trace。這個套件在 API process（送任務那端）跟 worker
process（執行任務那端）都要呼叫 `CeleryInstrumentor().instrument()`，
只裝一邊沒有用。
"""
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

import main_config


def configure_tracing(service_name):
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    exporter = OTLPSpanExporter(endpoint=main_config.otelExporterOtlpEndpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
