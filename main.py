from fastapi import FastAPI, Query, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import pandas as pd   
from fastapi.responses import JSONResponse
import os
import sqlite3


app = FastAPI(
    title="API Tech Challenge",
    version="1.0.0",
    description="Trabalho Fase 1"
    )


# Caminho do banco de dados
DB_FILE = os.path.join(os.path.dirname(__file__), "data", "challenge1.sqlite")

# Função utilitária para consultar o banco
def query_db(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Retorna como dicionário
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Home
@app.get("/")
async def home():
    return "Hello, FastAPI!"

################################################################
#################### Endpoints Obrigatórios ####################
################################################################

# lista todos os livros disponíveis na base de dados
@app.get("/api/v1/books")
async def get_books():
    query = """
        SELECT titulo
        FROM books_details
        WHERE disponibilidade > 0
    """
    livros = query_db(query)
    return {"livros_disponiveis": livros}



# retorna detalhes completos de um livro específico pelo ID
@app.get("/api/v1/books/{id:int}")
async def get_book(id: int):
    query = """
        SELECT rowid as ID, *
        FROM books_details
        WHERE rowid = ?
    """
    result = query_db(query, (id,))
    if not result:
        return {"error": "Livro não encontrado"}
    return result[0]

# busca livros por título e/ou categoria
@app.get("/api/v1/books/search")
async def search_books(
    title: str = Query(None, description="Título ou parte do título do livro"),
    category: str = Query(None, description="Categoria ou parte da categoria")
):
    query = "SELECT rowid as ID, titulo, categoria, disponibilidade FROM books_details WHERE 1=1"
    params = []

    if title:
        query += " AND titulo LIKE ?"
        params.append(f"%{title}%")
    if category:
        query += " AND categoria LIKE ?"
        params.append(f"%{category}%")

    livros = query_db(query, tuple(params))
    return {"resultado": livros}

# lista todas as categorias disponíveis
@app.get("/api/v1/categories")
async def get_categories():
    query = """
        SELECT DISTINCT categoria
        FROM books_details
        WHERE disponibilidade > 0
    """
    categorias = query_db(query)
    return {"Categorias_disponiveis": categorias}

# verifica status da API e conectividade com os dados
@app.get("/api/v1/health")
async def health_check():
    if not os.path.exists(DB_FILE):
        return {"status": "error", "detail": "Banco de dados não encontrado"}
    try:
        result = query_db("SELECT COUNT(*) as total FROM books_details")
    except Exception as e:
        return {"status": "error", "detail": f"Erro ao ler BD: {str(e)}"}
    return {"status": "ok", "total_livros": result[0]["total"]}


################################################################
#################### Endpoints Opcionais #######################
################################################################

@app.get("/api/v1/stats/overview")
async def stats_overview():
    # Total de livros
    total_livros = query_db("SELECT COUNT(*) as total FROM books_details")[0]["total"]

    # Preço médio (removendo símbolos de moeda e vírgulas)
    query_precos = """
        SELECT preço FROM books_details WHERE preço IS NOT NULL AND preço != ''
    """
    precos = query_db(query_precos)


    preco_medio = round(sum([float(row["preço"]) for row in precos]) / len(precos), 2) if precos else 0


    # Distribuição de ratings
    query_ratings = """
        SELECT rating, COUNT(*) as total
        FROM books_details
        WHERE rating IS NOT NULL AND rating != ''
        GROUP BY rating
    """
    ratings = query_db(query_ratings)

    return {
        "total_livros": total_livros,
        "preco_medio": preco_medio,
        "distribuicao_ratings": ratings
    }


# Estatísticas detalhadas por categoria 
@app.get("/api/v1/stats/categories")
async def stats_categories():
    # Consulta as categorias e preços
    query = """
        SELECT categoria, preço
        FROM books_details
        WHERE categoria IS NOT NULL AND categoria != ''
    """
    rows = query_db(query)

    categorias = {}

    for row in rows:
        categoria = str(row["categoria"]).strip()
        preco_raw = row["preço"]

        # Tenta converter o preço direto em float (pode vir como None)
        try:
            preco = float(preco_raw)
        except (ValueError, TypeError):
            preco = None

        if categoria not in categorias:
            categorias[categoria] = {"quantidade": 0, "precos": []}

        categorias[categoria]["quantidade"] += 1
        if preco is not None:
            categorias[categoria]["precos"].append(preco)

    # Calcula estatísticas por categoria
    stats = []
    for categoria, data in categorias.items():
        precos = data["precos"]
        if precos:
            preco_medio = round(sum(precos) / len(precos), 2)
            preco_min = round(min(precos), 2)
            preco_max = round(max(precos), 2)
        else:
            preco_medio = preco_min = preco_max = 0

        stats.append({
            "categoria": categoria,
            "quantidade": data["quantidade"],
            "preco_medio": preco_medio,
            "preco_min": preco_min,
            "preco_max": preco_max
        })

    return {"categorias": stats}


# Lista os livros com melhor avaliação 

@app.get("/api/v1/books/top-rated")
async def top_rated_books(limit: int = 10):
    """
    Lista os livros com melhor avaliação (rating mais alto).

    """

    # Puxa título, categoria e avaliação da tabela
    query = """
        SELECT titulo, categoria, rating
        FROM books_details
        WHERE rating = 5
    """
    livros = query_db(query)

    return {"top_rated_books": livros}

# Filtra livros dentro de uma faixa de preço específica.
# /api/v1/books/price-range?min={min}&max={max}
@app.get("/api/v1/books/price-range")
async def books_price_range(
    min: float = Query(..., description="Preço mínimo"),
    max: float = Query(..., description="Preço máximo")
):
    """
    Filtra livros dentro de uma faixa de preço específica.
    """
    query = """
        SELECT titulo, categoria, preço, disponibilidade
        FROM books_details
        WHERE preço IS NOT NULL AND preço != ''
    """
    rows = query_db(query)

    livros_filtrados = []
    for row in rows:
        # Limpa o preço (removendo símbolos e convertendo para float)
        preco_raw = str(row["preço"]).strip()
        try:
            preco = float(preco_raw)
        except (ValueError, TypeError):
            continue

        if min <= preco <= max:
            livros_filtrados.append({
                "titulo": row["titulo"].strip(),
                "categoria": row["categoria"].strip(),
                "preço": preco,
                "disponibilidade": str(row["disponibilidade"]).strip() if row["disponibilidade"] else ""

            })

    return {"livros_filtrados": livros_filtrados}