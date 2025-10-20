import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, engine
import asyncio
import os
import shutil
# Importando IO para simular arquivos PDF
from io import BytesIO

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Limpa e configura o ambiente antes de CADA teste
    if os.path.exists("./data"):
        shutil.rmtree("./data")
    os.makedirs("./data/uploads", exist_ok=True)
    asyncio.run(init_db())
    yield
    # Limpa o ambiente após CADA teste
    if os.path.exists("./data"):
        shutil.rmtree("./data")

def test_create_and_retrieve_processo_success():
    processo_data = {"classe":"ARE","numero":123456,"orgao_origem":"STF"}
    processo_id = f"{processo_data['classe']}{processo_data['numero']}"

    # 1. Criação (POST)
    resp_post = client.post("/api/processos", json=processo_data)
    assert resp_post.status_code == 201
    
    j_post = resp_post.json()
    assert j_post.get("status") == "processo cadastrado"

    # 2. Recuperação (GET)
    resp_get = client.get(f"/api/processos/{processo_id}")
    
    if resp_get.status_code != 200:
        pytest.fail(f"Falha ao buscar processo {processo_id}. Status: {resp_get.status_code}. Resposta do servidor: {resp_get.json()}")

    assert resp_get.status_code == 200
    j_get = resp_get.json()
    assert j_get["processo"]["classe"] == "ARE"
    assert j_get["processo"]["numero"] == 123456
    assert j_get["processo"]["documentos"] == []


def test_create_duplicate_processo_fails():
    processo_data = {"classe":"RE","numero":999,"orgao_origem":"STF"}

    # 1. Criação bem-sucedida
    resp_post = client.post("/api/processos", json=processo_data)
    assert resp_post.status_code == 201
    
    # 2. Tentativa de duplicata
    resp_duplicate = client.post("/api/processos", json=processo_data)
    assert resp_duplicate.status_code == 400
    assert resp_duplicate.json()["detail"] == "processo já existe"


def test_get_non_existent_processo_fails():
    resp = client.get("/api/processos/NAOEXISTE123")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "processo não encontrado"


def test_document_endpoints_404_cases():
    existing_process_id = "TESTE123"
    client.post("/api/processos", json={"classe":"TESTE","numero":123,"orgao_origem":"STF"})
    non_existent_process_id = "ERRO404"
    non_existent_document_id = 9999
    
    # Caso 1: Upload para processo inexistente (POST /documentos)
    files = {"file": ("test.pdf", b"pdf content", "application/pdf")}
    resp_upload = client.post(f"/api/processos/{non_existent_process_id}/documentos", files=files)
    assert resp_upload.status_code == 404
    assert resp_upload.json()["detail"] == "processo não encontrado"

    # Caso 2: Recuperar documento em processo inexistente (GET /documentos/{id})
    resp_get_doc = client.get(f"/api/processos/{non_existent_process_id}/documentos/1")
    assert resp_get_doc.status_code == 404
    assert resp_get_doc.json()["detail"] == "processo não encontrado"

    # Caso 3: Recuperar status em processo inexistente (GET /documentos/{id}/status)
    resp_get_status = client.get(f"/api/processos/{non_existent_process_id}/documentos/1/status")
    assert resp_get_status.status_code == 404
    assert resp_get_status.json()["detail"] == "processo não encontrado"

    # Caso 4: Recuperar documento inexistente em processo existente (GET /documentos/{id})
    resp_get_doc_404 = client.get(f"/api/processos/{existing_process_id}/documentos/{non_existent_document_id}")
    assert resp_get_doc_404.status_code == 404
    assert resp_get_doc_404.json()["detail"] == "documento não encontrado"

    # Caso 5: Recuperar status de documento inexistente (GET /documentos/{id}/status)
    resp_get_status_404 = client.get(f"/api/processos/{existing_process_id}/documentos/{non_existent_document_id}/status")
    assert resp_get_status_404.status_code == 404
    assert resp_get_status_404.json()["detail"] == "documento não encontrado"

