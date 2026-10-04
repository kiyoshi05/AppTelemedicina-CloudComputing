from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Especialidad(Base):
    __tablename__ = "especialidades"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    icono: Mapped[str] = mapped_column(String(10))


class Medico(Base):
    __tablename__ = "medicos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    especialidad_id: Mapped[str] = mapped_column(ForeignKey("especialidades.id"), index=True)
    experiencia: Mapped[str] = mapped_column(String(30))
    rating: Mapped[float] = mapped_column(Float)


class HorarioBase(Base):
    """Horas en las que atiende cada médico. La ocupación la controla el servicio de citas."""

    __tablename__ = "horarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    medico_id: Mapped[int] = mapped_column(ForeignKey("medicos.id"), index=True)
    hora: Mapped[str] = mapped_column(String(5))


class ReglaSintoma(Base):
    """Palabra clave que asocia un síntoma con una especialidad."""

    __tablename__ = "reglas_sintomas"

    id: Mapped[int] = mapped_column(primary_key=True)
    especialidad_id: Mapped[str] = mapped_column(ForeignKey("especialidades.id"), index=True)
    palabra: Mapped[str] = mapped_column(String(60))
