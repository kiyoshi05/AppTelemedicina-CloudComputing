"""Microservicio de recetas: recetas digitales y catálogo de medicamentos."""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Medicamento, Receta, RecetaItem
from .schemas import MedicamentoOut, RecetaCreate, RecetaOut
from .seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(
    title="SaludYa · Recetas",
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "servicio": "recetas"}


@app.get("/medicamentos", response_model=list[MedicamentoOut])
def listar_medicamentos(db: Session = Depends(get_db)):
    return db.scalars(select(Medicamento).order_by(Medicamento.nombre)).all()


@app.get("/", response_model=list[RecetaOut])
def listar_recetas(paciente_id: int, db: Session = Depends(get_db)):
    consulta = select(Receta).where(Receta.paciente_id == paciente_id).order_by(Receta.fecha.desc())
    return db.scalars(consulta).all()


@app.get("/cita/{cita_id}", response_model=RecetaOut)
def receta_de_cita(cita_id: int, db: Session = Depends(get_db)):
    receta = db.scalar(select(Receta).where(Receta.cita_id == cita_id))
    if not receta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La cita no tiene receta")
    return receta


@app.post("/", response_model=RecetaOut, status_code=status.HTTP_201_CREATED)
def crear_receta(datos: RecetaCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Receta).where(Receta.cita_id == datos.cita_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa cita ya tiene una receta")
    receta = Receta(
        **datos.model_dump(exclude={"items"}),
        items=[RecetaItem(**item.model_dump()) for item in datos.items],
    )
    db.add(receta)
    db.commit()
    db.refresh(receta)
    return receta
