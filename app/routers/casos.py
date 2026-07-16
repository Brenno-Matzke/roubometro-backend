"""
Router de casos.

Rotas que merecem explicação:

- GET /api/casos é PÚBLICA de propósito — a Home mostra a tabela e o
  contador sem exigir login, porque o objetivo do projeto é transparência.
  Mas só devolve casos com status != em_apuracao — enquanto o admin ainda
  está apurando/conferindo a denúncia, ela fica visível só no Dashboard.
  Assim que o status muda pra "verificado" ou "contestado" (edição feita
  pelo admin), o caso passa a aparecer pra todo mundo. Se quem pedir a
  lista for admin (usuario_id de admin na query), devolve tudo, incluindo
  os que ainda estão em apuração, pra ele conseguir revisar.
- POST/PUT/DELETE exigem usuario_id (passado pelo Frontend, que guarda o
  usuário logado) E que esse usuário seja admin — o Dashboard é uma
  ferramenta de moderação, não um CRUD aberto a qualquer conta. Isto
  NÃO é uma autenticação forte (não valida token, só confia no id
  enviado) — é aceitável para v1 porque ainda não há JWT. Fica marcado
  aqui como um ponto a reforçar quando a etapa de JWT chegar.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app import storage
from app.models import CasoCreate, CasoOut

router = APIRouter(prefix="/api/casos", tags=["casos"])


def _exigir_admin(usuario_id: str) -> None:
    if not storage.is_admin(usuario_id):
        raise HTTPException(status_code=403, detail="Apenas moderadores podem fazer isso.")


def _publico(caso: dict) -> bool:
    return caso.get("status") != "em_apuracao"


@router.get("", response_model=list[CasoOut])
def listar_casos(usuario_id: Optional[str] = Query(None)):
    casos = storage.list_casos()
    if usuario_id and storage.is_admin(usuario_id):
        return casos
    return [c for c in casos if _publico(c)]


@router.get("/resumo")
def resumo():
    casos = [c for c in storage.list_casos() if _publico(c)]
    total = sum(float(c["valor_estimado"] or 0) for c in casos)
    return {"total_estimado": total, "quantidade_casos": len(casos)}


@router.post("", response_model=CasoOut)
def criar_caso(dados: CasoCreate, usuario_id: str = Query(...)):
    _exigir_admin(usuario_id)
    novo = storage.create_caso({
        "usuario_id": usuario_id,
        "titulo": dados.titulo,
        "envolvidos": dados.envolvidos,
        "valor_estimado": dados.valor_estimado,
        "data": dados.data,
        "fonte": dados.fonte,
        "status": dados.status.value,
        "observacoes": dados.observacoes,
    })
    return novo


@router.put("/{caso_id}", response_model=CasoOut)
def editar_caso(caso_id: str, dados: CasoCreate, usuario_id: str = Query(...)):
    _exigir_admin(usuario_id)
    atualizado = storage.update_caso(caso_id, {
        "titulo": dados.titulo,
        "envolvidos": dados.envolvidos,
        "valor_estimado": dados.valor_estimado,
        "data": dados.data,
        "fonte": dados.fonte,
        "status": dados.status.value,
        "observacoes": dados.observacoes,
    })
    if not atualizado:
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    return atualizado


@router.delete("/{caso_id}")
def excluir_caso(caso_id: str, usuario_id: str = Query(...)):
    _exigir_admin(usuario_id)
    if not storage.delete_caso(caso_id):
        raise HTTPException(status_code=404, detail="Caso não encontrado.")
    return {"ok": True}
