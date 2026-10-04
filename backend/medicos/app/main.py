"""Microservicio de médicos: especialidades, médicos, horarios y sugerencia por síntomas."""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Especialidad, HorarioBase, Medico, ReglaSintoma
from .schemas import EspecialidadOut, MedicoOut, SugerenciaOut, SugerirIn
from .seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(
    title="SaludYa · Médicos",
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "servicio": "medicos"}


@app.get("/especialidades", response_model=list[EspecialidadOut])
def listar_especialidades(db: Session = Depends(get_db)):
    return db.scalars(select(Especialidad).order_by(Especialidad.nombre)).all()


@app.post("/sugerir", response_model=list[SugerenciaOut])
def sugerir(datos: SugerirIn, db: Session = Depends(get_db)):
    """Top 3 de especialidades según palabras clave en los síntomas (no es IA)."""
    texto = datos.texto.lower()
    puntos: dict[str, int] = {}
    for regla in db.scalars(select(ReglaSintoma)):
        if regla.palabra in texto:
            puntos[regla.especialidad_id] = puntos.get(regla.especialidad_id, 0) + 1

    ranking = sorted(puntos.items(), key=lambda kv: kv[1], reverse=True)
    if not ranking:
        ranking = [("general", 0)]

    especialidades = {e.id: e for e in db.scalars(select(Especialidad))}
    for esp_id in especialidades:
        if len(ranking) >= 3:
            break
        if esp_id not in dict(ranking):
            ranking.append((esp_id, 0))

    return [
        SugerenciaOut(
            especialidad_id=esp_id,
            nombre=especialidades[esp_id].nombre,
            icono=especialidades[esp_id].icono,
            puntaje=puntaje,
        )
        for esp_id, puntaje in ranking[:3]
    ]


@app.get("/", response_model=list[MedicoOut])
def listar_medicos(especialidad: str | None = None, db: Session = Depends(get_db)):
    consulta = select(Medico).order_by(Medico.nombre)
    if especialidad:
        consulta = consulta.where(Medico.especialidad_id == especialidad)
    return db.scalars(consulta).all()


@app.get("/{medico_id}", response_model=MedicoOut)
def obtener_medico(medico_id: int, db: Session = Depends(get_db)):
    medico = db.get(Medico, medico_id)
    if not medico:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado")
    return medico


@app.get("/{medico_id}/horario", response_model=list[str])
def horario_medico(medico_id: int, db: Session = Depends(get_db)):
    if not db.get(Medico, medico_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado")
    consulta = select(HorarioBase.hora).where(HorarioBase.medico_id == medico_id).order_by(HorarioBase.hora)
    return db.scalars(consulta).all()
