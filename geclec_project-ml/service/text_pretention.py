def splitAndNewLine(sent):
    sent=sent.replace("\n"," \n ")
    return sent.split('.')
def deleteSuperfluousSpace(sent:str):
    sent=sent.replace("( ","(")
    sent=sent.replace(" )",")")
    sent=sent.replace(" - ","-")
    return sent
def IsWrongEnter(sent_list:list):
    for sent in sent_list:
        if len(sent)>512:
            return True
    return False