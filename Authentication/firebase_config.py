import firebase_admin
import os
from firebase_admin import db,credentials,firestore
cred_path = os.path.join(os.path.dirname(__file__), '..', '..', 'credenciais.json')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()