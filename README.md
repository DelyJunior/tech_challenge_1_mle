# \# Books API — Tech Challenge (Fase 1)

# 

# \## Visão geral do projeto

# Este repositório implementa um pipeline completo para disponibilizar dados de livros por meio de uma API pública, simulando um cenário real de construção de uma base para \*\*recomendações de livros\*\*. O fluxo contempla:

# 

# \- \*\*Ingestão (on demand)\*\* por scraping do site fonte.

# \- \*\*Processamento/ETL\*\* com validações e normalizações.

# \- \*\*Armazenamento\*\* em \*\*SQLite\*\*.

# \- \*\*API REST (FastAPI)\*\* com endpoints Core, Insights e ML-Ready.

# \- \*\*Consumo\*\* por cientistas de dados e aplicações de ML.

# 

# > O objetivo é garantir uma base consistente para consumo analítico e treinamento de modelos, com foco em escalabilidade e reuso.

# 

# ---

# 

# \## Arquitetura (alto nível)

# 

# \- Fonte: https://books.toscrape.com/

# \- Scraper (Selenium) → CSV: `data/books\_details.csv`

# \- ETL (validação/limpeza) → SQLite: `data/challenge1.sqlite` (tabela `books\_details`)

# \- API (FastAPI) → Endpoints Core/Insights/ML/Auth

# \- Consumidores (DS/ML): recebem JSON; predições são persistidas via `/api/v1/ml/predictions`

# 

# > Tabelas auxiliares geridas pela API: `users`, `ml\_predictions`.

# 

# ---

# 

# \## Estrutura recomendada de pastas

# 

# ```

# .

# ├─ data/

# │  ├─ books\_details.csv

# │  └─ challenge1.sqlite

# ├─ notebooks/

# │  ├─ bookstoscrape\_Scraper.ipynb

# │  ├─ exploratory\_data\_analysis.ipynb

# │  └─ model\_pipeline.ipynb

# ├─ main.py

# ├─ auth.py

# ├─ db\_usuarios.py

# ├─ requirements.txt (recomendado)

# └─ README.md

# ```

# 

# ---

# 

# \## Pré-requisitos

# 

# \- Python 3.11+ recomendado

# \- Google Chrome instalado (para Selenium)

# \- ChromeDriver compatível com sua versão do Chrome

# &nbsp; - Dica: use webdriver-manager ou instale manualmente o ChromeDriver

# \- Pip/venv (ou Conda) para isolar dependências

# 

# ---

# 

# \## Instalação e configuração

# 

# \### 1) Criar e ativar o ambiente virtual

# \- venv (padrão Python)

# &nbsp; - Windows:

# &nbsp;   - `python -m venv .venv`

# &nbsp;   - `.venv\\Scripts\\activate`

# &nbsp; - macOS/Linux:

# &nbsp;   - `python3 -m venv .venv`

# &nbsp;   - `source .venv/bin/activate`

# 

# \### 2) Instalar dependências

# Crie um `requirements.txt` (sugestão):

# 

# ```

# fastapi

# uvicorn\[standard]

# python-jose\[cryptography]

# passlib

# python-multipart

# pandas

# selenium

# webdriver-manager

# tqdm

# fuzzywuzzy

# ```

# 

# Instale:

# \- `pip install -r requirements.txt`

# 

# Observações:

# \- `sqlite3` é da biblioteca padrão do Python.

# \- `python-multipart` é necessário para o formulário do login (OAuth2PasswordRequestForm).

# \- O notebook importa `fuzzywuzzy` e `tqdm` (usados no scraping).

# 

# \### 3) Preparar diretório de dados

# \- Garanta a existência da pasta `data/`:

# &nbsp; - `mkdir data` (macOS/Linux)

# &nbsp; - `mkdir data` (PowerShell/Windows)

# 

# ---

# 

# \## Pipeline de dados

# 

# \### 1) Ingestão (Scraping)

# \- Notebook: `notebooks/bookstoscrape\_Scraper.ipynb`

# &nbsp; - Acessa `https://books.toscrape.com/`

# &nbsp; - Paginação por `.next`

# &nbsp; - Coleta links dos livros (cards `.product\_pod → h3 > a\[href]`)

# &nbsp; - Para cada livro, extrai:

# &nbsp;   - `titulo` (h1.text)

# &nbsp;   - `preço` (string “£..” → float)

# &nbsp;   - `rating` (classe em `p.star-rating` → mapeamento One..Five → 1.0..5.0)

# &nbsp;   - `disponibilidade` (regex de dígitos em “In stock (N available)” → int)

# &nbsp;   - `categoria`, `imagem` (URL absoluta), `url\_livro` (href da página)

