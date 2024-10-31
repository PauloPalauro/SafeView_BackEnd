from firebase_admin import storage

def upload_pdf_to_firebase(byte_string, filename):
    bucket = storage.bucket()

    # Define o caminho completo com a pasta "reports"
    blob = bucket.blob(f'Reports/{filename}')  

    blob.upload_from_string(byte_string, content_type='application/pdf')

    blob.make_public()
    return blob.public_url
