import streamlit as st
import requests

st.set_page_config(page_title="API Dinâmica", layout="wide")
st.title("Mini Postman Dinâmico - API Tech Challenge")

# -----------------------------
# Configurações base
# -----------------------------
API_URL = st.text_input("URL base da API:", "http://127.0.0.1:8000")
jwt_token = st.text_input("Token JWT (opcional)", type="password")

# -----------------------------
# Pegar endpoints dinamicamente
# -----------------------------
try:
    response = requests.get(API_URL.rstrip("/") + "/api/v1/endpoints")
    endpoints_list = response.json()
    endpoint_display = [f"{e['path']} ({','.join(e['methods'])})" for e in endpoints_list]
    selected = st.selectbox("Escolha o endpoint", endpoint_display)
except Exception as e:
    st.warning(f"Não foi possível buscar endpoints: {e}")
    endpoints_list = []
    selected = None

# -----------------------------
# Configuração de campos POST
# -----------------------------
POST_FIELDS = {
    "/add_user": ["username", "password"],        # username não obrigatório para criar usuário
    "/api/v1/auth/login": ["username", "password"]  # username obrigatório
}

# -----------------------------
# Ação ao clicar no botão
# -----------------------------
if selected:
    path = selected.split(" ")[0]
    methods = [m.strip() for m in selected.split("(")[1].replace(")","").split(",")]
    st.write(f"Métodos disponíveis: {methods}")

    inputs = {}
    if "POST" in methods:
        st.subheader("Campos para POST")
        fields = POST_FIELDS.get(path, [])
        for field in fields:
            is_required = field=="username" and path=="/api/v1/auth/login"
            if "password" in field.lower():
                inputs[field] = st.text_input(f"{field}{' (obrigatório)' if is_required else ''}", type="password")
            else:
                inputs[field] = st.text_input(f"{field}{' (obrigatório)' if is_required else ''}")

    if st.button("Enviar requisição"):
        url = API_URL.rstrip("/") + path
        headers = {}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        try:
            if "GET" in methods and not "POST" in methods:
                response = requests.get(url, headers=headers)
            elif "POST" in methods:
                # Verificar obrigatórios
                if path=="/api/v1/auth/login" and (not inputs.get("username") or not inputs.get("password")):
                    st.warning("Username e Password são obrigatórios para login")
                else:
                    response = requests.post(url, json=inputs, headers=headers)
            st.write("Status:", response.status_code)
            try:
                st.json(response.json())
            except:
                st.write(response.text)
        except Exception as e:
            st.error(f"Erro: {e}")
