import streamlit as st
import requests
import json

st.set_page_config(page_title="API Tester Dinâmico", layout="wide")
st.title("API Tester Dinâmico - Mini Postman")

# Base da API
API_URL = st.text_input("Digite a URL base da API:", "https://tech-challenge-1-mle.onrender.com")

# Escolha do método HTTP
metodo = st.selectbox("Método HTTP", ["GET", "POST"])

# Endpoint
rota = st.text_input("Caminho da rota (ex: /api/v1/books, /add_user)")

# JWT opcional
jwt_token = st.text_input("Token JWT (opcional para endpoints protegidos)")

# Inputs dinâmicos dependendo do método
body = None
data = None
if metodo == "POST":
    tipo_post = st.radio("Tipo de POST", ["JSON", "Form-data"])
    if tipo_post == "JSON":
        json_input = st.text_area("JSON do corpo da requisição", '{"username": "teste", "password": "123456"}')
        try:
            body = json.loads(json_input)
        except json.JSONDecodeError:
            st.warning("JSON inválido! Verifique a sintaxe.")
    else:
        # Form-data dinâmico: campo chave=valor separados por vírgula
        st.markdown("Exemplo: username=teste,password=123456")
        form_input = st.text_input("Form-data (chave=valor separados por vírgula)")
        if form_input:
            data = {}
            try:
                for item in form_input.split(","):
                    k, v = item.split("=")
                    data[k.strip()] = v.strip()
            except:
                st.warning("Erro na formatação do form-data")

# Botão de envio
if st.button("Enviar Requisição"):
    if not rota:
        st.warning("Preencha a rota!")
    else:
        if not rota.startswith("/"):
            rota = "/" + rota
        url = API_URL.rstrip("/") + rota
        headers = {}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"
        try:
            if metodo == "GET":
                response = requests.get(url, headers=headers)
            elif metodo == "POST":
                if body:
                    response = requests.post(url, json=body, headers=headers)
                else:
                    response = requests.post(url, data=data, headers=headers)
            st.write("Status:", response.status_code)
            try:
                st.json(response.json())
            except:
                st.write(response.text)
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")
