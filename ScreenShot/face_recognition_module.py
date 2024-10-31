import os
import face_recognition
from firebase_admin import storage
import os
import face_recognition
from io import BytesIO
from PIL import Image


def carregar_base_dados():
    """
    Carrega as imagens de rostos de uma pasta no Firebase Storage e retorna um dicionário
    com o nome dos arquivos como chave e os encodings dos rostos como valor.
    """
    bucket = storage.bucket()
    base_dados = {}

    # Listar todos os arquivos na pasta do Firebase Storage
    blobs = bucket.list_blobs(prefix="Faces/")  # Ajuste o prefixo conforme necessário

    for blob in blobs:
        if blob.name.endswith(('.jpg', '.jpeg', '.png')):
            # Baixar a imagem em memória
            imagem_bytes = blob.download_as_bytes()
            imagem = Image.open(BytesIO(imagem_bytes))
            imagem_rgb = imagem.convert("RGB")  # Converter para RGB se for PNG

            # Processar a imagem e obter encodings
            imagem_array = face_recognition.load_image_file(BytesIO(imagem_bytes))
            encodings = face_recognition.face_encodings(imagem_array)
            
            if encodings:  # Verifica se há algum rosto detectado
                base_dados[os.path.splitext(os.path.basename(blob.name))[0]] = encodings[0]

    return base_dados


def reconhecer_face(imagem_teste, base_dados):
    """
    Realiza o reconhecimento de rosto em uma imagem de teste comparando com a base de dados de rostos.
    Retorna o nome da pessoa reconhecida ou 'Desconhecido' se não houver correspondência.
    """
    img_teste = face_recognition.load_image_file(imagem_teste)
    encodings_faces = face_recognition.face_encodings(img_teste, face_recognition.face_locations(img_teste))

    for face_encoding in encodings_faces:
        distancias = face_recognition.face_distance(list(base_dados.values()), face_encoding)
        indice_melhor = distancias.argmin()
        return list(base_dados.keys())[indice_melhor] if distancias[indice_melhor] < 0.6 else "Desconhecido"
    
    return "Desconhecido"
