from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .fechas import hoy
from .models import COMPLETADA, CONFIRMADA, Cita


def seed(db: Session) -> None:
    """Citas de ejemplo de la paciente demo (id 1).

    Los ids de médico coinciden con el seed del servicio de médicos, y la cita
    completada (id 1) tiene una receta en el servicio de recetas.
    """
    if db.scalar(select(func.count()).select_from(Cita)):
        return
    db.add_all(
        [
            Cita(
                paciente_id=1,
                medico_id=3,
                medico_nombre="Dr. Jorge Salas",
                especialidad_id="cardio",
                fecha=(hoy() - timedelta(days=15)).isoformat(),
                hora="10:30",
                estado=COMPLETADA,
            ),
            Cita(
                paciente_id=1,
                medico_id=5,
                medico_nombre="Dra. Ana Belén Ríos",
                especialidad_id="derma",
                fecha=(hoy() + timedelta(days=2)).isoformat(),
                hora="16:30",
                estado=CONFIRMADA,
            ),
        ]
    )
    db.commit()
