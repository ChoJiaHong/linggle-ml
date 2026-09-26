"""AWS overflow controller — 查詢階段（見 readme 八）。

目前只做「查」，不做「決策＋執行」：印出 RabbitMQ backlog 跟目前有幾台
AWS GPU worker 在跑，讓人工核對這兩個數字跟 RabbitMQ management UI／AWS
Console 看到的是否一致。scale-up/down 邏輯等這一步驗證過再加。
"""

from aws_ec2 import list_running_workers
from rabbitmq import get_messages_ready


def main():
    messages_ready = get_messages_ready()
    workers = list_running_workers()

    print(f"messages_ready = {messages_ready}")
    print(f"running_workers = {len(workers)}")
    for worker in workers:
        print(f"  {worker.instance_id}  {worker.state}  launched_at={worker.launched_at}")


if __name__ == "__main__":
    main()
