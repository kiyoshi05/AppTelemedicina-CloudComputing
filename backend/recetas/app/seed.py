import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Medicamento, Receta, RecetaItem

ZONA = timezone(timedelta(hours=int(os.getenv("TZ_OFFSET_HOURS", "-5"))))

MEDICAMENTOS = [
    ("Losartán 50mg", "Tabletas"),
    ("Ácido acetilsalicílico 100mg", "Tabletas"),
    ("Paracetamol 500mg", "Tabletas"),
    ("Ibuprofeno 400mg", "Tabletas"),
    ("Amoxicilina 500mg", "Cápsulas"),
    ("Loratadina 10mg", "Tabletas"),
    ("Omeprazol 20mg", "Cápsulas"),
    ("Hidrocortisona 1%", "Crema"),
]


def seed(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Medicamento)):
        return
    db.add_all(Medicamento(nombre=n, presentacion=p) for n, p in MEDICAMENTOS)

    # Receta de la cita completada de ejemplo (cita 1 de la paciente demo).
    fecha = (datetime.now(ZONA).date() - timedelta(days=15)).isoformat()
    db.add(
        Receta(
            cita_id=1,
            paciente_id=1,
            medico_nombre="Dr. Jorge Salas",
            especialidad_id="cardio",
            fecha=fecha,
            indicaciones="Reposo relativo, control de presión 2 veces al día.",
            items=[
                RecetaItem(medicamento="Losartán 50mg", dosis="1 tableta cada 24h por 30 días"),
                RecetaItem(
                    medicamento="Ácido acetilsalicílico 100mg",
                    dosis="1 tableta cada 24h, con alimentos",
                ),
            ],
        )
    )
    db.commit()
