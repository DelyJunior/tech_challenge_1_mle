# %%
import pandas as pd
import numpy as np
import random
import time
import re
import warnings
from datetime import date
import datetime as dt
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import os


from webdriver_manager.chrome import ChromeDriverManager
from fuzzywuzzy import fuzz
from tqdm import tqdm

warnings.filterwarnings("ignore")

# Configura o driver do Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless")  # descomente se quiser rodar sem abrir a janela



# %%
driver = webdriver.Chrome()

# %%
start_url = "https://books.toscrape.com/"
driver.get(start_url)

# %%
all_book_links = []
page_count = 1

# --- Loop para navegar por todas as páginas (lógica similar) ---
while True:
    print(f"Coletando links da página: {page_count}")

    # Encontra todos os "cards" de livros na página atual
    books = driver.find_elements(By.CLASS_NAME, "product_pod")

    # --- Loop para extrair o link de cada livro na página ---
    for book in books:
        try:
            # >>> MUDANÇA: Encontramos a tag 'a' dentro do 'h3' e pegamos o atributo 'href'
            link_element = book.find_element(By.TAG_NAME, "h3").find_element(By.TAG_NAME, "a")
            link = link_element.get_attribute("href")
            all_book_links.append(link)
        except Exception as e:
            print(f"Erro ao extrair o link de um livro: {e}")
            continue

    # --- Lógica de Paginação (sem alterações) ---
    try:
        # Procura pelo botão "Next"
        next_button = driver.find_element(By.CLASS_NAME, "next")
        next_button.find_element(By.TAG_NAME, "a").click()
        page_count += 1
        time.sleep(3) # Pequena pausa para o carregamento da página
    except NoSuchElementException:
        # Se não encontrar o botão "Next", saímos do loop
        print("Chegamos na última página. Fim da coleta de links.")
        break

# %%
rating_map = {
    "One": 1.0,
    "Two": 2.0,
    "Three": 3.0,
    "Four": 4.0,
    "Five": 5.0
}


# %%


# %%
all_books_details = []

for url in tqdm(all_book_links):
    
    driver.get(url)
    time.sleep(2)
    try:
        # Extrai as informações
        title = driver.find_element(By.TAG_NAME, "h1").text
        price = driver.find_element(By.CLASS_NAME, "price_color").text
        try:
            # Remove o '£' e converte para float
            price_float = float(price.replace('£', ''))
        except ValueError:
            price_float = 0.0 # Valor padrão em caso de erro    
            
            
            
        # Disponibilidade: 'In stock (22 available)' -> extrai apenas o texto
        availability = driver.find_element(By.CLASS_NAME, "instock.availability").text
        match = re.search(r'\d+', availability)
        if match:
            availability_int = int(match.group(0))
        else:
            availability_int = 0 # Valor padrão se não encontrar número
            
            
        # Rating: A classe é 'star-rating Five', pegamos a segunda parte 'Five'
        rating_element = driver.find_element(By.CSS_SELECTOR, "p.star-rating")
        rating = rating_element.get_attribute("class").replace("star-rating ", "")
        rating_float = rating_map.get(rating, 0.0)
        
        # Categoria: Usa XPath para encontrar o terceiro item da lista de breadcrumb
        category = driver.find_element(By.XPATH, "//ul[@class='breadcrumb']/li[3]/a").text

        # Imagem: Pega o src e junta com a URL base
        image_relative_url = driver.find_element(By.CSS_SELECTOR, "div.item.active img").get_attribute("src")
        image_url = image_relative_url.replace("../..", "https://books.toscrape.com")


        # Adiciona os dados a uma lista de dicionários
        all_books_details.append({
            "titulo": title,
            "preço": price_float,
            "rating": rating_float,
            "disponibilidade": availability_int,
            "categoria": category,
            "imagem": image_url,
            "url_livro": url
        })

        # Pequena pausa para não sobrecarregar o servidor
        # time.sleep(0.5) 

    except Exception as e:
        print(f"  -> Erro ao extrair dados da URL {url}: {e}")
        continue
    

# %%
df = pd.DataFrame(all_books_details)



# %%

# Diretório do notebook
notebook_dir = os.getcwd()

# Caminho correto para a pasta data no diretório principal
data_dir = os.path.join(notebook_dir, "..", "data")
os.makedirs(data_dir, exist_ok=True)  # garante que a pasta exista

# Caminho completo do CSV
csv_path = os.path.join(data_dir, "books_details.csv")

# Salva o DataFrame
df.to_csv(csv_path, index=False)

print(f"CSV salvo em: {os.path.abspath(csv_path)}")


# %%
NOME_DO_BANCO = 'challenge1.sqlite'
NOME_DA_TABELA = 'books_details'

# %%


# Diretório do notebook
notebook_dir = os.getcwd()

# Caminho correto para o banco na pasta data do projeto
data_dir = os.path.join(notebook_dir, "..", "data")
os.makedirs(data_dir, exist_ok=True)  # cria a pasta caso não exista

# Caminho completo do banco
db_path = os.path.join(data_dir, NOME_DO_BANCO)

# Conecta ao banco
conn = sqlite3.connect(db_path)

# Salva o DataFrame na tabela (substituindo se já existir)
df.to_sql(NOME_DA_TABELA, conn, if_exists='replace', index=False)

# Fecha a conexão
conn.close()

print(f"Banco salvo em: {os.path.abspath(db_path)}")

# %%


# %%


# %%


# %%


# %%



