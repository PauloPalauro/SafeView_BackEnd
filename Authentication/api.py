from fastapi import FastAPI, HTTPException, status, Request
from firebase_config import db
from fastapi.responses import JSONResponse
import requests
import logging
import bcrypt


app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get('/usuarios')
async def todos_usuarios():
    users_ref = db.collection('usuarios')
    docs = users_ref.stream()
    usuarios = []
    for doc in docs:
        usuario = doc.to_dict()
        print(usuario)  
        usuarios.append(usuario)
    
    return {'usuarios': usuarios}

@app.post('/registra_usuario_padrao')
async def registra_usuario(request: Request):
    try:
        logger.info("Recebendo requisição para registrar usuário...") 

        info = await request.json()
        logger.info(f"Dados recebidos: {info}")  

        email = info.get('email')
        nome = info.get('nome')
        senha = info.get('senha')
        senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

        if not email or not nome or not senha:
            logger.error("Email,nome ou senha não fornecidos.")
            raise HTTPException(status_code=400, detail="Email e nome são obrigatórios.")

        users_ref = db.collection('usuarios')
        
        logger.info(f"Verificando se o usuário com email {email} já existe...")
        docs = users_ref.where('Email', '==', email).stream()
        for doc in docs:
            if doc.exists:
                logger.error(f"Usuário com email {email} já existe.")
                raise HTTPException(status_code=400, detail="Usuário com este email já existe.")
    
        logger.info("Criando novo usuário...")
        new_user_ref = users_ref.document()
        new_user_ref.set({
            'Email': email,
            'Nome': nome,
            'Admin': False,
            'Senha': senha.decode('utf-8')
        })
        logger.info(f"Usuário {nome} cadastrado com sucesso com ID {new_user_ref.id}")
        return JSONResponse({'mensagem': 'Usuário cadastrado com sucesso', 'user_id': new_user_ref.id}, status_code=201)
    
    except HTTPException as http_exc:
        logger.error(f"Erro HTTP: {http_exc.detail}")
        return JSONResponse({'detail': str(http_exc.detail)}, status_code=http_exc.status_code)
    
    except Exception as e:
        logger.error(f"Ocorreu um erro ao registrar o usuário: {e}")
        return JSONResponse({'mensagem': 'Ocorreu um erro ao registrar o usuário', 'erro': str(e)}, status_code=500)

@app.post('/login')
async def verifica_usuario(request: Request):
    try:
        logger.info("Recebendo requisição para verificar usuário...") 
        info = await request.json()
        logger.info(f"Dados recebidos: {info}")  

        nome = info.get('nome')
        senha = info.get('senha')

        if not nome or not senha:
            logger.error("nome ou senha não fornecidos.")
            raise HTTPException(status_code=400, detail="nome e senha são obrigatórios.")

        users_ref = db.collection('usuarios')
        
        logger.info(f"Verificando se o usuário com nome {nome} existe...")
        docs = users_ref.where('Nome', '==', nome).stream()
        user_found = False
        stored_password = None
        for doc in docs:
            user_found = True
            user_data = doc.to_dict()
            stored_password = user_data.get('Senha')
            break
        
        if not user_found:
            logger.error(f"Usuário com nome {nome} não encontrado.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        if not bcrypt.checkpw(senha.encode('utf-8'), stored_password.encode('utf-8')):
            logger.error("Senha incorreta.")
            raise HTTPException(status_code=401, detail="Senha incorreta.")

        logger.info(f"Usuário com nome {nome} autenticado com sucesso.")
        return JSONResponse({'mensagem': 'Usuário autenticado com sucesso'}, status_code=200)
    
    except HTTPException as http_exc:
        logger.error(f"Erro HTTP: {http_exc.detail}")
        return JSONResponse({'detail': str(http_exc.detail)}, status_code=http_exc.status_code)
    
    except Exception as e:
        logger.error(f"Ocorreu um erro ao verificar o usuário: {e}")
        return JSONResponse({'mensagem': 'Ocorreu um erro ao verificar o usuário', 'erro': str(e)}, status_code=500)
