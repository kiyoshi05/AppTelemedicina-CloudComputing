from pydantic import BaseModel, ConfigDict, Field


class CitaCreate(BaseModel):
    paciente_id: int
    medico_id: int
    fecha: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    hora: str = Field(pattern=r"^\d{2}:\d{2}$")


class CitaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paciente_id: int
    medico_id: int
    medico_nombre: str
    especialidad_id: str
    fecha: str
    hora: str
    estado: str


class HoraDisponible(BaseModel):
    hora: str
    disponible: bool
