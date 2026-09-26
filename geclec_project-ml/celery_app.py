import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from celery import Celery
from celery.signals import worker_init, worker_ready, setup_logging
from opentelemetry.instrumentation.celery import CeleryInstrumentor

import main_config
from logging_config import configure_logging
from tracing_config import configure_tracing


@setup_logging.connect
def _configure_worker_logging(**kwargs):
    # 接管 Celery 的 logging 設定，讓 worker 的 log（包含 Celery 自己印的
    # task 成功/失敗訊息）跟 API process 用同一種 JSON 格式，共用
    # logging_config.py。連上這個 signal 之後 Celery 就不會再套用自己的
    # 預設 logging 設定，不會有 handler 重複、log 印兩次的問題。
    configure_logging()

celery_app = Celery(
    "geclec_project-ml",
    broker=main_config.celeryBrokerUrl,
    backend="rpc://",  # 結果透過 RabbitMQ 的 rpc:// result backend 取回，用 task_id 領取，不用自己管 pub/sub
    include=["tasks"],
)

celery_app.conf.update(
    task_default_queue=main_config.celeryQueueName,
    # late ack：任務處理完成（成功或失敗）才 ack。RabbitMQ 是原生 AMQP
    # broker，worker process 若中途斷線（OOM/SIGKILL），未 ack 的訊息會被
    # broker 自動重新投遞給其他 consumer——這是 AMQP 內建行為，不像 Redis
    # broker 需要另外設定 visibility_timeout 模擬。預設的 early ack 只有
    # at-most-once，沒有這個保障。
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # 搭配 late ack：避免一個 worker 預先搶走多筆任務，斷線時要重派一大批
)


# --- 健康檢查（K8s startupProbe/readinessProbe/livenessProbe 用，見
#     kubernetes/base/05-local-gpu-worker.yaml）---
# Celery 沒有內建 HTTP health endpoint，這裡起一個最小的背景 HTTP server：
# process 活著就能回 /healthz/live；worker_ready signal（worker 完成啟動、
# 開始能接任務）觸發前，/healthz/ready、/healthz/startup 回 503。
#
# 刻意掛在 worker_init（只有真的執行 `celery ... worker` 才會觸發），不是
# module 頂層直接呼叫——main.py（API process）也會 import 這個檔案拿
# celery_app 物件送任務，如果頂層就啟動 server，API container 會平白多開一個
# 用不到、且 worker_ready 永遠不會觸發（一直回 503）的健康檢查埠。
_ready = False


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz/live":
            self.send_response(200)
            self.end_headers()
        elif self.path in ("/healthz/ready", "/healthz/startup"):
            self.send_response(200 if _ready else 503)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def _start_health_server(port=9090):
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


@worker_init.connect
def _on_worker_init(**kwargs):
    # 跟健康檢查 server 同樣的理由掛在 worker_init：main.py（API process）
    # 也會 import 這個檔案拿 celery_app 物件送任務，tracing 的初始化（service
    # name 是 "local-gpu-worker"）只該在真的執行 `celery ... worker` 時發生。
    # CeleryInstrumentor 這裡負責從 task 的 message header 還原 API process
    # 送出時寫入的 trace context，讓兩邊的 span 屬於同一個 trace，見
    # tracing_config.py 開頭的說明。
    configure_tracing("local-gpu-worker")
    CeleryInstrumentor().instrument()
    _start_health_server()


@worker_ready.connect
def _on_worker_ready(**kwargs):
    global _ready
    _ready = True
