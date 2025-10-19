from nbclient import NotebookClient
from nbformat import read
import threading
import traceback

def run_scraping():
    notebook_path = "notebooks/bookstoscrape_Scraper.ipynb"
    print("Iniciando execução do notebook de scraping...")

    try:
        # Abre o notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = read(f, as_version=4)

        # Cria o client para executar o notebook
        client = NotebookClient(nb, timeout=3600, kernel_name="venv")

        # Executa o notebook
        client.execute()

        print("✅ Notebook executado com sucesso!")

    except Exception as e:
        print("❌ Erro ao executar o notebook:")
        traceback.print_exc()