# &nbsp; - Gera CSV em `data/books\_details.csv`

# 

# > Dica Selenium:

# > - Importe exceções: `from selenium.common.exceptions import NoSuchElementException`

# > - Prefira `WebDriverWait`/`EC` em vez de `time.sleep` fixo.

# 

# \### 2) ETL (validação/limpeza)

# \- Leitura: `data/books\_details.csv`

# \- Validações recomendadas:

# &nbsp; - Schema e tipos:

# &nbsp;   - `titulo:str`, `preço:float`, `rating:float (1.0–5.0)`, `disponibilidade:int (>=0)`, `categoria:str`, `imagem:str`, `url\_livro:str`

# &nbsp; - Deduplicação por `url\_livro`

# &nbsp; - Normalização (trim) e checagem de faixas (`preço >= 0`, `rating ∈ \[1..5]`)

# \- Carga: grava no SQLite `data/challenge1.sqlite`, tabela `books\_details`

# &nbsp; - No notebook: `df.to\_sql('books\_details', conn, if\_exists='replace', index=False)`

# 

# ---

# 

# \## Executando a API

# 

# \### 1) Ajustes mínimos (opcional, mas recomendado)

# \- No `auth.py`, substitua a `SECRET\_KEY` por um valor forte.

# \- Avançado: externalize `SECRET\_KEY` como variável de ambiente e ajuste o código para ler via `os.getenv`.

# 

# \### 2) Subir a aplicação (ambiente local)

# \- Na raiz do projeto:

# &nbsp; - `uvicorn main:app --reload`

# \- A API subirá, por padrão, em: `http://127.0.0.1:8000`

# 

# \### 3) Documentação automática (FastAPI)

# \- Swagger UI: `http://127.0.0.1:8000/docs`

# \- Redoc: `http://127.0.0.1:8000/redoc`

# 

# ---

# 

# \## Banco de dados

# 

# \- Caminho: `data/challenge1.sqlite` (conforme `main.py`)

# \- Tabelas utilizadas:

# &nbsp; - `books\_details`: fonte principal para os endpoints Core/Insights/ML

# &nbsp; - `users`: criada por `/add\_user` (auth)

# &nbsp; - `ml\_predictions`: criada por `/api/v1/ml/predictions` (persistência de predições)

# 

# > Importante: os endpoints utilizam `rowid` como `ID` lógico ao retornar `/api/v1/books/{id}`.

# 

# ---

# 

# \## Documentação das rotas (com exemplos)

# 

# \### Saúde e raiz

# \- GET `/` 

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/`

# &nbsp;   - Response: `{"message":"Hello, FastAPI!"}`

# 

# \- GET `/api/v1/health`

# &nbsp; - Verifica acesso ao SQLite e conta registros.

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/health`

# &nbsp;   - Response (ex.): `{"status":"ok","total\_livros": 1000}`

# 

# \### Core

# \- GET `/api/v1/books`

# &nbsp; - Retorna livros com disponibilidade > 0 (campos: `titulo`).

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/books`

# &nbsp;   - Response (ex.): `{"livros\_disponiveis":\[{"titulo":"A Light in the Attic"}, ...]}`

# 

# \- GET `/api/v1/books/{id:int}`

# &nbsp; - Retorna o registro completo por `rowid`.

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/books/1`

# &nbsp;   - Response (ex.): 

# &nbsp;     ```

# &nbsp;     {

# &nbsp;       "ID": 1,

# &nbsp;       "titulo": "...",

# &nbsp;       "preço": 51.77,

# &nbsp;       "rating": 3.0,

# &nbsp;       "disponibilidade": 22,

# &nbsp;       "categoria": "Poetry",

# &nbsp;       "imagem": "https://...",

# &nbsp;       "url\_livro": "https://..."

# &nbsp;     }

# &nbsp;     ```

# 

# \- GET `/api/v1/books/search?title\&category`

# &nbsp; - Busca por `titulo` e/ou `categoria` (LIKE).

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl "http://127.0.0.1:8000/api/v1/books/search?title=light\&category=Poetry"`

# &nbsp;   - Response (ex.): `{"resultado":\[{"ID":1,"titulo":"A Light in the Attic","categoria":"Poetry","disponibilidade":22}]}`

# 

# \- GET `/api/v1/categories`

# &nbsp; - Lista categorias com disponibilidade > 0.

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/categories`

# &nbsp;   - Response (ex.): `{"Categorias\_disponiveis":\[{"categoria":"Poetry"}, {"categoria":"Fiction"}, ...]}`

# 

# \### Insights

# \- GET `/api/v1/stats/overview`

# &nbsp; - Retorna: total de livros, preço médio, distribuição de ratings.

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/stats/overview`

# &nbsp;   - Response (ex.): 

# &nbsp;     ```

