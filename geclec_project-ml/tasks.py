from celery_app import celery_app
from model import inference, translation
from service import SentenceDifferent, text_pretention


def _correct_and_diff(original_sent, sent_list):
    corrected = inference.correct_many_sents(sent_list)
    corrected = text_pretention.deleteSuperfluousSpace(corrected)
    return SentenceDifferent.findSentenceDifferent(original_sent, corrected)


@celery_app.task(name="geclec_project-ml.correct_text")
def correct_text_task(sent):
    """整段文字一次修正、一次 diff，給 /predict、/predict_login 用。結果透過
    Celery 的 rpc:// result backend 回傳，呼叫端用 AsyncResult(task_id).get()
    領取，不需要另外維護 pub/sub 或 queue。"""
    sent_list = text_pretention.splitAndNewLine(sent)
    return _correct_and_diff(sent, sent_list)


@celery_app.task(name="geclec_project-ml.translate_zh_to_en")
def translate_zh_to_en_task(sent):
    """中翻英，給 /translate 用。跟 correct_text_task 用同一個 worker
    process、同一個 queue，不需要另外分流。"""
    return translation.translate_zh_to_en(sent)
