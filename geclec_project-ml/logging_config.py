"""共用的 JSON logging 設定，API process（main.py）跟 worker process
（celery_app.py，透過 Celery 的 setup_logging signal）都呼叫
`configure_logging()`，確保兩邊的 log 是同一種格式，方便之後接 Loki 用
`task_id` 這類欄位查詢。自己寫 formatter，不引入額外套件。

刻意不記錄使用者輸入的原始文字——log 裡只放 metadata（長度、task_id、
耗時、狀態），避免使用者的寫作內容留在集中式的 log 系統裡。

trace_id/span_id：如果這行 log 是在一個活躍的 OTel span 底下印出來的
（FastAPIInstrumentor／CeleryInstrumentor 都會建立 span，見
tracing_config.py），自動把目前的 trace_id/span_id 併進 JSON——這是讓
Grafana 能從 Tempo 的一個 trace 直接跳去查對應 Loki log 的關鍵（trace↔log
correlation），不用手動在兩邊分別查、拿 task_id 對。沒有活躍 span 時
（例如 process 啟動時的 log）不加這兩個欄位，不要塞一個沒有意義的全零
trace_id 進去。
"""
import json
import logging
import traceback

from opentelemetry import trace

_RESERVED_LOG_RECORD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()) | {"message"}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        span_context = trace.get_current_span().get_span_context()
        if span_context.is_valid:
            payload["trace_id"] = format(span_context.trace_id, "032x")
            payload["span_id"] = format(span_context.span_id, "016x")
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
