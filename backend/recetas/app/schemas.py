from pydantic import BaseModel, ConfigDict, Field


class MedicamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    presentacion: str


class RecetaItemIn(BaseModel):
    medicamento: str = Field(min_length=1, max_length=120)
    dosis: str = Field(min_length=1, max_length=200)


class RecetaItemOut(RecetaItemIn):
    model_config = ConfigDict(from_attributes=True)


class RecetaCreate(BaseModel):
    cita_id: int
    paciente_id: int
    medico_nombre: str = Field(min_length=1, max_length=120)
    especialidad_id: str = Field(min_length=1, max_length=30)
    fecha: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    indicaciones: str = Field(min_length=1)
    items: list[RecetaItemIn] = Field(min_length=1)


class RecetaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cita_id: int
    paciente_id: int
    medico_nombre: str
    especialidad_id: str
    fecha: str
    indicaciones: str
    items: list[RecetaItemOut]