# &nbsp;     {

# &nbsp;       "total\_livros": 1000,

# &nbsp;       "preco\_medio": 35.77,

# &nbsp;       "distribuicao\_ratings": \[{"rating":5.0,"total":200}, ...]

# &nbsp;     }

# &nbsp;     ```

# 

# \- GET `/api/v1/stats/categories`

# &nbsp; - Retorna, por categoria: quantidade, preço médio, min, max.

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/stats/categories`

# &nbsp;   - Response (ex.):

# &nbsp;     ```

# &nbsp;     {

# &nbsp;       "categorias":\[

# &nbsp;         {"categoria":"Poetry","quantidade":20,"preco\_medio":31.2,"preco\_min":10.5,"preco\_max":55.0}

# &nbsp;       ]

# &nbsp;     }

# &nbsp;     ```

# 

# \### Extras

# \- GET `/api/v1/books/top-rated?limit=10`

# &nbsp; - Retorna livros com `rating = 5` (corte em memória pelo `limit`).

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl "http://127.0.0.1:8000/api/v1/books/top-rated?limit=5"`

# &nbsp;   - Response (ex.): `{"top\_rated\_books":\[{"titulo":"Sapiens...", "categoria":"History", "rating":5.0}, ...]}`

# 

# \- GET `/api/v1/books/price-range?min=10\&max=30`

# &nbsp; - Filtra em memória por faixa de preço.

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl "http://127.0.0.1:8000/api/v1/books/price-range?min=10\&max=30"`

# &nbsp;   - Response (ex.):

# &nbsp;     ```

# &nbsp;     {

# &nbsp;       "livros\_filtrados":\[

# &nbsp;         {"titulo":"The Requiem Red","categoria":"Young Adult","preço":22.65,"disponibilidade":"19"}

# &nbsp;       ]

# &nbsp;     }

# &nbsp;     ```

# 

# \### ML-Ready

# \- GET `/api/v1/ml/features`

# &nbsp; - Retorna features numéricas limpas de `rating`, `preco`, com `categoria` e `disponibilidade`.

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/ml/features`

# &nbsp;   - Response (ex.):

# &nbsp;     ```

# &nbsp;     {

# &nbsp;       "features\_data":\[{"titulo":"...","rating":4.0,"preco":47.82,"categoria":"Mystery","disponibilidade":20}],

# &nbsp;       "total\_registros": 980

# &nbsp;     }

# &nbsp;     ```

# 

# \- GET `/api/v1/ml/training-data`

# &nbsp; - Retorna dataset pronto para treino com \*\*OHE\*\* de `categoria`:

# &nbsp;   - `X\_rating` (float)

# &nbsp;   - `X\_categoria\_ohe` (vetor binário)

# &nbsp;   - `Y\_preco` (float)

# &nbsp;   - `one\_hot\_encoding\_map` (ordem das categorias)

# &nbsp; - Exemplo:

# &nbsp;   - Request: `curl http://127.0.0.1:8000/api/v1/ml/training-data`

# &nbsp;   - Response (ex.):

# &nbsp;     ```

# &nbsp;     {

# &nbsp;       "training\_data":\[{"X\_rating":4.0,"X\_categoria\_ohe":\[0,1,0,...],"Y\_preco":47.82}],

# &nbsp;       "total\_samples": 980,

# &nbsp;       "one\_hot\_encoding\_map": \["Poetry","Mystery","History", ...]

# &nbsp;     }

# &nbsp;     ```

# 

# \- POST `/api/v1/ml/predictions`

# &nbsp; - Persiste predições em `ml\_predictions`.

# &nbsp; - Body (JSON, lista de objetos):

# &nbsp;   ```

# &nbsp;   \[

# &nbsp;     {

# &nbsp;       "predicted\_price": 39.9,

# &nbsp;       "input\_features": {"rating":4.0,"categoria":"Mystery"},

# &nbsp;       "model\_version": "v1.0.0"

# &nbsp;     }

# &nbsp;   ]

# &nbsp;   ```

# &nbsp; - Exemplo:

# &nbsp;   - Request:

# &nbsp;     ```

# &nbsp;     curl -X POST http://127.0.0.1:8000/api/v1/ml/predictions \\

# &nbsp;       -H "Content-Type: application/json" \\

# &nbsp;       -d '\[{"predicted\_price":39.9,"input\_features":{"rating":4.0,"categoria":"Mystery"},"model\_version":"v1.0.0"}]'

# &nbsp;     ```

# &nbsp;   - Response (ex.):

# &nbsp;     ```

# &nbsp;     {"message":"Sucesso ao receber e armazenar 1 de 1 predições no SQLite.","status":"stored\_ok"}

