import base64
import binascii
import hashlib
import json
from pathlib import PurePosixPath, Path
import sqlite3
import subprocess
import sys
import threading
from contextlib import closing
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4, UUID

import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

MAX_BYTES = 5 * 1024 * 1024
EXTRACT_TIMEOUT = 15
MEMORY_BUDGET = 512 * 1024 * 1024


class ImportMaterial(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=180)
    content: str = Field(max_length=7_000_000)
    encoding: Literal['utf-8', 'cp1252'] = 'utf-8'


def extract_bounded(raw, extension, encoding):
    command = [sys.executable, '--extract', extension, encoding] if getattr(sys, 'frozen', False) else [sys.executable, '-m', 'app.extract_material', extension, encoding]
    process = subprocess.Popen(command,
        cwd=Path(__file__).resolve().parents[1], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    finished = threading.Event()
    exceeded = threading.Event()
    owned = {}
    def capture():
        try:
            root = psutil.Process(process.pid)
            for child in [root] + root.children(recursive=True):
                owned[(child.pid, child.create_time())] = child
        except psutil.NoSuchProcess:
            pass
    def stop():
        capture()
        for child in reversed(list(owned.values())):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
    def monitor():
        while not finished.wait(.1):
            capture()
            total = 0
            for child in list(owned.values()):
                try:
                    total += child.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            if total > MEMORY_BUDGET:
                exceeded.set()
                stop()
                return
    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    try:
        output, _ = process.communicate(raw, timeout=EXTRACT_TIMEOUT)
        if exceeded.is_set():
            raise HTTPException(400, 'Extração interrompida por consumo de memória. Divida ou simplifique o PDF.')
        if process.returncode:
            raise HTTPException(400, 'O extrator não conseguiu processar o arquivo.')
        result = json.loads(output.decode('utf-8'))
        if result.get('error'):
            raise HTTPException(400, result['error'])
        return result
    except subprocess.TimeoutExpired:
        finished.set()
        watcher.join()
        stop()
        process.communicate()
        raise HTTPException(400, 'Extração excedeu 15 segundos. Divida ou simplifique o material.')
    finally:
        finished.set()
        watcher.join()


def materials_router(folder):
    router = APIRouter(prefix='/api/v1/materials')
    path = folder / 'materials.sqlite3'
    import_lock = threading.Lock()
    schema_lock = threading.Lock()
    def connect():
        with schema_lock:
            db = sqlite3.connect(path, timeout=5)
            db.row_factory = sqlite3.Row
            try:
                db.execute('PRAGMA secure_delete=ON')
                version = db.execute('PRAGMA user_version').fetchone()[0]
                if version == 0:
                    db.executescript('''BEGIN IMMEDIATE;
                        CREATE TABLE materials(id TEXT PRIMARY KEY, name TEXT NOT NULL, extension TEXT NOT NULL, size INTEGER NOT NULL, digest TEXT NOT NULL UNIQUE, created TEXT NOT NULL, encoding TEXT NOT NULL, warning TEXT NOT NULL, pages TEXT NOT NULL, original BLOB NOT NULL);
                        PRAGMA user_version=1;
                        COMMIT;''')
                elif version != 1:
                    raise sqlite3.DatabaseError('Versão de acervo incompatível')
                return db
            except Exception:
                db.close()
                raise
    columns = 'id,name,extension,size,created,encoding,warning'

    @router.get('')
    def listing():
        with closing(connect()) as db:
            return [dict(row) for row in db.execute(f'SELECT {columns} FROM materials ORDER BY created DESC,id')]

    @router.get('/{identifier}')
    def detail(identifier: UUID):
        with closing(connect()) as db:
            row = db.execute(f'SELECT {columns},pages FROM materials WHERE id=?', (str(identifier),)).fetchone()
            if not row:
                raise HTTPException(404, 'Material não encontrado.')
            value = dict(row)
            value['pages'] = json.loads(value['pages'])
            return value

    @router.post('')
    def import_file(value: ImportMaterial):
        name = value.name.strip()
        if not name or '/' in name or '\\' in name or any(ord(c) < 32 for c in name):
            raise HTTPException(400, 'Use somente o nome do arquivo, sem caminhos.')
        extension = PurePosixPath(name).suffix.lower()
        try:
            raw = base64.b64decode(value.content, validate=True)
        except (ValueError, binascii.Error):
            raise HTTPException(400, 'Conteúdo de arquivo inválido.')
        if not raw or len(raw) > MAX_BYTES:
            raise HTTPException(400, 'Cada arquivo deve ter entre 1 byte e 5 MiB.')
        if not import_lock.acquire(blocking=False):
            raise HTTPException(409, 'Outra importação está em andamento. Aguarde e tente novamente.')
        try:
            digest = hashlib.sha256(raw).hexdigest()
            with closing(connect()) as db:
                row = db.execute('SELECT id FROM materials WHERE digest=?', (digest,)).fetchone()
                if row:
                    return {'material': detail(UUID(row['id'])), 'duplicate': True}
            result = extract_bounded(raw, extension, value.encoding)
            identifier = str(uuid4())
            with closing(connect()) as db, db:
                db.execute('BEGIN IMMEDIATE')
                count, size = db.execute('SELECT count(*),coalesce(sum(size),0) FROM materials').fetchone()
                if count >= 200 or size + len(raw) > 100 * 1024 * 1024:
                    raise HTTPException(400, 'Limite do protótipo: 200 materiais ou 100 MiB de originais. Remova materiais antes de importar.')
                # A restrição UNIQUE protege também duas instâncias do backend.
                db.execute('INSERT OR IGNORE INTO materials VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (identifier, name, extension, len(raw), digest, datetime.now(timezone.utc).isoformat(),
                     value.encoding if extension != '.pdf' else 'pdf', result['warning'], json.dumps(result['pages'], ensure_ascii=False), raw))
                actual = db.execute('SELECT id FROM materials WHERE digest=?', (digest,)).fetchone()['id']
            return {'material': detail(UUID(actual)), 'duplicate': actual != identifier}
        finally:
            import_lock.release()

    @router.delete('/{identifier}')
    def remove(identifier: UUID):
        with closing(connect()) as db, db:
            db.execute('DELETE FROM materials WHERE id=?', (str(identifier),))
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='rag_index'").fetchone():
                db.execute('DELETE FROM rag_index')
        return {'removed': True}

    return router
