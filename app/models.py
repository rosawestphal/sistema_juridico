# app/models.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
from datetime import datetime

class ExtracaoStatus(str, Enum):
    NAO_INICIADA = "NAO_INICIADA"
    EM_EXECUCAO = "EM_EXECUCAO"
    CONCLUIDA = "CONCLUIDA"
    FALHA_NO_PROCESSAMENTO = "FALHA_NO_PROCESSAMENTO"

class Processo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    classe: str
    numero: int
    orgao_origem: str
    codigo: str = Field(index=True, unique=True)  # ex: ARE123456

    documentos: List["Documento"] = Relationship(back_populates="processo")

class Documento(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    processo_id: int = Field(foreign_key="processo.id")
    filename: str
    checksum: str
    path: str
    texto: Optional[str] = None
    status: ExtracaoStatus = Field(default=ExtracaoStatus.NAO_INICIADA)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    processo: Optional[Processo] = Relationship(back_populates="documentos")
