# Sistema de Análise de Processos Jurídicos

API REST assíncrona para cadastro de processos, upload de PDFs e extração de texto com processamento em segundo plano usando RabbitMQ.

## Arquitetura MVC

O projeto segue o padrão **MVC**:

```
         +-----------------+
         |     Cliente      |
         |  (API/Swagger)   |
         +--------+--------+
                  |
                  v
         +-----------------+
         |       API       |
         |  FastAPI (async) |
         +--------+--------+
                  |
       +----------+-----------+
       |                      |
       v                      v
+--------------+        +-------------+
|  Models/DB   |        |  Worker     |
|  SQLite      |        | RabbitMQ    |
+--------------+        +-------------+
       |                      |
       +----------+-----------+
                  |
                  v
            Armazenamento
            de PDFs local
```
- **Models**: definição das tabelas Processo e Documento, status de extração.  
- **Views/Controllers**: rotas FastAPI (`routers/processos.py`) que respondem JSON.  
- **Services/Helpers**: `storage.py` para salvar PDFs, `queue.py` para publicar eventos.  
- **Worker**: consome RabbitMQ, extrai texto via `pdftotext` e atualiza status no DB.

## Requisitos

- Python 3.10+
- poppler-utils (`sudo apt-get install -y poppler-utils`) para pdftotext
- SQLite (embutido)

## Estrutura de diretórios

```
processos_api/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   └── services/
├── data/uploads/        # PDFs enviados
├── tests/               # Testes automatizados
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Execução local (SQLite)

1. Criar ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows
```
2. Instalar dependências:
```bash
pip install -r requirements.txt
```
3. Criar diretórios de upload:
```bash
mkdir -p data/uploads
```
4. Rodar a API:
```bash
uvicorn app.main:app --reload
```
5. Rodar o worker em outro terminal:
```bash
python worker.py
```

A API estará disponível em [http://localhost:8000/docs](http://localhost:8000/docs) com Swagger.

## Execução via Docker + RabbitMQ

1. Construir e subir serviços:
```bash
docker compose up --build
```
- `api` → FastAPI (porta 8000)
- `rabbitmq` → fila de mensagens (porta 5672 e 15672 para management)
- `worker` → consome fila `pdf_extract` e extrai texto dos PDFs

## Testes automatizados

Executar testes com `pytest`:
```bash
pytest tests
```

## Endpoints principais

- `POST /api/processos` → criar processo
- `POST /api/processos/{processo_id}/documentos` → enviar PDF
- `GET /api/processos/{processo_id}` → consultar dados do processo
- `GET /api/processos/{processo_id}/documentos/{documento_id}` → consultar documento e texto
- `GET /api/processos/{processo_id}/documentos/{documento_id}/status` → status da extração
