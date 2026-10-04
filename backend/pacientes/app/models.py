from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombres: Mapped[str] = mapped_column(String(120))
    documento: Mapped[str | None] = mapped_column(String(20))
    fecha_nacimiento: Mapped[str | None] = mapped_column(String(10))
    telefono: Mapped[str | None] = mapped_column(String(20))
    sexo: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
