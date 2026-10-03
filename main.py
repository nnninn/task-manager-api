from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from db import engine, SessionLocal, Base
from models import TaskDB

# Cipta table dalam database kalau belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI()


# Data yang kita terima dari user
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    done: bool = False


# Data yang kita hantar balik (ada id)
class TaskResponse(TaskCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Buka sambungan database untuk setiap request, tutup bila siap
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Hello, Task Manager API!"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = TaskDB(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(TaskDB).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.get(TaskDB, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    db_task = db.get(TaskDB, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.title = task.title
    db_task.description = task.description
    db_task.done = task.done
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.get(TaskDB, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}