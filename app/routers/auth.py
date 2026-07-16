"""
Autenticação v1: cadastro e login simples, sem JWT.

Por que sem JWT agora? Porque o prompt original já definiu JWT como uma
melhoria de versão futura. Implementar autenticação de sessão completa
(tokens, expiração, refresh) antes de o resto do sistema funcionar seria
otimizar uma parte antes de validar o todo. Por enquanto, o Frontend
guarda o id do usuário logado e manda ele em cada requisição que precisa
saber "quem está fazendo isso" (ex: criar um caso).

A senha NUNCA é guardada em texto puro — usamos hash com salt (pbkdf2,
da biblioteca padrão do Python, sem dependência externa).
"""
import hashlib
import os
from fastapi import APIRouter, HTTPException
from app import storage
from app.models import UsuarioCreate, UsuarioLogin, UsuarioOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_senha(senha: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 100_000).hex()


def _gerar_hash_completo(senha: str) -> str:
    salt = os.urandom(16).hex()
    return f"{salt}${_hash_senha(senha, salt)}"


def _verificar_senha(senha: str, hash_completo: str) -> bool:
    salt, hash_esperado = hash_completo.split("$")
    return _hash_senha(senha, salt) == hash_esperado


@router.post("/cadastro", response_model=UsuarioOut)
def cadastrar(dados: UsuarioCreate):
    if storage.find_user_by_email(dados.email):
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")
    senha_hash = _gerar_hash_completo(dados.senha)
    user = storage.create_user(dados.nome, dados.email, senha_hash, dados.telefone, dados.anonimo)
    return UsuarioOut(
        id=user["id"],
        nome=user["nome"],
        email=user["email"],
        telefone=user["telefone"],
        anonimo=bool(user["anonimo"]),
        admin=False,
    )


@router.post("/login", response_model=UsuarioOut)
def login(dados: UsuarioLogin):
    user = storage.find_user_by_email(dados.email)
    if not user or not _verificar_senha(dados.senha, user["senha_hash"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    return UsuarioOut(
        id=user["id"],
        nome=user["nome"],
        email=user["email"],
        telefone=user.get("telefone", ""),
        anonimo=storage.parse_bool(user.get("anonimo")),
        admin=storage.parse_bool(user.get("admin")),
    )
