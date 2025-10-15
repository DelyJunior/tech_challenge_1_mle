# db_usuarios.py
import sqlite3
import os

# Caminho do banco de dados
DB_FILE = os.path.join(os.path.dirname(__file__), "data", "challenge1.sqlite")


# Função para criar tabela de usuários se não existir
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Função para adicionar um usuário
def add_user(username: str, password: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

# Função para buscar um usuário pelo username
def get_user(username: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

# Inicializa o banco na importação
init_db()
