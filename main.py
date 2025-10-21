# main.py
from fastapi import FastAPI, Query, Depends, HTTPException, status, Body, Header
from fastapi.security import OAuth2PasswordRequestForm
import os
import sqlite3
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from jose import jwt
from auth import SECRET_KEY, ALGORITHM 
from typing import List, Dict, Any 
import datetime
import json
import threading
import subprocess

app = FastAPI(
    title="API Tech Challenge",
    version="1.0.0",
    description="Trabalho Fase 1"
)





# Rotas públicas
@app.get("/")
async def home():
    return {"message": "Hello, FastAPI!"}



# Caminho do banco de dados
DB_FILE = os.path.join(os.path.dirname(__file__), "data", "challenge1.sqlite")

# Função utilitária para consultar o banco SQLite
def query_db(query: str, params: tuple = (), fetchone=False):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    if fetchone:
        return dict(rows[0]) if rows else None
    return [dict(row) for row in rows]



# Criar usuário (hash de senha incluso)
@app.post("/add_user")
def add_user(user: dict = Body(...)):
    username = user.get("username")
    password = user.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username e password são obrigatórios")
    
    hashed_pw = get_password_hash(password)
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Cria tabela caso não exista
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Usuário já existe")
    
    conn.close()
    return {"message": f"Usuário {username} criado com sucesso!"}

