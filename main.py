import jwt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from db import engine, SessionLocal, Base
from models import TaskDB, UserDB
from security import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

# Cipta table dalam database kalau belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Beritahu FastAPI token diambil dari endpoint /login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Data yang kita terima dari user
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    done: bool = False


# Data yang kita hantar balik (ada id)
class TaskResponse(TaskCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Data untuk register user
class UserCreate(BaseModel):
    email: EmailStr
    password: str


# Data user yang dihantar balik (TIADA password)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


# Buka sambungan database untuk setiap request, tutup bila siap
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Semak token dan cari siapa user yang sedang login
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_error = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_error

    user = db.get(UserDB, user_id)
    if user is None:
        raise credentials_error
    return user


# Cari task milik user tertentu sahaja
def get_owned_task(task_id: int, user: UserDB, db: Session):
    task = (
        db.query(TaskDB)
        .filter(TaskDB.id == task_id, TaskDB.owner_id == user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/")
def home():
    return {"message": "Hello, Task Manager API!"}


@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = UserDB(email=user.email, hashed_password=hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_task = TaskDB(**task.model_dump(), owner_id=current_user.id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    return db.query(TaskDB).filter(TaskDB.owner_id == current_user.id).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    return get_owned_task(task_id, current_user, db)


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_task = get_owned_task(task_id, current_user, db)
    db_task.title = task.title
    db_task.description = task.description
    db_task.done = task.done
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    db_task = get_owned_task(task_id, current_user, db)
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}