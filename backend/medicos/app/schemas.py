from pydantic import BaseModel, ConfigDict, Field


class EspecialidadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    icono: str


class MedicoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    especialidad_id: str
    experiencia: str
    rating: float


class SugerirIn(BaseModel):
    texto: str = Field(min_length=1, max_length=1000)


class SugerenciaOut(BaseModel):
    especialidad_id: str
    nombre: str
    icono: str
    puntaje: int
