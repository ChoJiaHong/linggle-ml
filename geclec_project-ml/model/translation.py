from model import config
import os
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
dirname = os.path.dirname(__file__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

zh_en_path = os.path.join(dirname, 'models', config.ZH_EN_TRANSLATE)
zh_en_tok = AutoTokenizer.from_pretrained(zh_en_path)
zh_en_model = AutoModelForSeq2SeqLM.from_pretrained(zh_en_path).to(device)


def translate_zh_to_en(text) -> str:
    input_ids = zh_en_tok(text, return_tensors='pt').input_ids.to(device)
    outputs = zh_en_model.generate(input_ids, max_length=200)
    return zh_en_tok.decode(outputs[0].cpu(), skip_special_tokens=True)
