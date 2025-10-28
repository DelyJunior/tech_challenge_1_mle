import streamlit as st
import requests

st.title("API Dinâmica - Mini Postman")

API_URL = st.text_input("URL base da API:", "https://tech-challenge-1-mle.onrender.com")

jwt_token = st.text_input("Token JWT (opcional)")

# -----------------------------
# Configuração dinâmica dos endpoints
# -----------------------------
endpoints = {
    "/add_user": {
        "method": "POST",
        "fields": ["username", "password"],  # campos que serão exibidos
        "type": "JSON"
    },
    "/api/v1/auth/login": {
        "method": "POST",
        "fields": ["username", "password"],
        "type": "Form-data"
    },
    "/api/v1/scraping/trigger": {
        "method": "GET",
        "fields": [],  # GET não precisa de campos
        "type": "GET"
    }
}

# -----------------------------
# Selecionar endpoint
# -----------------------------
rota = st.selectbox("Escolha o endpoint", list(endpoints.keys()))
config = endpoints[rota]

st.write(f"Método: {config['method']} | Tipo: {config['type']}")

# -----------------------------
# Gerar inputs dinamicamente
# -----------------------------
inputs = {}
for field in config["fields"]:
    if "password" in field.lower():
        inputs[field] = st.text_input(field, type="password")
    else:
        inputs[field] = st.text_input(field)

# -----------------------------
# Botão de envio
# -----------------------------
if st.button("Enviar Requisição"):
    url = API_URL.rstrip("/") + rota
    headers = {}
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"

    try:
        if config["method"] == "GET":
            response = requests.get(url, headers=headers)
        elif config["method"] == "POST":
            if config["type"] == "JSON":
                response = requests.post(url, json=inputs, headers=headers)
            else:  # form-data
                response = requests.post(url, data=inputs, headers=headers)
        st.write("Status:", response.status_code)
        try:
            st.json(response.json())
        except:
            st.write(response.text)
    except Exception as e:
        st.error(f"Erro: {e}")
