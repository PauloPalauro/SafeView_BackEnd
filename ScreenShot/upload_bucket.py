import firebase_admin
from firebase_admin import credentials, storage

def upload_pdf_to_firebase(byte_string, filename):
    bucket = storage.bucket()

    blob = bucket.blob(f'{filename}')  

    blob.upload_from_string(byte_string, content_type='application/pdf')

    blob.make_public()
    return blob.public_url