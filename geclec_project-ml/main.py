import logging
from typing import Union
from fastapi import FastAPI, status, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from service import text_pretention
import main_config
from auth import auth
from celery_app import celery_app
from logging_config import configure_logging
from tracing_config import configure_tracing

configure_logging()
logger = logging.getLogger(__name__)

configure_tracing("inference-api")
# 這個 process 是送任務那端（celery_app.send_task），CeleryInstrumentor 在
# 這裡負責把目前的 trace context 寫進 Celery message header；worker
# process（celery_app.py）另外也要呼叫，兩邊都裝才會是同一個 trace，見
# tracing_config.py 開頭的說明。
CeleryInstrumentor().instrument()

CORRECT_TEXT_TASK_NAME = "geclec_project-ml.correct_text"
TRANSLATE_TASK_NAME = "geclec_project-ml.translate_zh_to_en"

app = FastAPI(root_path="/ml")
FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz")


auth.firebase_init()

app.add_middleware(
        CORSMiddleware,
        allow_origins=main_config.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )

class predictModel(BaseModel):
        sent:str

class  loginModel(BaseModel):
    uid:Union[str, None] = None
    email:Union[str, None] = None
    username:Union[str, None] = None


def handle_predict(sent):
    """同步版本：送一個 Celery task 處理整段文字，用 task_id 向 rpc:// result
    backend 領結果，逾時就回 503。對外行為（一次拿到完整結果）跟改版前一樣，
    實際推論改在 Celery worker 執行，這個 process 不載入模型。

    log 裡不記錄使用者輸入的原始文字，只記長度——避免使用者的寫作內容留在
    集中式的 log 系統裡。"""
    sent = sent.strip()
    sent_list = text_pretention.splitAndNewLine(sent)
    if text_pretention.IsWrongEnter(sent_list):
        return status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE

    async_result = celery_app.send_task(CORRECT_TEXT_TASK_NAME, args=[sent])
    logger.info(
        "predict task dispatched",
        extra={"task_id": async_result.id, "input_length": len(sent)},
    )
    try:
        return async_result.get(timeout=main_config.predictSyncTimeoutSeconds)
    except TimeoutError:
        logger.warning(
            "predict task timed out",
            extra={"task_id": async_result.id, "timeout_seconds": main_config.predictSyncTimeoutSeconds},
        )
        return status.HTTP_503_SERVICE_UNAVAILABLE
    except Exception:
        # worker 真的執行失敗（模型錯誤／連線問題等），不是使用者輸入的問題，
        # 用 500 不是 431；logger.exception 會自動把完整 traceback 一起記錄，
        # 這是唯一能事後知道 worker 為什麼失敗的地方。
        logger.exception("predict task failed", extra={"task_id": async_result.id})
        return status.HTTP_500_INTERNAL_SERVER_ERROR


@app.post("/predict")
def predict(_predictModel:predictModel):
    return handle_predict(_predictModel.sent)


class translateModel(BaseModel):
        sent:str


def handle_translate(sent):
    """同步版本：送一個 Celery task 做中翻英，用 task_id 向 rpc:// result
    backend 領結果，逾時就回 503。跟 handle_predict 同一套機制，這個
    process 一樣不載入模型。"""
    sent = sent.strip()

    async_result = celery_app.send_task(TRANSLATE_TASK_NAME, args=[sent])
    logger.info(
        "translate task dispatched",
        extra={"task_id": async_result.id, "input_length": len(sent)},
    )
    try:
        return async_result.get(timeout=main_config.predictSyncTimeoutSeconds)
    except TimeoutError:
        logger.warning(
            "translate task timed out",
            extra={"task_id": async_result.id, "timeout_seconds": main_config.predictSyncTimeoutSeconds},
        )
        return status.HTTP_503_SERVICE_UNAVAILABLE
    except Exception:
        logger.exception("translate task failed", extra={"task_id": async_result.id})
        return status.HTTP_500_INTERNAL_SERVER_ERROR


@app.post("/translate")
def translate(_translateModel:translateModel):
    return handle_translate(_translateModel.sent)

class predictAuthModel(BaseModel):
    sent:str
    uid:Union[str, None] = None
    email:Union[str, None] = None
    username:Union[str, None] = None


@app.post("/predict_login")
def predict(_predictAuthModel:predictAuthModel):
    if auth.IsEnableMemberShip():
        if _predictAuthModel.uid==None:
            return status.HTTP_401_UNAUTHORIZED
        if auth.allLoginProcess(uid=_predictAuthModel.uid,email=_predictAuthModel.email,username=_predictAuthModel.username) ==False:
            return status.HTTP_403_FORBIDDEN

    return handle_predict(_predictAuthModel.sent)


@app.get("/healthz/live")
def healthz_live():
    return {"status": "ok"}


@app.get("/healthz/ready")
def healthz_ready():
    # API process 不載入模型，只需確認能連到 RabbitMQ（Celery broker）。
    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=1)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ok"}



@app.post("/login")
def login(_loginModel:loginModel):
    return auth.allLoginProcess(uid=_loginModel.uid,email=_loginModel.email,username=_loginModel.username)


@app.get("/ml/app")
def read_main(request: Request):
    return {"message": "Hello World", "root_path": "ml/app"}

@app.get("/app")
def read_main(request: Request):
    return os.getenv("docker-env")
