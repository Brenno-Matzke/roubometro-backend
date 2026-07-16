"""
Modelos Pydantic.

Por que ter modelos separados de entrada (Create) e saída (Out)? Porque a
API nunca deve devolver senha_hash pro Frontend, mesmo que o CSV guarde
esse campo internamente. Separar Create/Out é o que garante isso — não é
uma opção estilística, é uma barreira de segurança.
"""
from enum import Enum
from pydantic import BaseModel, EmailStr


class StatusCaso(str, Enum):
    em_apuracao = "em_apuracao"
    verificado = "verificado"
    contestado = "contestado"


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    telefone: str = ""
    anonimo: bool = False


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


class UsuarioUpdate(BaseModel):
    nome: str
    email: EmailStr


class UsuarioOut(BaseModel):
    id: str
    nome: str
    email: str
    telefone: str = ""
    anonimo: bool = False
    admin: bool = False


class CasoCreate(BaseModel):
    titulo: str
    envolvidos: str
    valor_estimado: float
    data: str
    fonte: str
    status: StatusCaso = StatusCaso.em_apuracao
    observacoes: str = ""


class CasoOut(BaseModel):
    id: str
    usuario_id: str
    titulo: str
    envolvidos: str
    valor_estimado: float
    data: str
    fonte: str
    status: str
    observacoes: str
