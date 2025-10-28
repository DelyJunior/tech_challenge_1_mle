import streamlit as st
import requests

st.title("API Dinâmica - Mini Postman")

# URL base da API
API_URL = st.text_input("URL base da API:", "https://tech-challenge-1-mle.onrender.com")

# Token JWT opcional
jwt_token = st.text_input("Token JWT (opcional)", type="password")

# -----------------------------
# Configuração dinâmica dos endpoints
# -----------------------------
endpoints = {
    "/add_user": {
        "method": "POST",
        "fields": ["username", "password"],  # campos obrigatórios
        "type": "JSON",
        "requires_token": False
    },
    "/api/v1/auth/login": {
        "method": "POST",
        "fields": ["username", "password"],  # campos obrigatórios
        "type": "Form-data",
        "requires_token": False
    },
    "/api/v1/scraping/trigger": {
        "method": "GET",
        "fields": [],  # GET não precisa de campos
        "type": "GET",
        "requires_token": True
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
    is_required = (rota in ["/add_user", "/api/v1/auth/login"])
    if "password" in field.lower():
        inputs[field] = st.text_input(f"{field}{' (obrigatório)' if is_required else ''}", type="password")
    else:
        inputs[field] = st.text_input(f"{field}{' (obrigatório)' if is_required else ''}")

# -----------------------------
# Botão de envio
# -----------------------------
if st.button("Enviar Requisição"):
    # Verifica se é necessário token
    if config.get("requires_token") and not jwt_token:
        st.warning("Não foi possível executar: é necessário informar o token JWT")
    else:
        url = API_URL.rstrip("/") + rota
        headers = {}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        try:
            if config["method"] == "GET":
                response = requests.get(url, headers=headers)
            elif config["method"] == "POST":
                # Checar campos obrigatórios
                if rota in ["/add_user", "/api/v1/auth/login"] and (not inputs.get("username") or not inputs.get("password")):
                    st.warning("Username e Password são obrigatórios para este endpoint")
                else:
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
