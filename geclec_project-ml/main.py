from typing import Union
from model import inference
from fastapi import FastAPI,status,Request
import  nltk
from service import SentenceDifferent,text_pretention
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

import main_config
from auth import auth




#寫進python shell

app = FastAPI(root_path="/ml")


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
    
@app.post("/predict")
def predict(_predictModel:predictModel):
    
    sent=_predictModel.sent.strip()
    sent_list=text_pretention.splitAndNewLine(sent)
    if text_pretention.IsWrongEnter(sent_list):
        return status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE
    geclec_sent = inference.correct_many_sents(sent_list)
    geclec_sent=text_pretention.deleteSuperfluousSpace(geclec_sent)
    return SentenceDifferent.findSentenceDifferent(sent,geclec_sent)

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
    
    sent=_predictAuthModel.sent.strip()
    sent_list=text_pretention.splitAndNewLine(sent)
    if text_pretention.IsWrongEnter(sent_list):
        return status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE
    geclec_sent = inference.correct_many_sents(sent_list)
    geclec_sent=text_pretention.deleteSuperfluousSpace(geclec_sent)
    return SentenceDifferent.findSentenceDifferent(sent,geclec_sent)




@app.post("/login")
def login(_loginModel:loginModel):
    return auth.allLoginProcess(uid=_loginModel.uid,email=_loginModel.email,username=_loginModel.username)


@app.get("/ml/app")
def read_main(request: Request):
    return {"message": "Hello World", "root_path": "ml/app"}

@app.get("/app")
def read_main(request: Request):
    return os.getenv("docker-env")