import os
import re
import sqlite3
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# =============================
# INÍCIO DO SCRAPING
# =============================
print("Iniciando scraping (sem navegador)...")
BASE_URL = "https://books.toscrape.com/"

all_book_links = []
page_url = BASE_URL

while True:
    print(f"Coletando links da página {page_url}...")
    resp = requests.get(page_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    books = soup.select("article.product_pod h3 a")
    for book in books:
        link = book.get("href")
        all_book_links.append(BASE_URL + link.replace("../", ""))

    next_btn = soup.select_one("li.next a")
    if next_btn:
        next_page = next_btn.get("href")
        page_url = BASE_URL + "catalogue/" + next_page
    else:
        print("Última página alcançada. Fim da coleta de links.")
        break

# =============================
# COLETA DE DETALHES
# =============================
rating_map = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0}
all_books_details = []

for url in tqdm(all_book_links, desc="Extraindo detalhes dos livros"):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.find("h1").text.strip()
    price_text = soup.select_one("p.price_color").text.strip()
    price_float = float(price_text.replace("£", ""))

    availability_text = soup.select_one("p.instock.availability").text
    match = re.search(r'\d+', availability_text)
    availability_int = int(match.group(0)) if match else 0

    rating_class = soup.select_one("p.star-rating").get("class")[1]
    rating_float = rating_map.get(rating_class, 0.0)

    category = soup.select("ul.breadcrumb li a")[2].text.strip()
    image_relative_url = soup.select_one("div.item.active img")["src"]
    image_url = BASE_URL + image_relative_url.replace("../", "")

    all_books_details.append({
        "titulo": title,
        "preco": price_float,
        "rating": rating_float,
        "disponibilidade": availability_int,
        "categoria": category,
        "imagem": image_url,
        "url_livro": url
    })

print("Scraping concluído!")

# =============================
# SALVAR DADOS
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
