"""Microservicio de pacientes: registro, login y perfil."""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Paciente
from .schemas import LoginIn, PacienteCreate, PacienteOut
from .security import hash_password, verify_password
from .seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(
    title="SaludYa · Pacientes",
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "servicio": "pacientes"}


@app.post("/registro", response_model=PacienteOut, status_code=status.HTTP_201_CREATED)
def registrar(datos: PacienteCreate, db: Session = Depends(get_db)):
    email = datos.email.strip().lower()
    if db.scalar(select(Paciente).where(Paciente.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta con ese correo")
    paciente = Paciente(
        **datos.model_dump(exclude={"email", "password"}),
        email=email,
        password_hash=hash_password(datos.password),
    )
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    return paciente


@app.post("/login", response_model=PacienteOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    paciente = db.scalar(select(Paciente).where(Paciente.email == datos.email.strip().lower()))
    if not paciente or not verify_password(datos.password, paciente.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    return paciente


@app.get("/{paciente_id}", response_model=PacienteOut)
def obtener(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado")
    return paciente
