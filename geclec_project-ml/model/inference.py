from model import config
import os
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
dirname = os.path.dirname(__file__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

geclec_t5_path = os.path.join(dirname, 'models', config.T5_GEC_LEC)
geclec_t5_tok = AutoTokenizer.from_pretrained(geclec_t5_path)
geclec_t5_model = AutoModelForSeq2SeqLM.from_pretrained(geclec_t5_path).to(device)


def correct_sent( sent) -> str:
    input_ids = geclec_t5_tok(f"{config.PREFIX}{sent}", return_tensors='pt').input_ids.to(device)
    outputs = geclec_t5_model.generate(input_ids, max_length=200)
    output_sent = geclec_t5_tok.decode(outputs[0].cpu(), skip_special_tokens=True, clean_up_tokenization_spaces=True)
    return output_sent


def correct_many_sents(sent_list) -> str:
    output_sents = []
    for sent in sent_list:
        if sent=='':
            continue
        sent=sent+'.'
        output = correct_sent(sent)
        output_sents.append(output)
    return ' '.join(output_sents)
