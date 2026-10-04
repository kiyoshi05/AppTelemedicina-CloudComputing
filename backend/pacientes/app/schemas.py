from pydantic import BaseModel, ConfigDict, Field

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class PacienteCreate(BaseModel):
    nombres: str = Field(min_length=2, max_length=120)
    documento: str | None = Field(default=None, max_length=20)
    fecha_nacimiento: str | None = Field(default=None, max_length=10)
    telefono: str | None = Field(default=None, max_length=20)
    sexo: str | None = Field(default=None, max_length=30)
    email: str = Field(pattern=EMAIL_REGEX, max_length=120)
    password: str = Field(min_length=6, max_length=100)


class LoginIn(BaseModel):
    email: str
    password: str


class PacienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombres: str
    documento: str | None
    fecha_nacimiento: str | None
    telefono: str | None
    sexo: str | None
    email: str
