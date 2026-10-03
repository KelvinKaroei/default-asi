"""Memórias declaradas pelo usuário: opt-in, sem mineração automática de chats."""
from contextlib import closing
import sqlite3
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

class MemoryValue(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text: str=Field(min_length=1,max_length=160)
    @field_validator('text')
    @classmethod
    def text_valid(cls,value):
        value=value.strip()
        if not value: raise ValueError('Memória vazia')
        return value
class MemorySwitch(BaseModel):
    model_config=ConfigDict(extra='forbid')
    enabled: bool

class MemoryStore:
    def __init__(self,folder):
        self.path=folder/'memory.sqlite3'
        with closing(self.connect()) as db,db:
            db.executescript('''CREATE TABLE IF NOT EXISTS preferences(id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL);
            INSERT OR IGNORE INTO preferences VALUES(1,0);
            CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY,text TEXT NOT NULL);''')
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5);db.execute('PRAGMA secure_delete=ON');return db
    def read(self):
        with closing(self.connect()) as db:
            return {'enabled':bool(db.execute('SELECT enabled FROM preferences').fetchone()[0]),'items':[{'id':r[0],'text':r[1]} for r in db.execute('SELECT id,text FROM memories ORDER BY rowid')]}
    def context(self):
        with closing(self.connect()) as db:
            if not db.execute('SELECT enabled FROM preferences').fetchone()[0]: return []
            return [row[0] for row in db.execute('SELECT text FROM memories ORDER BY rowid')]
    def router(self):
        router=APIRouter(prefix='/api/v1/memory')
        @router.get('')
        def read(): return self.read()
        @router.put('/enabled')
        def enabled(value:MemorySwitch):
            with closing(self.connect()) as db,db: db.execute('UPDATE preferences SET enabled=?',(value.enabled,))
            return self.read()
        def save(text,identifier=None):
            with closing(self.connect()) as db,db:
                db.execute('BEGIN IMMEDIATE')
                if not db.execute('SELECT enabled FROM preferences').fetchone()[0]: raise HTTPException(409,'Ative a memória para adicionar ou editar. Apagar permanece disponível.')
                if identifier and not db.execute('SELECT 1 FROM memories WHERE id=?',(identifier,)).fetchone(): raise HTTPException(404,'Memória não encontrada.')
                rows=db.execute('SELECT id,text FROM memories').fetchall()
                others=[r[1] for r in rows if r[0]!=identifier]
                if len(others)>=3 or sum(len(t.encode('utf-8')) for t in [*others,text])>500: raise HTTPException(400,'Limite: três memórias e 500 bytes de texto ao todo. Resuma as preferências.')
                db.execute('INSERT OR REPLACE INTO memories VALUES(?,?)',(identifier or str(uuid4()),text))
            return self.read()
        @router.post('')
        def add(value:MemoryValue): return save(value.text)
        @router.put('/{identifier}')
        def edit(identifier:UUID,value:MemoryValue): return save(value.text,str(identifier))
        @router.delete('/{identifier}')
        def remove(identifier:UUID):
            with closing(self.connect()) as db,db: db.execute('DELETE FROM memories WHERE id=?',(str(identifier),))
            return self.read()
        @router.delete('')
        def clear():
            with closing(self.connect()) as db,db: db.execute('DELETE FROM memories')
            return self.read()
        return router
