# app/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .models import ExtracaoStatus

class ProcessoCreate(BaseModel):
    classe: str
    numero: int
    orgao_origem: str

class ProcessoOut(BaseModel):
    classe: str
    numero: int
    orgao_origem: str
    documentos: List[dict]

class UploadResponse(BaseModel):
    status: str
    checksum: str
    documento_id: int

class DocumentoOut(BaseModel):
    id: int
    checksum: str
    texto: Optional[str]

class StatusOut(BaseModel):
    status: ExtracaoStatus
    data_criacao: datetime
    data_atualizacao: datetime
