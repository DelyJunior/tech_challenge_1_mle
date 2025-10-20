import subprocess

def run_scraping():
    script_path = "notebooks/bookstoscrape.py"
    print("Iniciando execução do script de scraping...")

    try:
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        print(result.stdout)
        print("✅ Script executado com sucesso!")
    except Exception as e:
        print("❌ Erro ao executar o script:")
        print(e)
