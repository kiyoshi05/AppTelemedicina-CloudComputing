from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

CONFIRMADA = "Confirmada"
CANCELADA = "Cancelada"
COMPLETADA = "Completada"


class Cita(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(primary_key=True)
    # paciente_id y medico_id apuntan a datos de otros microservicios,
    # por eso no son llaves foráneas.
    paciente_id: Mapped[int] = mapped_column(index=True)
    medico_id: Mapped[int] = mapped_column(index=True)
    # Copia de datos del médico para mostrar la cita sin llamar a otro servicio.
    medico_nombre: Mapped[str] = mapped_column(String(120))
    especialidad_id: Mapped[str] = mapped_column(String(30))
    fecha: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD
    hora: Mapped[str] = mapped_column(String(5))  # HH:MM
    estado: Mapped[str] = mapped_column(String(20), default=CONFIRMADA)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        # Un médico no puede tener dos citas activas en la misma fecha y hora.
        Index(
            "ux_cita_activa",
            "medico_id",
            "fecha",
            "hora",
            unique=True,
            sqlite_where=text(f"estado != '{CANCELADA}'"),
        ),
    )
