"""Histórico local transacional; nenhuma dependência além de sqlite3."""
import json
import sqlite3
from contextlib import contextmanager, closing
from pathlib import Path
from threading import RLock
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

Mode = Literal['EXPLAIN', 'TUTOR', 'LAB', 'QUIZ', 'DEBUG', 'ANALYZE', 'COURSE']


class Source(BaseModel):
    label: str = Field(max_length=8)
    material_id: UUID
    name: str = Field(max_length=180)
    page: int = Field(ge=1)
    text: str = Field(max_length=500)


class Message(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID
    role: Literal['user', 'assistant']
    content: str = Field(max_length=100000)
    mode: Mode
    status: Literal['generating', 'complete', 'cancelled', 'error'] | None = None
    error: str | None = Field(default=None, max_length=2000)
    model: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=2000)
    finishReason: str | None = Field(default=None, max_length=32)
    tokensPerSecond: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    sources: list[Source] = Field(default_factory=list, max_length=3)


class Conversation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: UUID
    title: str = Field(min_length=1, max_length=200)
    category: Literal['Cybersecurity', 'Linux', 'Networking', 'Programming', 'Labs']
    mode: Mode
    draft: str = Field(default='', max_length=12000)
    messages: list[Message] = Field(max_length=10000)


class History(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=0)
    mutation: UUID
    chats: list[Conversation] = Field(max_length=500)

    @model_validator(mode='after')
    def unique_ids(self):
        ids = [str(chat.id) for chat in self.chats]
        messages = [str(message.id) for chat in self.chats for message in chat.messages]
        if len(ids) != len(set(ids)) or len(messages) != len(set(messages)):
            raise ValueError('IDs duplicados no histórico')
        return self


class HistoryStore:
    def __init__(self, folder: Path):
        self.path = folder / 'history.sqlite3'
        self.backup_path = folder / 'history.backup.sqlite3'
        self.lock = RLock()
        self.initialized = False

    @contextmanager
    def connect(self):
        with self.lock:
            db = sqlite3.connect(self.path, timeout=5)
            try:
                db.execute('PRAGMA foreign_keys=ON')
                version = db.execute('PRAGMA user_version').fetchone()[0]
                if version not in (0, 1):
                    raise sqlite3.DatabaseError('Versão de banco incompatível')
                if version == 0:
                    db.executescript('''BEGIN IMMEDIATE;
                        CREATE TABLE meta (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, mutation TEXT NOT NULL);
                        INSERT INTO meta VALUES(1,0,'');
                        CREATE TABLE chats (id TEXT PRIMARY KEY, position INTEGER NOT NULL, data TEXT NOT NULL);
                        CREATE TABLE messages (id TEXT PRIMARY KEY, chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE, position INTEGER NOT NULL, data TEXT NOT NULL);
                        CREATE INDEX messages_chat ON messages(chat_id,position);
                        PRAGMA user_version=1;
                        COMMIT;''')
                if not self.initialized:
                    if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                        raise sqlite3.DatabaseError('Falha de integridade')
                    changed = False
                    for identifier, raw in db.execute('SELECT id,data FROM messages').fetchall():
                        value = json.loads(raw)
                        if value.get('status') == 'generating':
                            value.update(status='cancelled', note='Geração interrompida ao fechar o aplicativo. Texto salvo recuperado.')
                            db.execute('UPDATE messages SET data=? WHERE id=?', (json.dumps(value, ensure_ascii=False), identifier))
                            changed = True
                    if changed:
                        db.execute("UPDATE meta SET revision=revision+1, mutation='' WHERE id=1")
                    db.commit()
                    self.initialized = True
                yield db
            finally:
                db.close()

    def read(self):
        with self.connect() as db:
            chats = []
            for identifier, raw in db.execute('SELECT id,data FROM chats ORDER BY position'):
                chat = json.loads(raw)
                chat['messages'] = [json.loads(row[0]) for row in db.execute('SELECT data FROM messages WHERE chat_id=? ORDER BY position', (identifier,))]
                chats.append(chat)
            return {'revision': db.execute('SELECT revision FROM meta').fetchone()[0], 'chats': chats}

    def save(self, value: History):
        with self.connect() as db:
            with db:
                db.execute('BEGIN IMMEDIATE')
                revision, mutation = db.execute('SELECT revision,mutation FROM meta').fetchone()
                if mutation == str(value.mutation):
                    return {'revision': revision}
                if revision != value.revision:
                    raise HTTPException(409, 'Histórico mudou em outra janela. Feche esta janela e reabra antes de continuar; alterações não salvas permanecem nesta janela.')
                db.execute('DELETE FROM chats')
                for position, chat in enumerate(value.chats):
                    data = chat.model_dump(mode='json', exclude_none=True)
                    messages = data.pop('messages')
                    db.execute('INSERT INTO chats VALUES(?,?,?)', (data['id'], position, json.dumps(data, ensure_ascii=False)))
                    for order, message in enumerate(messages):
                        db.execute('INSERT INTO messages VALUES(?,?,?,?)', (message['id'], data['id'], order, json.dumps(message, ensure_ascii=False)))
                db.execute('UPDATE meta SET revision=?,mutation=? WHERE id=1', (revision + 1, str(value.mutation)))
            return {'revision': revision + 1}

    def backup(self):
        with self.connect() as db:
            temporary = self.backup_path.with_suffix('.tmp')
            with closing(sqlite3.connect(temporary)) as target:
                db.backup(target)
            temporary.replace(self.backup_path)
        return {'message': 'Backup local criado.', 'path': str(self.backup_path)}

    def restore(self, revision: int):
        # Ler o backup sem criar um arquivo vazio quando ele não existe.
        with self.lock:
            if not self.backup_path.exists():
                raise HTTPException(404, 'Nenhum backup local disponível.')
            with closing(sqlite3.connect(self.backup_path.as_uri() + '?mode=ro', uri=True)) as source:
                if source.execute('PRAGMA quick_check').fetchone()[0] != 'ok' or source.execute('PRAGMA user_version').fetchone()[0] != 1:
                    raise sqlite3.DatabaseError('Backup inválido')
                chats = []
                for identifier, raw in source.execute('SELECT id,data FROM chats ORDER BY position'):
                    chat = json.loads(raw)
                    chat['messages'] = [json.loads(row[0]) for row in source.execute('SELECT data FROM messages WHERE chat_id=? ORDER BY position', (identifier,))]
                    for message in chat['messages']:
                        if message.get('status') == 'generating':
                            message.update(status='cancelled', note='Resposta parcial recuperada do backup.')
                    chats.append(chat)
            value = History(revision=revision, mutation=uuid4(), chats=chats)
            with self.connect() as db:
                with closing(sqlite3.connect(self.path.with_name('history.before-restore.sqlite3'))) as target:
                    db.backup(target)
            self.save(value)
            return self.read()
