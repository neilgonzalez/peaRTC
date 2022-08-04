#database

import os
from firebase_admin import credentials
import firebase_admin
from firebase_admin import firestore


os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./peers-a8ed5-firebase-adminsdk-z23m3-f4def19f1f.json"
cred = credentials.Certificate("./peers-a8ed5-firebase-adminsdk-z23m3-f4def19f1f.json")
firebase_admin.initialize_app(cred)


async def firebase_to_string(db_ref):
    docs = db_ref.stream()
  
    async for doc in docs:
        send = ""
        sdp = f"{doc.to_dict()}".replace('\\\\', '\\').replace("\'", "\"").replace("(", "{").replace(")", "}")
        sdp = sdp[sdp.find("=") - 4:]
        sdp = sdp[:-2]
        word = sdp.split(' ')
        for x in word:
            
            #if line contains sdp flag
            if x.find("sdp") > -1:   
                send = send + "{\"sdp\": \"v=0\\r\\no=- "
                

            #if line contains type flag 
            elif x.find("type") > -1:
                send = send + "\"type\": \"offer\"}"
        

            #otherwise append to result
            else:
                send = send + x + " "

        return send



#todo: insert and retrieve SDP signals from firestore
async def addData(entry):
    doc_ref = db.collection("users").document("names")
    return await doc_ref.set({"name": entry})
  