# Login e geração de token
@app.post("/api/v1/auth/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = query_db("SELECT * FROM users WHERE username = ?", (form_data.username,), fetchone=True)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# -> função pra inserir nos endpoints sensiveis -> current_user: dict = Depends(get_current_user) - aqui solicita o token gerado

@app.post("/api/v1/auth/refresh")
def refresh_token(authorization: str = Header(...)):
    """
    Renova o token JWT.
    Recebe o token atual no header Authorization: Bearer <token>
    """
    # Verifica se o header começa com "Bearer "
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = authorization.split(" ")[1]

    try:
        # Decodifica o token atual
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    # Gera um novo token
    new_token = create_access_token(data={"sub": username})
    return {"access_token": new_token, "token_type": "bearer"}

@app.get("/api/v1/scraping/trigger")
def trigger_scraping(current_user: dict = Depends(get_current_user)):
    subprocess.Popen(["python", "notebooks/bookstoscrape.py"])
    return {
        "status": "Scraping iniciado em background",
        "usuario": current_user["username"]  # ou o campo que você tiver
    }

# Rotas protegidas
@app.get("/api/v1/books")
async def get_books():
    livros = query_db("SELECT titulo FROM books_details WHERE disponibilidade > 0")
    return {"livros_disponiveis": livros}

@app.get("/api/v1/books/{id:int}")
async def get_book(id: int):
    result = query_db("SELECT rowid as ID, * FROM books_details WHERE rowid = ?", (id,), fetchone=True)
    if not result:
        return {"error": "Livro não encontrado"}
    return result

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

@app.get("/api/v1/categories")
async def get_categories():
    categorias = query_db("SELECT DISTINCT categoria FROM books_details WHERE disponibilidade > 0")
    return {"Categorias_disponiveis": categorias}

@app.get("/api/v1/health")
async def health_check():
    if not os.path.exists(DB_FILE):
        return {"status": "error", "detail": "Banco de dados não encontrado"}
    try:
        result = query_db("SELECT COUNT(*) as total FROM books_details", fetchone=True)
    except Exception as e:
        return {"status": "error", "detail": f"Erro ao ler BD: {str(e)}"}
    return {"status": "ok", "total_livros": result["total"]}

# Estatísticas gerais
@app.get("/api/v1/stats/overview")
async def stats_overview():
    total_livros = query_db("SELECT COUNT(*) as total FROM books_details", fetchone=True)["total"]
    precos_raw = query_db("SELECT preço FROM books_details WHERE preço IS NOT NULL AND preço != ''")
    precos = []
    for row in precos_raw:
        try:
            precos.append(float(row["preço"]))
        except:
            continue
    preco_medio = round(sum(precos) / len(precos), 2) if precos else 0
    ratings = query_db("""
        SELECT rating, COUNT(*) as total
        FROM books_details
        WHERE rating IS NOT NULL AND rating != ''
        GROUP BY rating
    """)
    return {
        "total_livros": total_livros,
        "preco_medio": preco_medio,
        "distribuicao_ratings": ratings
    }

# Estatísticas por categoria
@app.get("/api/v1/stats/categories")
async def stats_categories():
    rows = query_db("SELECT categoria, preço FROM books_details WHERE categoria IS NOT NULL AND categoria != ''")
    categorias = {}
    for row in rows:
        categoria = str(row["categoria"]).strip()
        try:
            preco = float(row["preço"])
        except (ValueError, TypeError):
            preco = None
        if categoria not in categorias:
            categorias[categoria] = {"quantidade": 0, "precos": []}
        categorias[categoria]["quantidade"] += 1
        if preco is not None:
            categorias[categoria]["precos"].append(preco)

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

# Top rated
@app.get("/api/v1/books/top-rated")
async def top_rated_books(limit: int = 10):
    livros = query_db("SELECT titulo, categoria, rating FROM books_details WHERE rating = 5")
    return {"top_rated_books": livros[:limit]}

# Faixa de preço
@app.get("/api/v1/books/price-range")
async def books_price_range(min: float = Query(...), max: float = Query(...)):
    rows = query_db("SELECT titulo, categoria, preço, disponibilidade FROM books_details WHERE preço IS NOT NULL AND preço != ''")
    livros_filtrados = []
    for row in rows:
        try:
            preco = float(row["preço"])
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

@app.get("/api/v1/ml/features")
async def get_ml_features():
    """
    Retorna dados limpos e formatados para serem usados como features de um modelo ML.
    Filtra entradas onde rating ou preço não podem ser convertidos para float.
    """
    rows = query_db("SELECT titulo, rating, preço, categoria, disponibilidade FROM books_details")
    features_data = []
    
    for row in rows:
        rating = float(row["rating"])
        preco = float(row["preço"])
        disponibilidade = row["disponibilidade"]

        # Filtra apenas registros que tenham dados numéricos válidos para rating e preço
        if rating is not None and preco is not None:
            features_data.append({
                "titulo": str(row["titulo"]).strip(),
                "rating": rating,
                "preco": preco,
                "categoria": str(row["categoria"]).strip(),
                # Simplifica disponibilidade para um valor numérico (ex: 1 se disponível, 0 se indisponível/desconhecido)
                "disponibilidade": disponibilidade
            })
            
    return {"features_data": features_data, "total_registros": len(features_data)}

@app.get("/api/v1/ml/training-data")
async def get_ml_training_data():
    """
    Retorna um dataset pronto para treinamento, com a coluna 'categoria' codificada em One-Hot (OHE).
    A coluna 'Y_preco' é o target (o que se quer prever).
    """
    # 1. Obter todas as categorias únicas (vocabulário)
    unique_categories_raw = query_db("SELECT DISTINCT categoria FROM books_details WHERE categoria IS NOT NULL AND categoria != ''")
    
    # Lista ordenada de categorias
    unique_categories = [str(row['categoria']).strip() for row in unique_categories_raw]
    
    # Mapeamento para obter o índice do vetor OHE rapidamente
    category_to_index = {cat: i for i, cat in enumerate(unique_categories)}
    num_categories = len(unique_categories)
    
    # 2. Obter os dados brutos
    rows = query_db("SELECT rating, preço, categoria FROM books_details")
    training_set = []

    # 3. Processar cada linha e aplicar OHE
    for row in rows:
        rating = float(row["rating"])
        preco = float(row["preço"])
        categoria = str(row["categoria"]).strip()
        
        # Garante que as variáveis X (rating) e Y (preço) são numéricas e válidas
        if rating is not None and preco is not None and categoria:
            
            # Inicializa o vetor OHE com zeros
            one_hot_vector = [0] * num_categories
            
            # Pega o índice e seta para 1
            cat_index = category_to_index.get(categoria)
            if cat_index is not None:
                 one_hot_vector[cat_index] = 1

            training_set.append({
                "X_rating": rating,
                # Retorna o vetor OHE em vez da string da categoria
                "X_categoria_ohe": one_hot_vector, 
                "Y_preco": preco
            })
            
    return {
        "training_data": training_set, 
        "total_samples": len(training_set),
        # Retorna o mapa para que o cliente saiba qual categoria corresponde a qual índice do vetor OHE
        "one_hot_encoding_map": unique_categories 
    }

@app.post("/api/v1/ml/predictions")
async def receive_predictions(
    predictions_payload: List[Dict[str, Any]] = Body(..., description="Lista de objetos de predição, contendo features e o valor predito."),
):
    """
    Recebe um lote de predições de um modelo ML e as armazena no banco de dados SQLite para persistência.
    """
    
    if not isinstance(predictions_payload, list) or not all(isinstance(item, dict) for item in predictions_payload):
        raise HTTPException(status_code=400, detail="O corpo deve ser uma lista de objetos JSON.")
        
    num_predictions = len(predictions_payload)
    successful_inserts = 0
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # 1. Cria a tabela de predições se ela não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            predicted_price REAL,
            input_features_json TEXT NOT NULL,
            model_version TEXT
        )
    """)
    
    now = datetime.datetime.now().isoformat()
    
    # 2. Insere cada predição no banco de dados
    for pred in predictions_payload:
        predicted_price = pred.get("predicted_price")
        input_features = pred.get("input_features", {})
        model_version = pred.get("model_version")
        
        # Validação básica: verifica se a predição chave é um número
        if predicted_price is None or not isinstance(predicted_price, (int, float)):
            continue

        try:
            # Serializa os objetos Python complexos (features) para JSON string
            input_features_json = json.dumps(input_features)
            
            cur.execute("""
                INSERT INTO ml_predictions (timestamp, predicted_price, input_features_json, model_version)
                VALUES (?, ?, ?, ?)
            """, (now, predicted_price, input_features_json, model_version))
            
            successful_inserts += 1
            
        except Exception as e:
            # Em um app real, você faria um logging mais robusto
            print(f"Erro ao inserir predição: {e}") 
            continue
            
    conn.commit()
    conn.close()
            
    if successful_inserts == num_predictions:
        return {
            "message": f"Sucesso ao receber e armazenar {successful_inserts} de {num_predictions} predições no SQLite.",
            "status": "stored_ok"
        }
    else:
        return {
            "message": f"Recebidas {num_predictions} predições, mas apenas {successful_inserts} foram armazenadas com sucesso. Verifique os logs do servidor para detalhes.",
            "status": "partial_success"
        }
