import streamlit as st
import requests

st.set_page_config(page_title="Meu App com API", layout="wide")

st.title("Integração com API - Tech Challenge")

# Endpoint base
API_URL = "https://tech-challenge-1-mle.onrender.com/"

# Botão para testar conexão
if st.button("Testar API"):
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            st.success("API está online!")
            st.json(response.json())
        else:
            st.warning(f"API respondeu com status {response.status_code}")
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")

# Campo para testar rota personalizada
rota = st.text_input("Digite o caminho da rota (ex: /api/v1/books). Adicionar apenas os endpoints")
if rota:
    try:
        response = requests.get(API_URL.rstrip("/") + rota)
        if response.status_code == 200:
            st.json(response.json())
        else:
            st.warning(f"Erro {response.status_code}")
    except Exception as e:
        st.error(f"{e}")
