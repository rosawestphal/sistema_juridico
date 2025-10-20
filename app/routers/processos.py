# app/routers/processos.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.models import Processo, Documento, ExtracaoStatus
from app.schemas import ProcessoCreate, UploadResponse, ProcessoOut, DocumentoOut, StatusOut
from app.services.storage import save_upload
from app.services.queue import publish_document_event
import os
from datetime import datetime

router = APIRouter(prefix="/api/processos", tags=["processos"])

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("", status_code=201)
async def create_processo(payload: dict, session: AsyncSession = Depends(get_session)):
    codigo = f"{payload['classe']}{payload['numero']}"
    stmt = select(Processo).where(Processo.codigo == codigo)
    result = await session.execute(stmt)
    processo_existente = result.scalars().first()
    if processo_existente:
        raise HTTPException(status_code=400, detail="processo já existe")

    processo = Processo(
        classe=payload['classe'],
        numero=payload['numero'],
        orgao_origem=payload['orgao_origem'],
        codigo=codigo
    )
    session.add(processo)
    await session.commit()
    await session.refresh(processo)
    return {
        "status": "processo cadastrado",
        "numero": processo.numero,
        "classe": processo.classe,
        "codigo": processo.codigo
    }

@router.post("/{processo_id}/documentos", status_code=201)
async def upload_documento(processo_id: str, file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    # Buscar processo
    stmt = select(Processo).where(Processo.codigo == processo_id)
    result = await session.execute(stmt)
    processo = result.scalars().first()
    if not processo:
        raise HTTPException(status_code=404, detail="processo não encontrado")
    
    # Salvar arquivo
    path, checksum = await save_upload(file, f"{processo_id}_{file.filename}")
    
    # Criar Documento
    documento = Documento(
        processo_id=processo.id,
        filename=file.filename,
        path=path,
        checksum=checksum,
        status=ExtracaoStatus.NAO_INICIADA
    )
    session.add(documento)
    await session.commit()
    await session.refresh(documento)
    
    # Publicar evento na fila
    await publish_document_event(documento.id, path)
    
    return {
        "status": "documento cadastrado",
        "checksum": checksum,
        "documento_id": documento.id
    }

@router.get("/{processo_id}")
async def get_processo(processo_id: str, session: AsyncSession = Depends(get_session)):
    stmt = select(Processo).where(Processo.codigo == processo_id)
    result = await session.execute(stmt)
    processo = result.scalars().first()

    if not processo:
        raise HTTPException(status_code=404, detail="processo não encontrado")
    # load documentos
    q2 = await session.execute(select(Documento).where(Documento.processo_id == processo.id))
    docs = q2.all()

    return {"processo": {"classe": processo.classe, "numero": processo.numero, "orgao_origem": processo.orgao_origem, "documentos": docs}}

@router.get("/{processo_id}/documentos/{documento_id}")
async def get_documento(processo_id: str, documento_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Processo).where(Processo.codigo == processo_id)
    result = await session.execute(stmt)
    processo = result.scalars().first()
    if not processo:
        raise HTTPException(status_code=404, detail="processo não encontrado")
    qd = await session.execute(select(Documento).where(Documento.id == documento_id, Documento.processo_id == processo.id))
    documento = qd.first()
    if not documento:
        raise HTTPException(status_code=404, detail="documento não encontrado")
    return documento

@router.get("/{processo_id}/documentos/{documento_id}/status")
async def get_status(processo_id: str, documento_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Processo).where(Processo.codigo == processo_id)
    result = await session.execute(stmt)
    processo = result.scalars().first()
    if not processo:
        raise HTTPException(status_code=404, detail="processo não encontrado")
    qd = await session.execute(select(Documento).where(Documento.id == documento_id, Documento.processo_id == processo.id))
    documento = qd.first()
    if not documento:
        raise HTTPException(status_code=404, detail="documento não encontrado")
    return documento
