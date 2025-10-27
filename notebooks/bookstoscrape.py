import os
import re
import sqlite3
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

# =============================
# CONFIGURAÇÕES INICIAIS
# =============================
BASE_URL = "https://books.toscrape.com/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY = 1.0  # segundos entre as requisições

all_book_links = []
page_url = BASE_URL
page_count = 1

print("Iniciando scraping de livros...")
print("=" * 60)

# =============================
# PAGINAÇÃO
# =============================
while True:
    print(f"Coletando links da página {page_count}: {page_url}")
    resp = requests.get(page_url, headers=HEADERS)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    books = soup.select("article.product_pod h3 a")
    for book in books:
        link = book.get("href")
        book_url = urljoin(page_url, link)
        all_book_links.append(book_url)

    next_btn = soup.select_one("li.next a")
    if next_btn:
        next_page = next_btn.get("href")
        page_url = urljoin(page_url, next_page)
        page_count += 1
        time.sleep(DELAY)
    else:
        print("Última página alcançada. Fim da coleta de links.")
        break

print(f"Total de links coletados: {len(all_book_links)} livros encontrados.")
print("=" * 60)

# =============================
# EXTRAÇÃO DE DETALHES
# =============================
rating_map = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0}
all_books_details = []

print("Extraindo detalhes dos livros...")
for url in tqdm(all_book_links, desc="Extraindo detalhes"):
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # Título
        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "N/A"

        # Preço
        price_tag = soup.select_one("p.price_color")
        price_text = price_tag.text.strip() if price_tag else "0.0"
        price_float = float(re.sub(r"[^\d.]", "", price_text))

        # Disponibilidade
        avail_tag = soup.select_one("p.instock.availability")
        availability_text = avail_tag.text if avail_tag else "0"
        match = re.search(r"\d+", availability_text)
        availability_int = int(match.group(0)) if match else 0

        # Rating
        rating_tag = soup.select_one("p.star-rating")
        rating_class = rating_tag.get("class")[1] if rating_tag else "Zero"
        rating_float = rating_map.get(rating_class, 0.0)

        # Categoria
        category_tag = soup.select("ul.breadcrumb li a")
        category = category_tag[2].text.strip() if len(category_tag) > 2 else "N/A"

        # Imagem
        image_tag = soup.select_one("div.item.active img")
        image_url = urljoin(BASE_URL, image_tag["src"]) if image_tag else ""

        all_books_details.append({
            "titulo": title,
            "preco": price_float,
            "rating": rating_float,
            "disponibilidade": availability_int,
            "categoria": category,
            "imagem": image_url,
            "url_livro": url
        })

        time.sleep(0.3)  # delay pequeno para não sobrecarregar o servidor
    except Exception as e:
        print(f"Erro ao extrair {url}: {e}")
        continue

print("Scraping concluído!")

# =============================
# SALVAR RESULTADOS
# =============================
df = pd.DataFrame(all_books_details)

data_dir = os.path.join(os.getcwd(), "data")
os.makedirs(data_dir, exist_ok=True)

# CSV
csv_path = os.path.join(data_dir, "books_details.csv")
df.to_csv(csv_path, index=False)
print(f"CSV salvo em: {os.path.abspath(csv_path)}")

# Banco SQLite
db_path = os.path.join(data_dir, "challenge1.sqlite")
conn = sqlite3.connect(db_path)
df.to_sql("books_details", conn, if_exists="replace", index=False)
conn.close()
print(f"Banco salvo em: {os.path.abspath(db_path)}")

print("=" * 60)
print(f"Processo finalizado com {len(df)} livros extraídos em {page_count} páginas!")
