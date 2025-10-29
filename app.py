import streamlit as st
import requests

st.title("API Dinâmica - Mini Postman")

# URL base da API
API_URL = st.text_input("URL base da API:", "https://tech-challenge-1-mle.onrender.com")

# Token JWT (opcional)
jwt_token = st.text_input(
    "Token JWT (opcional)",
    type="password",
    value=st.session_state.get("jwt_token", "")
)

# ----------------------------------------------------------
# Botão para carregar endpoints automaticamente via OpenAPI
# ----------------------------------------------------------
if st.button("Carregar endpoints da API"):
    try:
        openapi_url = API_URL.rstrip("/") + "/openapi.json"
        response = requests.get(openapi_url)

        if response.status_code == 200:
            data = response.json()
            endpoints_info = []

            # Extrai as rotas e métodos disponíveis
            for path, methods in data.get("paths", {}).items():
                for method, details in methods.items():
                    endpoints_info.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "parameters": details.get("parameters", []),
                        "requestBody": details.get("requestBody", {})
                    })

            if endpoints_info:
                st.session_state["endpoints_info"] = endpoints_info
                st.success(f"Foram encontrados {len(endpoints_info)} endpoints na API!")
            else:
                st.warning("Nenhum endpoint encontrado no OpenAPI.")
        else:
            st.error("Não foi possível acessar o /openapi.json da API.")
    except Exception as e:
        st.error(f"Erro ao buscar endpoints: {e}")

# ----------------------------------------------------------
# Selecionar endpoint dinamicamente OU inserir manualmente
# ----------------------------------------------------------
if "endpoints_info" in st.session_state:
    st.subheader("Selecione ou insira um endpoint manualmente")
    col1, col2 = st.columns(2)

    with col1:
        options = [f"{ep['method']} {ep['path']}" for ep in st.session_state["endpoints_info"]]
        selected = st.selectbox("Escolha um endpoint detectado", options)

    with col2:
        manual_path = st.text_input("Ou insira manualmente (ex: /api/v1/books/1)")

    # Define o endpoint final
    if manual_path:
        method = st.selectbox("Método HTTP", ["GET", "POST", "PUT", "DELETE"])
        endpoint = {"path": manual_path, "method": method, "parameters": [], "requestBody": {}}
    else:
        endpoint = next(ep for ep in st.session_state["endpoints_info"]
                        if f"{ep['method']} {ep['path']}" == selected)

    st.write(f"Método: `{endpoint['method']}`")
    st.write(f"Caminho: `{endpoint['path']}`")
    if endpoint.get("summary"):
        st.info(endpoint["summary"])

    # ----------------------------------------------------------
    # Interface de entrada
    # ----------------------------------------------------------
    user_inputs = {}

    # Casos especiais: add_user e login
    if endpoint["path"].endswith("/add_user") and endpoint["method"] == "POST":
        st.subheader("Criar novo usuário")
        user_inputs["username"] = st.text_input("Username", key="add_user_username")
        user_inputs["password"] = st.text_input("Password", type="password", key="add_user_password")

    elif endpoint["path"].endswith("/api/v1/auth/login") and endpoint["method"] == "POST":
        st.subheader("Login")
        user_inputs["username"] = st.text_input("Username", key="login_username")
        user_inputs["password"] = st.text_input("Password", type="password", key="login_password")

    # Parâmetros normais
    elif endpoint["parameters"]:
        st.subheader("Parâmetros")
        for param in endpoint["parameters"]:
            name = param["name"]
            required = param.get("required", False)
            param_type = param.get("schema", {}).get("type", "string")
            label = f"{name}{' (obrigatório)' if required else ''}"

            if param_type == "boolean":
                user_inputs[name] = st.checkbox(label)
            else:
                user_inputs[name] = st.text_input(label)

    else:
        st.caption("Este endpoint não requer parâmetros específicos.")

    # ----------------------------------------------------------
    # Enviar requisição
    # ----------------------------------------------------------
    if st.button("Enviar requisição"):
        try:
            url = API_URL.rstrip("/") + endpoint["path"]
            headers = {"Authorization": f"Bearer {jwt_token}"} if jwt_token else {}

            # login -> form-data
            if endpoint["path"].endswith("/api/v1/auth/login"):
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                response = requests.post(url, headers=headers, data=user_inputs)

            # add_user -> JSON
            elif endpoint["path"].endswith("/add_user"):
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=user_inputs)

            # Outros endpoints dinâmicos
            else:
                headers["Content-Type"] = "application/json"
                if endpoint["method"] == "GET":
                    response = requests.get(url, headers=headers, params=user_inputs)
                elif endpoint["method"] in ["POST", "PUT", "DELETE"]:
                    response = requests.request(
                        method=endpoint["method"],
                        url=url,
                        headers=headers,
                        json=user_inputs
                    )
                else:
                    st.warning(f"Método {endpoint['method']} ainda não suportado.")

            # Exibir resultado
            st.write("Status:", response.status_code)
            try:
                result = response.json()
                st.json(result)
                # salva token automaticamente
                if "access_token" in result:
                    st.session_state["jwt_token"] = result["access_token"]
                    st.success("Token JWT armazenado automaticamente!")
            except Exception:
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro ao enviar requisição: {e}")
else:
    st.info("Clique em 'Carregar endpoints da API' para listar as rotas disponíveis.")