# &nbsp;     ```

# 

# \### Autenticação (bônus)

# \- POST `/add\_user`

# &nbsp; - Cria tabela `users` se não existir e insere usuário com senha hasheada.

# &nbsp; - Body (JSON):

# &nbsp;   ```

# &nbsp;   {"username":"admin","password":"s3cr3t"}

# &nbsp;   ```

# &nbsp; - Exemplo:

# &nbsp;   - Request:

# &nbsp;     ```

# &nbsp;     curl -X POST http://127.0.0.1:8000/add\_user \\

# &nbsp;       -H "Content-Type: application/json" \\

# &nbsp;       -d '{"username":"admin","password":"s3cr3t"}'

# &nbsp;     ```

# &nbsp;   - Response (ex.): `{"message":"Usuário admin criado com sucesso!"}`

# 

# \- POST `/api/v1/auth/login`

# &nbsp; - Retorna JWT (OAuth2PasswordRequestForm).

# &nbsp; - Exemplo:

# &nbsp;   - Request:

# &nbsp;     ```

# &nbsp;     curl -X POST http://127.0.0.1:8000/api/v1/auth/login \\

# &nbsp;       -H "Content-Type: application/x-www-form-urlencoded" \\

# &nbsp;       -d "username=admin\&password=s3cr3t"

# &nbsp;     ```

# &nbsp;   - Response (ex.):

# &nbsp;     ```

# &nbsp;     {"access\_token":"<JWT>", "token\_type":"bearer"}

# &nbsp;     ```

# 

# \- POST `/api/v1/auth/refresh`

# &nbsp; - Renova token (header Authorization: Bearer <token>).

# &nbsp; - Exemplo:

# &nbsp;   - Request:

# &nbsp;     ```

# &nbsp;     curl -X POST http://127.0.0.1:8000/api/v1/auth/refresh \\

# &nbsp;       -H "Authorization: Bearer <JWT>"

# &nbsp;     ```

# &nbsp;   - Response (ex.):

# &nbsp;     ```

# &nbsp;     {"access\_token":"<NEW\_JWT>", "token\_type":"bearer"}

# &nbsp;     ```

# 

# > Observação: por padrão, as rotas não estão protegidas com `Depends(get\_current\_user)`. Você pode aplicar a proteção em endpoints sensíveis seguindo o comentário no `main.py`.

# 

# ---

# 

# \## Execução ponta-a-ponta (passo a passo)

# 

# 1\. Criar e ativar venv; instalar dependências (`pip install -r requirements.txt`).

# 2\. Criar a pasta `data/`.

# 3\. Executar o notebook `notebooks/bookstoscrape\_Scraper.ipynb` para gerar:

# &nbsp;  - `data/books\_details.csv`

# &nbsp;  - `data/challenge1.sqlite` (tabela `books\_details`)

# 4\. Subir a API:

# &nbsp;  - `uvicorn main:app --reload`

# 5\. Acessar documentação:

# &nbsp;  - Swagger: `http://127.0.0.1:8000/docs`

# 6\. (Opcional) Criar usuário e obter token JWT:

# &nbsp;  - POST `/add\_user` → POST `/api/v1/auth/login`

# 7\. Realizar chamadas aos endpoints (Core, Insights, ML).

# 8\. (Opcional) Persistir predições:

# &nbsp;  - POST `/api/v1/ml/predictions` → tabela `ml\_predictions`.

# 

# ---

# 

# \## Boas práticas e próximos passos

# 

# \- \*\*Padronização de caminhos\*\*:

# &nbsp; - Garanta que o notebook grave em `data/books\_details.csv` e `data/challenge1.sqlite` (coerente com o `main.py`).

# \- \*\*Validação no ETL\*\*:

# &nbsp; - Checagem explícita de schema, deduplicação por `url\_livro`, faixas e nulos críticos.

# \- \*\*Índices no SQLite\*\*:

# &nbsp; - Criar índices (ex.: `categoria`, `titulo`, `rating`) para acelerar buscas e consultas estatísticas.

# \- \*\*Segurança\*\*:

# &nbsp; - Mover `SECRET\_KEY` para variável de ambiente e usar no `auth.py`.

# &nbsp; - Aplicar `Depends(get\_current\_user)` onde necessário.

# \- \*\*Escalabilidade futura\*\*:

# &nbsp; - Migrar para Postgres gerenciado.

# &nbsp; - Agendar scraping (cron/Lambda) e usar fila (SQS/Kafka) para desacoplar.

# &nbsp; - Múltiplas instâncias da API atrás de um Load Balancer.

# &nbsp; - Observabilidade: logs estruturados, métricas e dashboard.

# 

# ---

# 

