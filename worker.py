# worker.py
import asyncio
import json
import os
from aio_pika import connect_robust, IncomingMessage
from app.db import AsyncSessionLocal
from app.models import Documento, ExtracaoStatus
from sqlmodel import select
from datetime import datetime
import pdfminer

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq/")

async def handle_message(message: IncomingMessage):
    async with message.process():
        payload = json.loads(message.body.decode())
        doc_id = payload["documento_id"]
        path = payload["path"]
        # update status EM_EXECUCAO
        async with AsyncSessionLocal() as session:
            q = await session.exec(select(Documento).where(Documento.id == doc_id))
            doc = q.first()
            if not doc:
                return
            doc.status = ExtracaoStatus.EM_EXECUCAO
            doc.updated_at = datetime.utcnow()
            session.add(doc)
            await session.commit()
        try:
            # extract text
            with open(path, "rb") as f:
                pdf = pdfminer.high_level.extract_text(f)
                texto = "\n\n".join(pdf)
            # persist
            async with AsyncSessionLocal() as session:
                q = await session.exec(select(Documento).where(Documento.id == doc_id))
                doc = q.first()
                doc.texto = texto
                doc.status = ExtracaoStatus.CONCLUIDA
                doc.updated_at = datetime.utcnow()
                session.add(doc)
                await session.commit()
        except Exception as e:
            async with AsyncSessionLocal() as session:
                q = await session.exec(select(Documento).where(Documento.id == doc_id))
                doc = q.first()
                if doc:
                    doc.status = ExtracaoStatus.FALHA_NO_PROCESSAMENTO
                    doc.updated_at = datetime.utcnow()
                    session.add(doc)
                    await session.commit()

async def main():
    conn = await connect_robust(RABBIT_URL)
    channel = await conn.channel()
    queue = await channel.declare_queue("pdf_extract", durable=True)
    await queue.consume(handle_message)
    print("Worker listening on queue pdf_extract...")
    try:
        await asyncio.Future()  # run forever
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
