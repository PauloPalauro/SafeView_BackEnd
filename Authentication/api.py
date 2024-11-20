from fastapi import FastAPI, HTTPException, status, Request
from firebase_config import db
from fastapi.responses import JSONResponse
import requests
import logging
import bcrypt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from fastapi.responses import JSONResponse
import random
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
        cargo = 'usuario'

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
            'Cargo': cargo,
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

@app.get('/usuario/{email}')
async def usuario_por_email(email: str):
    try:
        logger.info(f"Procurando usuário com email {email}...")
        users_ref = db.collection('usuarios')
        docs = users_ref.where('Email', '==', email).stream()
        
        usuario = None
        for doc in docs:
            usuario = doc.to_dict()
            break
        
        if usuario is None:
            logger.error(f"Usuário com email {email} não encontrado.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        logger.info(f"Usuário com email {email} encontrado: {usuario}")
        return JSONResponse({'usuario': usuario}, status_code=200)
    
    except HTTPException as http_exc:
        logger.error(f"Erro HTTP: {http_exc.detail}")
        return JSONResponse({'detail': str(http_exc.detail)}, status_code=http_exc.status_code)
    
    except Exception as e:
        logger.error(f"Ocorreu um erro ao buscar o usuário: {e}")
        return JSONResponse({'mensagem': 'Ocorreu um erro ao buscar o usuário', 'erro': str(e)}, status_code=500)

@app.post('/login')
async def verifica_usuario(request: Request):
    try:
        logger.info("Recebendo requisição para verificar usuário...") 
        info = await request.json()
        logger.info(f"Dados recebidos: {info}")  

        email = info.get('email')
        senha = info.get('senha')

        if not email or not senha:
            logger.error("email ou senha não fornecidos.")
            raise HTTPException(status_code=400, detail="email e senha são obrigatórios.")

        users_ref = db.collection('usuarios')
        
        logger.info(f"Verificando se o usuário com email {email} existe...")
        docs = users_ref.where('Email', '==', email).stream()
        user_found = False
        stored_password = None
        for doc in docs:
            user_found = True
            user_data = doc.to_dict()
            stored_password = user_data.get('Senha')
            break
        
        if not user_found:
            logger.error(f"Usuário com email {email} não encontrado.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        if not bcrypt.checkpw(senha.encode('utf-8'), stored_password.encode('utf-8')):
            logger.error("Senha incorreta.")
            raise HTTPException(status_code=401, detail="Senha incorreta.")

        logger.info(f"Usuário com email {email} autenticado com sucesso.")
        return JSONResponse({'mensagem': 'Usuário autenticado com sucesso'}, status_code=200)
    
    except HTTPException as http_exc:
        logger.error(f"Erro HTTP: {http_exc.detail}")
        return JSONResponse({'detail': str(http_exc.detail)}, status_code=http_exc.status_code)
    
    except Exception as e:
        logger.error(f"Ocorreu um erro ao verificar o usuário: {e}")
        return JSONResponse({'mensagem': 'Ocorreu um erro ao verificar o usuário', 'erro': str(e)}, status_code=500)

conf = ConnectionConfig(
    MAIL_USERNAME="safeviewrecuperacaosenha@gmail.com",
    MAIL_PASSWORD="zvfl wbhy cwfd ncos",  # Use a senha de app aqui
    MAIL_FROM="safeviewrecuperacaosenha@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


@app.post('/enviar_codigo_recuperacao')
async def enviar_codigo_recuperacao(request: Request):
    try:
        logger.info("Recebendo requisição para recuperação de senha...")
        info = await request.json()
        email = info.get('email')

        if not email:
            logger.error("Email não fornecido.")
            raise HTTPException(status_code=400, detail="Email é obrigatório.")

        users_ref = db.collection('usuarios')
        docs = users_ref.where('Email', '==', email).stream()
        
        usuario = None
        for doc in docs:
            usuario = doc.to_dict()
            break

        if usuario is None:
            logger.error(f"Usuário com email {email} não encontrado.")
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        # Gerar um código de recuperação
        codigo_recuperacao = str(random.randint(100000, 999999))
        users_ref.document(doc.id).update({'CodigoRecuperacao': codigo_recuperacao})

        corpo_email = f"Olá {usuario['Nome']},\n\nSeu código de recuperação de senha é: {codigo_recuperacao}\n\nUtilize este código para redefinir sua senha."

        mensagem = MessageSchema(
            subject="Código de Recuperação de Senha",
            recipients=[email],
            body=corpo_email,
            subtype="plain"
        )

        fast_mail = FastMail(conf)
        await fast_mail.send_message(mensagem)

        logger.info(f"Código de recuperação enviado para {email}.")
        return JSONResponse({'mensagem': 'Código de recuperação enviado com sucesso.'}, status_code=200)
    
    except Exception as e:
        logger.error(f"Ocorreu um erro ao enviar o código de recuperação: {e}")
        return JSONResponse({'mensagem': 'Erro ao enviar o código de recuperação', 'erro': str(e)}, status_code=500)
    

@app.post('/validar_codigo_recuperacao')
async def validar_codigo_recuperacao(request: Request):
    try:
        
        info = await request.json()
        
        email = info.get('email')
        codigo = info.get('codigo')
        nova_senha = info.get('nova_senha')
        logger.info(f"Dados recebidos: email={email}, codigo={codigo}, nova_senha={nova_senha}")

        if not email or not codigo or not nova_senha:
            logger.error("Dados incompletos.")
            raise HTTPException(status_code=400, detail="Email, código e nova senha são obrigatórios.")

        users_ref = db.collection('usuarios')
        docs = users_ref.where('Email', '==', email).stream()
        
        usuario = None
        for doc in docs:
            usuario = doc.to_dict()
            usuario['id'] = doc.id
            break

        if usuario is None or usuario.get('CodigoRecuperacao') != codigo:
            logger.error("Código de recuperação inválido ou expirado.")
            raise HTTPException(status_code=400, detail="Código inválido ou expirado.")

        # Atualizar a senha e remover o código de recuperação
        nova_senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users_ref.document(usuario['id']).update({
            'Senha': nova_senha_hash,
            'CodigoRecuperacao': None
        })

        logger.info(f"Senha atualizada com sucesso para o usuário {email}.")
        return JSONResponse({'mensagem': 'Senha atualizada com sucesso.'}, status_code=200)
    
    except Exception as e:
        logger.error(f"Ocorreu um erro ao validar o código de recuperação: {e}")
        return JSONResponse({'mensagem': 'Erro ao validar o código de recuperação', 'erro': str(e)}, status_code=500)

@app.delete('/apagar_usuario/{email_usuario_apagando}/{email_usuario_a_apagar}')
async def apagar_usuario(email_usuario_apagando: str, email_usuario_a_apagar: str):
    try:
        logger.info(f"Usuário {email_usuario_apagando} está tentando apagar o usuário {email_usuario_a_apagar}...")

        users_ref = db.collection('usuarios')
        
        logger.info(f"Verificando se o usuário com email {email_usuario_apagando} é admin...")
        docs = users_ref.where('Email', '==', email_usuario_apagando).stream()
        usuario_apagando = None
        for doc in docs:
            usuario_apagando = doc.to_dict()
            usuario_apagando['id'] = doc.id
            break
        
        if not usuario_apagando or usuario_apagando.get('Cargo') != 'admin':
            logger.error(f"Usuário {email_usuario_apagando} não é um admin.")
            raise HTTPException(status_code=403, detail="Voce nao tem permissao para apagar usuarios.")
        
        logger.info(f"Verificando se o usuário com email {email_usuario_a_apagar} existe...")
        docs = users_ref.where('Email', '==', email_usuario_a_apagar).stream()
        usuario_a_apagar = None
        for doc in docs:
            usuario_a_apagar = doc.to_dict()
            usuario_a_apagar['id'] = doc.id
            break

        if not usuario_a_apagar:
            logger.error(f"Usuário {email_usuario_a_apagar} não encontrado.")
            raise HTTPException(status_code=404, detail="Usuário a ser apagado não encontrado.")
        
        # Apaga o usuário
        logger.info(f"Apagando usuário com email {email_usuario_a_apagar}...")
        users_ref.document(usuario_a_apagar['id']).delete()
        
        logger.info(f"Usuário {email_usuario_a_apagar} apagado com sucesso.")
        return JSONResponse({'mensagem': f'Usuário {email_usuario_a_apagar} apagado com sucesso.'}, status_code=200)

    except HTTPException as http_exc:
        logger.error(f"Erro HTTP: {http_exc.detail}")
        return JSONResponse({'detail': str(http_exc.detail)}, status_code=http_exc.status_code)
    
    except Exception as e:
        logger.error(f"Ocorreu um erro ao tentar apagar o usuário: {e}")
        return JSONResponse({'mensagem': 'Ocorreu um erro ao tentar apagar o usuário', 'erro': str(e)}, status_code=500)
