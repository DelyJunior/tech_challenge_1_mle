import os
import time
import re
import warnings
import sqlite3
import tempfile
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

warnings.filterwarnings("ignore")

# =============================
# CONFIGURAÇÕES DO CHROME (Render)
# =============================
CHROME_PATH = os.getenv("GOOGLE_CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.binary_location = CHROME_PATH

# Diretório temporário isolado para o perfil do Chrome
user_data_dir = tempfile.mkdtemp()
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

# Inicializa o Chrome driver (usando os caminhos do Render)
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

# =============================
# INÍCIO DO SCRAPING
# =============================
print("🚀 Iniciando scraping...")
start_url = "https://books.toscrape.com/"
driver.get(start_url)

all_book_links = []
page_count = 1

while True:
    print(f"Coletando links da página {page_count}...")
    books = driver.find_elements(By.CLASS_NAME, "product_pod")

    for book in books:
        try:
            link_element = book.find_element(By.TAG_NAME, "h3").find_element(By.TAG_NAME, "a")
            link = link_element.get_attribute("href")
            all_book_links.append(link)
        except Exception as e:
            print(f"Erro ao extrair link: {e}")
            continue

    try:
        next_button = driver.find_element(By.CLASS_NAME, "next")
        next_button.find_element(By.TAG_NAME, "a").click()
        page_count += 1
        time.sleep(1)
    except NoSuchElementException:
        print("Última página alcançada. Fim da coleta de links.")
        break

# =============================
# COLETA DE DETALHES
# =============================
rating_map = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0}
all_books_details = []

for url in tqdm(all_book_links, desc="Extraindo detalhes dos livros"):
    driver.get(url)
    time.sleep(0.8)
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text
        price = driver.find_element(By.CLASS_NAME, "price_color").text
        price_float = float(price.replace("£", "")) if price else 0.0

        availability = driver.find_element(By.CLASS_NAME, "instock.availability").text
        match = re.search(r'\d+', availability)
        availability_int = int(match.group(0)) if match else 0

        rating_element = driver.find_element(By.CSS_SELECTOR, "p.star-rating")
        rating = rating_element.get_attribute("class").replace("star-rating ", "")
        rating_float = rating_map.get(rating, 0.0)

        category = driver.find_element(By.XPATH, "//ul[@class='breadcrumb']/li[3]/a").text
        image_relative_url = driver.find_element(By.CSS_SELECTOR, "div.item.active img").get_attribute("src")
        image_url = image_relative_url.replace("../..", "https://books.toscrape.com")

        all_books_details.append({
            "titulo": title,
            "preco": price_float,
            "rating": rating_float,
            "disponibilidade": availability_int,
            "categoria": category,
            "imagem": image_url,
            "url_livro": url
        })
    except Exception as e:
        print(f"Erro ao extrair {url}: {e}")
        continue

driver.quit()
print("Scraping concluído!")

# =============================
# SALVAR DADOS
# =============================
df = pd.DataFrame(all_books_details)

# Diretório data
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
