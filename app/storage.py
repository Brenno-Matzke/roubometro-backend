"""
Camada de persistência em PostgreSQL (antes era CSV).

Por que isolar tudo aqui? Porque é a ÚNICA parte do sistema que sabe que
os dados são guardados num banco de verdade. Routers e regras de negócio
nunca escrevem SQL diretamente — eles chamam estas funções, com a mesma
assinatura de quando isso aqui era CSV. Foi exatamente pra esse dia que
a camada foi isolada desde o início.

Conexão vem de DATABASE_URL (variável de ambiente, lida de um .env local
via python-dotenv, ou setada direto no serviço de hospedagem em produção).
"""
from __future__ import annotations

import os
import uuid
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def _conn():
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    """Cria as tabelas se ainda não existirem. Chamado uma vez, na subida da API."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                telefone TEXT NOT NULL DEFAULT '',
                anonimo BOOLEAN NOT NULL DEFAULT FALSE,
                admin BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS casos (
                id TEXT PRIMARY KEY,
                usuario_id TEXT NOT NULL,
                titulo TEXT NOT NULL,
                envolvidos TEXT NOT NULL,
                valor_estimado DOUBLE PRECISION NOT NULL,
                data TEXT NOT NULL,
                fonte TEXT NOT NULL,
                status TEXT NOT NULL,
                observacoes TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.commit()


def parse_bool(valor) -> bool:
    """Compat: no CSV isso vinha como texto ('True'/'False'); no Postgres já
    vem como bool nativo. Mantido pra quem ainda chama assim funcionar dos
    dois jeitos."""
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ("true", "1", "yes")


# ---------- Usuários ----------

def list_users() -> List[Dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM users")
        return [dict(row) for row in cur.fetchall()]


def find_user_by_email(email: str) -> Optional[Dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE lower(email) = lower(%s)", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def find_user_by_id(user_id: str) -> Optional[Dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_user(nome: str, email: str, senha_hash: str, telefone: str = "", anonimo: bool = False) -> Dict:
    # admin nunca vem do cadastro público — só é concedido manualmente
    # direto no banco, pra ninguém conseguir virar moderador só preenchendo
    # o formulário.
    novo_id = str(uuid.uuid4())
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO users (id, nome, email, senha_hash, telefone, anonimo, admin)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE)
            RETURNING *
            """,
            (novo_id, nome, email, senha_hash, telefone, anonimo),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)


def is_admin(user_id: str) -> bool:
    user = find_user_by_id(user_id)
    return bool(user) and parse_bool(user.get("admin"))


def update_user(user_id: str, nome: str, email: str) -> Optional[Dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "UPDATE users SET nome = %s, email = %s WHERE id = %s RETURNING *",
            (nome, email, user_id),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None


# ---------- Casos ----------

def list_casos() -> List[Dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM casos")
        return [dict(row) for row in cur.fetchall()]


def find_caso_by_id(caso_id: str) -> Optional[Dict]:
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM casos WHERE id = %s", (caso_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_caso(data: Dict) -> Dict:
    novo_id = str(uuid.uuid4())
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO casos (id, usuario_id, titulo, envolvidos, valor_estimado, data, fonte, status, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                novo_id,
                data["usuario_id"],
                data["titulo"],
                data["envolvidos"],
                data["valor_estimado"],
                data["data"],
                data["fonte"],
                data["status"],
                data.get("observacoes", ""),
            ),
        )
        row = cur.fetchone()
        conn.commit()
        return dict(row)


def update_caso(caso_id: str, data: Dict) -> Optional[Dict]:
    if not data:
        return find_caso_by_id(caso_id)
    colunas = ", ".join(f"{campo} = %s" for campo in data)
    valores = list(data.values()) + [caso_id]
    with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(f"UPDATE casos SET {colunas} WHERE id = %s RETURNING *", valores)
        row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None


def delete_caso(caso_id: str) -> bool:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM casos WHERE id = %s", (caso_id,))
        apagado = cur.rowcount > 0
        conn.commit()
        return apagado
