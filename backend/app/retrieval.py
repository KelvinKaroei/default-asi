"""Índice local FAISS persistido atomicamente junto ao acervo."""
import asyncio
from contextlib import closing
import hashlib
import json
import sqlite3

import faiss
import numpy as np
from fastapi import HTTPException

MODEL = 'embeddinggemma:300m'


class Retrieval:
    def __init__(self, folder, runtime, lock):
        self.path = folder / 'materials.sqlite3'
        self.runtime, self.lock = runtime, lock
        self.task = None
        self.progress = {'running': False, 'completed': 0, 'total': 0, 'error': ''}
        with closing(self.connect()) as db:
            db.execute('CREATE TABLE IF NOT EXISTS rag_index(id INTEGER PRIMARY KEY CHECK(id=1), signature TEXT NOT NULL, model TEXT NOT NULL, chunks TEXT NOT NULL, vector BLOB NOT NULL, checksum TEXT NOT NULL)')
            db.commit()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute('PRAGMA secure_delete=ON')
        return db

    def documents(self, db):
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='materials'").fetchone():
            return []
        return db.execute('SELECT id,name,digest,pages FROM materials ORDER BY id').fetchall()

    @staticmethod
    def signature(rows):
        return hashlib.sha256(json.dumps([(r[0], r[1], r[2]) for r in rows]).encode()).hexdigest()

    def status(self):
        with closing(self.connect()) as db:
            rows = self.documents(db)
            current = db.execute('SELECT signature,chunks FROM rag_index WHERE id=1').fetchone()
            return {**self.progress, 'ready': bool(current and current[0] == self.signature(rows)),
                    'documents': len(rows), 'chunks': len(json.loads(current[1])) if current else 0, 'model': MODEL}

    async def model_identity(self):
        tags = await self.runtime.call('GET', '/api/tags')
        model = next((m for m in tags.get('models', []) if m['name'] == MODEL), None)
        if not model:
            raise HTTPException(400, 'Modelo local de busca ausente. Instale embeddinggemma:300m antes de indexar.')
        info = await self.runtime.call('POST', '/api/show', json={'model': MODEL})
        if info.get('remote_host') or info.get('remote_model') or 'embedding' not in info.get('capabilities', []):
            raise HTTPException(400, 'O modelo de busca deve oferecer embeddings locais.')
        return model.get('digest', MODEL)

    async def embed(self, inputs):
        result = await self.runtime.call('POST', '/api/embed', json={'model': MODEL, 'input': inputs, 'truncate': False, 'keep_alive': '2m'}, timeout=120)
        vectors = np.asarray(result['embeddings'], dtype='float32')
        if vectors.ndim != 2 or len(vectors) != len(inputs) or not np.isfinite(vectors).all() or (np.linalg.norm(vectors, axis=1) == 0).any():
            raise ValueError('Embedding inválido')
        faiss.normalize_L2(vectors)
        return vectors

    def start(self):
        if self.progress['running'] or self.lock.locked():
            raise HTTPException(409, 'Aguarde a operação de IA atual antes de indexar.')
        self.progress = {'running': True, 'completed': 0, 'total': 0, 'error': ''}
        self.task = asyncio.create_task(self.build())
        return self.status()

    async def build(self):
        try:
            async with self.lock:
                identity = await self.model_identity()
                with closing(self.connect()) as db:
                    rows = self.documents(db)
                signature = self.signature(rows)
                chunks = []
                for identifier, name, _, pages in rows:
                    for page in json.loads(pages):
                        text = page['text']
                        for start in range(0, len(text), 340):
                            part = text[start:start + 420].strip()
                            if part:
                                chunks.append({'material_id': identifier, 'name': name, 'page': page['page'], 'text': part})
                            if len(chunks) > 5000:
                                raise HTTPException(400, 'Acervo excedeu 5.000 trechos. Reduza os materiais para indexar este protótipo.')
                self.progress['total'] = len(chunks)
                if not chunks:
                    raise HTTPException(400, 'Importe materiais com texto antes de indexar.')
                index = None
                for start in range(0, len(chunks), 16):
                    batch = chunks[start:start + 16]
                    vectors = await self.embed([f"title: {c['name']} | text: {c['text']}" for c in batch])
                    if index is None:
                        index = faiss.IndexFlatIP(vectors.shape[1])
                    index.add(vectors)
                    self.progress['completed'] += len(batch)
                blob = faiss.serialize_index(index).tobytes()
                with closing(self.connect()) as db, db:
                    db.execute('BEGIN IMMEDIATE')
                    if signature != self.signature(self.documents(db)):
                        raise HTTPException(409, 'O acervo mudou durante a indexação. Indexe novamente.')
                    db.execute('INSERT OR REPLACE INTO rag_index VALUES(1,?,?,?,?,?)', (signature, identity, json.dumps(chunks, ensure_ascii=False), blob, hashlib.sha256(blob).hexdigest()))
        except asyncio.CancelledError:
            self.progress['error'] = 'Indexação interrompida. O índice anterior foi preservado.'
            raise
        except Exception as error:
            self.progress['error'] = error.detail if isinstance(error, HTTPException) else 'Falha na indexação. Confira o modelo local e tente novamente.'
        finally:
            self.progress['running'] = False

    async def search(self, query):
        with closing(self.connect()) as db:
            row = db.execute('SELECT signature,model,chunks,vector,checksum FROM rag_index WHERE id=1').fetchone()
            if not row or row[0] != self.signature(self.documents(db)):
                raise HTTPException(409, 'Indexe o acervo atualizado na Base de conhecimento antes de consultar materiais.')
        if await self.model_identity() != row[1]:
            raise HTTPException(409, 'O modelo de busca mudou. Reindexe o acervo.')
        if hashlib.sha256(row[3]).hexdigest() != row[4]:
            raise HTTPException(409, 'Índice corrompido. Reindexe o acervo.')
        query_vector = await self.embed(['task: search result | query: ' + query[:1200]])
        index = faiss.deserialize_index(np.frombuffer(row[3], dtype='uint8').copy())
        if query_vector.shape[1] != index.d:
            raise HTTPException(409, 'Dimensão do índice mudou. Reindexe o acervo.')
        scores, positions = index.search(query_vector, min(3, index.ntotal))
        chunks = json.loads(row[2])
        found = [{**chunks[int(position)], 'score': round(float(score), 3)} for score, position in zip(scores[0], positions[0]) if position >= 0 and score >= .55]
        with closing(self.connect()) as db:
            if row[0] != self.signature(self.documents(db)):
                raise HTTPException(409, 'O acervo mudou durante a busca. Tente novamente após reindexar.')
        return found[:2]

    async def close(self):
        if self.task and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
