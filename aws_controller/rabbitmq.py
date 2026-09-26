from urllib.parse import quote

import requests

import config


def get_messages_ready() -> int:
    """查 gec-inference 這個 queue 目前有幾筆還沒被任何 worker 收走的訊息。

    對應 management UI 上 Queues 頁面看到的 "Ready" 欄位（不含已經被收走
    但還沒 ack 的 "Unacked"）——scale-up 判斷要看的是「還沒人在處理」的
    量，不是「總共卡在 queue 裡」的量。
    """
    vhost = quote(config.rabbitmq_vhost, safe="")
    queue = quote(config.celery_queue_name, safe="")
    url = f"{config.rabbitmq_management_url}/api/queues/{vhost}/{queue}"

    response = requests.get(
        url,
        auth=(config.rabbitmq_user, config.rabbitmq_password),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["messages_ready"]


if __name__ == "__main__":
    print(f"messages_ready = {get_messages_ready()}")
