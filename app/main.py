"""
Ponto de entrada da API.

CORS liberado explicitamente para o servidor de desenvolvimento do React
(porta 5173, padrão do Vite) e para o domínio de produção, se
FRONTEND_URL estiver setada (ver .env / variável de ambiente do serviço
de hospedagem). Sem isso, o navegador bloqueia as requisições do
Frontend por política de mesma origem — é um detalhe pequeno, mas que
trava o projeto inteiro se for esquecido.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import storage
from app.routers import auth, usuarios, casos

app = FastAPI(title="API - Registro de Escândalos e Desvios Públicos")

origens = ["http://localhost:5173", "http://127.0.0.1:5173"]
if os.environ.get("FRONTEND_URL"):
    origens.append(os.environ["FRONTEND_URL"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(casos.router)


@app.on_event("startup")
def _startup():
    storage.init_db()


@app.get("/")
def raiz():
    return {"status": "ok"}
