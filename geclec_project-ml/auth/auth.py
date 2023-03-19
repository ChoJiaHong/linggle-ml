#如果在emailMemberList裡，則建立member(會員)
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import os
from datetime import datetime, timezone, timedelta
import base64
def firebase_init():
    cred_path = 'linggle-write-firebase-adminsdk-w04f0-5e6b53a276.json'
    cred_path = os.path.join(os.path.dirname(__file__),cred_path)

    cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://linggle-write-default-rtdb.firebaseio.com/',
        'databaseAuthVariableOverride': {
        'uid': 'linggle-write'
        }
    })
    return db

def createMember(uid,email,username,memberExp):
    ref = db.reference('/user')
    user_ref = ref.child(uid)
    user_ref.set({
        'email':email,
        'memberExp':memberExp,
        "username":username
    })

#如果不在emailMemberList裡，則建立user(使用者)
def createUser(uid,email,username):
    ref = db.reference('/user')
    user_ref = ref.child(uid)
    user_ref.set({
        'email':email,
        'memberExp':'',
        "username":username
    })
    
#檢查是否已註冊過
def getUserInfo(uid):
    ref = db.reference('/user/'+uid)
    ref_user=ref.get()
    return ref_user

def IsMember(uid):
    userInfo=getUserInfo(uid)
    memberExp=userInfo['memberExp']#yes:看是否為會員(期限有無過期)
    tz = timezone(timedelta())
    if memberExp>datetime.now(tz).isoformat(timespec="seconds"):#yes:通過
           return True
    return False


def allLoginProcess(uid,email,username):#true，false判斷是為了之後可能的需求，目前不需要，其中有段判斷是否為會員，也不需要，但先留著
    userInfo=getUserInfo(uid)
    if userInfo!=None:#是否註冊
        memberExp=userInfo['memberExp']#yes:看是否為會員(期限有無過期)
        tz = timezone(timedelta())
        if memberExp>datetime.now(tz).isoformat(timespec="seconds"):#yes:通過
            return True
        return False
    else:# no:去memberlist找是否有資料(有買會員)
        emailList=str(email).split('@')
        emailList[0]=emailList[0].replace('.','')
        email_without_dot=emailList[0]+'@'+emailList[1]
        email_without_dot=email_without_dot.encode('Utf-8')
        email_without_dot_Base64=base64.b64encode(email_without_dot)
        email_without_dot_Base64=email_without_dot_Base64.decode("utf-8")
        ref=db.reference('/emailMemberList/'+email_without_dot_Base64)
        ref_emailMember=ref.get()
        if ref_emailMember!=None:#是否有資料(有買會員)
            
            memberExp=ref_emailMember["memberExp"]#有買會員
            
            createMember(uid,email,username,memberExp)
            return True  #通過
        else:  #沒買會員
            createUser(uid,email,username)
        return False

        
    
def IsEnableMemberShip():
    ref=db.reference('/EnableMembershipFunction')
    return ref.get()==True