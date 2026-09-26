import os

# --- RabbitMQ management API（查 backlog 用，跟 Celery 走的 AMQP 是同一個
#     RabbitMQ，但走 15672 這個 HTTP port，不是 5672）---
# 預設值對應 controller 實際跑在叢集裡時用的內部 DNS（見
# kubernetes/base/10-rabbitmq-debug-ingress.yaml 的說明：controller 不需要
# 外部能連到的 endpoint）。本機開發時用外部的除錯 Ingress 覆寫這個值。
rabbitmq_management_url = os.environ.get(
    "RABBITMQ_MANAGEMENT_URL", "http://rabbitmq.gec.svc.cluster.local:15672"
)
rabbitmq_vhost = os.environ.get("RABBITMQ_VHOST", "/")
rabbitmq_user = os.environ.get("RABBITMQ_USER", "guest")
rabbitmq_password = os.environ.get("RABBITMQ_PASSWORD", "guest")
celery_queue_name = os.environ.get("CELERY_QUEUE_NAME", "gec-inference")

# --- AWS EC2（開/關 GPU worker 用）---
# tag 值對應 terraform/variables.tf 的 project_name（預設 "gec"）跟
# terraform/ec2_worker.tf 幫 instance 打的 Role tag（"aws-gpu-worker"）——
# controller 靠這兩個 tag 篩選出「屬於自己管的」instance，不會誤動到帳號
# 裡其他跟這個專案無關的 EC2。
aws_region = os.environ.get("AWS_REGION", "ap-northeast-1")
aws_project_tag = os.environ.get("AWS_PROJECT_TAG", "gec")
aws_worker_role_tag = os.environ.get("AWS_WORKER_ROLE_TAG", "aws-gpu-worker")
