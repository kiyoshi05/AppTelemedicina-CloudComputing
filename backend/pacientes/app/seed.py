from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Paciente
from .security import hash_password

# Paciente de demostración (id = 1). Los servicios de citas y recetas
# usan este id en sus propios datos de ejemplo.
DEMO = {
    "nombres": "María Rojas Delgado",
    "documento": "70000001",
    "fecha_nacimiento": "1990-05-14",
    "telefono": "987654321",
    "sexo": "Femenino",
    "email": "maria.rojas@gmail.com",
    "password": "demo1234",
}


def seed(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Paciente)):
        return
    datos = dict(DEMO)
    password = datos.pop("password")
    db.add(Paciente(**datos, password_hash=hash_password(password)))
    db.commit()
