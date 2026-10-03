"""Cursos, tentativas de quiz e checklists de laboratório persistidos localmente."""
from contextlib import closing
import json
import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .curriculum import COURSE, LABS

class Completion(BaseModel):
    model_config=ConfigDict(extra='forbid')
    complete: bool
class Answer(BaseModel):
    model_config=ConfigDict(extra='forbid')
    choice: int = Field(ge=0,le=10)

def learning_router(folder):
    router=APIRouter(prefix='/api/v1/learning')
    path=folder/'learning.sqlite3'
    def connect():
        db=sqlite3.connect(path,timeout=5)
        db.execute('PRAGMA secure_delete=ON')
        return db
    with closing(connect()) as db,db:
        db.executescript('''CREATE TABLE IF NOT EXISTS lessons(id TEXT PRIMARY KEY, complete INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0, passed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS lab_steps(lab TEXT NOT NULL, step INTEGER NOT NULL, complete INTEGER NOT NULL, PRIMARY KEY(lab,step));''')
    lessons={lesson['id']:lesson for module in COURSE['modules'] for lesson in module['lessons']}
    def lesson(identifier):
        if identifier not in lessons: raise HTTPException(404,'Lição não encontrada.')
        return lessons[identifier]
    @router.get('/course')
    def course():
        # Não enviar o gabarito antes da tentativa.
        content=json.loads(json.dumps(COURSE))
        with closing(connect()) as db:
            progress={r[0]:{'complete':bool(r[1]),'attempts':r[2],'passed':bool(r[3])} for r in db.execute('SELECT * FROM lessons')}
        for module in content['modules']:
            for item in module['lessons']:
                item['quiz'].pop('answer');item['quiz'].pop('explanation')
                item['progress']=progress.get(item['id'],{'complete':False,'attempts':0,'passed':False})
        return content
    @router.put('/lessons/{identifier}')
    def complete(identifier:str,value:Completion):
        lesson(identifier)
        with closing(connect()) as db,db:
            db.execute('INSERT INTO lessons(id,complete) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET complete=excluded.complete',(identifier,value.complete))
        return {'complete':value.complete}
    @router.post('/lessons/{identifier}/quiz')
    def quiz(identifier:str,value:Answer):
        question=lesson(identifier)['quiz']
        if value.choice>=len(question['choices']): raise HTTPException(400,'Alternativa inexistente.')
        passed=value.choice==question['answer']
        with closing(connect()) as db,db:
            db.execute('INSERT INTO lessons(id,attempts,passed) VALUES(?,1,?) ON CONFLICT(id) DO UPDATE SET attempts=attempts+1,passed=max(passed,excluded.passed)',(identifier,passed))
        return {'correct':passed,'answer':question['answer'],'explanation':question['explanation']}
    @router.get('/labs')
    def labs():
        with closing(connect()) as db:
            rows=db.execute('SELECT lab,step FROM lab_steps WHERE complete=1').fetchall()
        return [{**item,'completed':[r[1] for r in rows if r[0]==item['id']]} for item in LABS]
    @router.put('/labs/{identifier}/steps/{step}')
    def lab_step(identifier:str,step:int,value:Completion):
        item=next((lab for lab in LABS if lab['id']==identifier),None)
        if not item or step<0 or step>=len(item['steps']): raise HTTPException(404,'Etapa não encontrada.')
        with closing(connect()) as db,db:
            db.execute('INSERT OR REPLACE INTO lab_steps VALUES(?,?,?)',(identifier,step,value.complete))
        return {'complete':value.complete}
    return router
