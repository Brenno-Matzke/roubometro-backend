from fastapi import APIRouter, HTTPException
from app import storage
from app.models import UsuarioUpdate, UsuarioOut

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


def _to_out(user: dict) -> UsuarioOut:
    return UsuarioOut(
        id=user["id"],
        nome=user["nome"],
        email=user["email"],
        telefone=user.get("telefone", ""),
        anonimo=storage.parse_bool(user.get("anonimo")),
        admin=storage.parse_bool(user.get("admin")),
    )


@router.get("/{usuario_id}", response_model=UsuarioOut)
def obter_usuario(usuario_id: str):
    user = storage.find_user_by_id(usuario_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return _to_out(user)


@router.put("/{usuario_id}", response_model=UsuarioOut)
def editar_usuario(usuario_id: str, dados: UsuarioUpdate):
    user = storage.update_user(usuario_id, dados.nome, dados.email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return _to_out(user)
