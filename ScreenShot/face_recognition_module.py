import os
import face_recognition


def carregar_base_dados(diretorio_base):
    """
    Carrega as imagens de rostos de um diretório e retorna um dicionário
    com o nome dos arquivos como chave e os encodings dos rostos como valor.
    """
    base_dados = {}
    for arquivo in os.listdir(diretorio_base):
        if arquivo.endswith(('.jpg', '.jpeg', '.png')):
            caminho_arquivo = os.path.join(diretorio_base, arquivo)
            imagem = face_recognition.load_image_file(caminho_arquivo)
            encodings = face_recognition.face_encodings(imagem)
            if encodings:  # Verifica se há algum rosto detectado
                base_dados[os.path.splitext(arquivo)[0]] = encodings[0]
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
