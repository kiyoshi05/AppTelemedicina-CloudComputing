"""Microservicio de citas: disponibilidad, reserva, cancelación y historial."""
import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import clients
from .database import Base, SessionLocal, engine, get_db
from .fechas import hoy
from .models import CANCELADA, COMPLETADA, CONFIRMADA, Cita
from .schemas import CitaCreate, CitaOut, HoraDisponible
from .seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(
    title="SaludYa · Citas",
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", ""),
    lifespan=lifespan,
)


def _horas_ocupadas(db: Session, medico_id: int, fecha: str) -> set[str]:
    consulta = select(Cita.hora).where(
        Cita.medico_id == medico_id, Cita.fecha == fecha, Cita.estado != CANCELADA
    )
    return set(db.scalars(consulta))


@app.get("/health")
def health():
    return {"status": "ok", "servicio": "citas"}


@app.get("/disponibilidad", response_model=list[HoraDisponible])
def disponibilidad(
    medico_id: int,
    fecha: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
):
    horario = clients.obtener_horario(medico_id)
    ocupadas = _horas_ocupadas(db, medico_id, fecha)
    return [HoraDisponible(hora=h, disponible=h not in ocupadas) for h in horario]


@app.get("/", response_model=list[CitaOut])
def listar_citas(paciente_id: int, db: Session = Depends(get_db)):
    consulta = (
        select(Cita)
        .where(Cita.paciente_id == paciente_id)
        .order_by(Cita.fecha.desc(), Cita.hora.desc())
    )
    return db.scalars(consulta).all()


@app.post("/", response_model=CitaOut, status_code=status.HTTP_201_CREATED)
def crear_cita(datos: CitaCreate, db: Session = Depends(get_db)):
    try:
        fecha = date.fromisoformat(datos.fecha)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Fecha inválida")
    if fecha < hoy():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No se puede agendar en una fecha pasada")

    if not clients.obtener_paciente(datos.paciente_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente no encontrado")
    medico = clients.obtener_medico(datos.medico_id)
    if not medico:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico no encontrado")
    if datos.hora not in clients.obtener_horario(datos.medico_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El médico no atiende a esa hora")
    if datos.hora in _horas_ocupadas(db, datos.medico_id, datos.fecha):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese horario ya está ocupado")

    cita = Cita(
        paciente_id=datos.paciente_id,
        medico_id=datos.medico_id,
        medico_nombre=medico["nombre"],
        especialidad_id=medico["especialidad_id"],
        fecha=datos.fecha,
        hora=datos.hora,
        estado=CONFIRMADA,
    )
    db.add(cita)
    try:
        db.commit()
    except IntegrityError:
        # Otra reserva tomó el mismo horario entre la verificación y el guardado.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese horario ya está ocupado")
    db.refresh(cita)
    return cita


def _cambiar_estado(db: Session, cita_id: int, nuevo_estado: str) -> Cita:
    cita = db.get(Cita, cita_id)
    if not cita:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cita no encontrada")
    if cita.estado != CONFIRMADA:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La cita ya está {cita.estado.lower()}")
    cita.estado = nuevo_estado
    db.commit()
    db.refresh(cita)
    return cita


@app.patch("/{cita_id}/cancelar", response_model=CitaOut)
def cancelar_cita(cita_id: int, db: Session = Depends(get_db)):
    return _cambiar_estado(db, cita_id, CANCELADA)


@app.patch("/{cita_id}/completar", response_model=CitaOut)
def completar_cita(cita_id: int, db: Session = Depends(get_db)):
    """Lo usaría el médico al terminar la consulta, antes de emitir la receta."""
    return _cambiar_estado(db, cita_id, COMPLETADA)
