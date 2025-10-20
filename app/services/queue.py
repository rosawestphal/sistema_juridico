# app/services/queue.py
import os
import json
import asyncio
from aio_pika import connect_robust, Message

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq/")

async def publish_document_event(document_id: int, path: str):
    conn = await connect_robust(RABBIT_URL)
    async with conn:
        channel = await conn.channel()
        await channel.default_exchange.publish(
            Message(body=json.dumps({"documento_id": document_id, "path": path}).encode()),
            routing_key="pdf_extract"
        )
