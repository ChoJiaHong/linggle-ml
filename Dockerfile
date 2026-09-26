# 兩個 build target 分出兩個各自獨立的 image：
#   docker build --target api    -t hiro08081/linggle-ml:api-N    .
#   docker build --target worker -t hiro08081/linggle-ml:worker-N .
#
# 為什麼要分：inference-api 完全不 import tasks.py／model.inference／
# model.translation（實際推論只在 local-gpu-worker 裡發生，見
# gec/kubernetes/base/04-inference-api.yaml／05-local-gpu-worker.yaml 開頭
# 的說明），已經用 grep 確認過 main.py 整條 import 鏈不碰 torch/
# transformers/nltk/sentencepiece——inference-api 卻一直跟 worker 共用同一個
# 3GB+ 的 image，等於每個 API replica 都白白帶著一份用不到的 ML 套件。拆開
# 後 api image 只有 requirements.txt 那些輕量套件，體積小很多、pull/啟動
# 都快。
#
# base 這個 stage 只裝 requirements.txt（兩邊都要的輕量套件：fastapi／
# celery／opentelemetry 這些），是兩個 target 共用的部分，避免兩份
# Dockerfile 內容重複。
FROM python:3.8 AS base

WORKDIR /

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt


FROM base AS api

COPY ./geclec_project-ml /geclec_project-ml
EXPOSE 80
CMD ["uvicorn", "geclec_project-ml.main:app", "--host", "0.0.0.0", "--port", "80"]


FROM base AS worker

# requirements-ml.txt（torch/transformers 這層本身就 2GB+）跟 app code
# 的 COPY 順序刻意這樣排：Docker layer cache 是「前一層 + 這個指令」的
# hash chain，只要放在 app code COPY 之前，之後改程式碼（會很常發生，例如
# 這次在除錯 OTel tracing）重新 build 就不會讓這層重跑、不用重新下載
# torch；如果放在 app code COPY 之後，程式碼一改就會連帶讓這層快取失效，
# 分層等於白做。
COPY ./requirements-ml.txt /requirements-ml.txt
RUN pip install --no-cache-dir --upgrade -r /requirements-ml.txt

COPY ./geclec_project-ml /geclec_project-ml
CMD ["celery", "-A", "geclec_project-ml.celery_app", "worker", "--loglevel=info", "--pool=solo"]
