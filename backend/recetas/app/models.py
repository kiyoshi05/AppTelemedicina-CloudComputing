from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Medicamento(Base):
    """Catálogo de medicamentos que el médico puede recetar."""

    __tablename__ = "medicamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    presentacion: Mapped[str] = mapped_column(String(80))


class Receta(Base):
    __tablename__ = "recetas"

    id: Mapped[int] = mapped_column(primary_key=True)
    # cita_id y paciente_id pertenecen a otros microservicios: sin llave foránea.
    cita_id: Mapped[int] = mapped_column(unique=True, index=True)
    paciente_id: Mapped[int] = mapped_column(index=True)
    medico_nombre: Mapped[str] = mapped_column(String(120))
    especialidad_id: Mapped[str] = mapped_column(String(30))
    fecha: Mapped[str] = mapped_column(String(10))
    indicaciones: Mapped[str] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    items: Mapped[list["RecetaItem"]] = relationship(
        back_populates="receta", cascade="all, delete-orphan", lazy="selectin"
    )


class RecetaItem(Base):
    __tablename__ = "receta_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    receta_id: Mapped[int] = mapped_column(ForeignKey("recetas.id"), index=True)
    medicamento: Mapped[str] = mapped_column(String(120))
    dosis: Mapped[str] = mapped_column(String(200))

    receta: Mapped[Receta] = relationship(back_populates="items")
