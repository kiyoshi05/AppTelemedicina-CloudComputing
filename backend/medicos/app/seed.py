from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Especialidad, HorarioBase, Medico, ReglaSintoma

ESPECIALIDADES = [
    ("general", "Medicina General", "🩺"),
    ("cardio", "Cardiología", "❤️"),
    ("derma", "Dermatología", "🧴"),
    ("pediatria", "Pediatría", "🧒"),
    ("gineco", "Ginecología", "👩‍⚕️"),
    ("psico", "Psicología", "🧠"),
    ("neuro", "Neurología", "🧬"),
    ("gastro", "Gastroenterología", "🍽️"),
    ("otorrino", "Otorrinolaringología", "👂"),
    ("trauma", "Traumatología", "🦴"),
]

# El orden define los ids: Dr. Jorge Salas = 3 y Dra. Ana Belén Ríos = 5
# (los usan los datos de ejemplo de citas y recetas).
MEDICOS = [
    ("Dr. Luis Fernández", "general", "8 años", 4.8),
    ("Dra. Carla Núñez", "general", "5 años", 4.6),
    ("Dr. Jorge Salas", "cardio", "14 años", 4.9),
    ("Dra. Patricia Vega", "cardio", "10 años", 4.7),
    ("Dra. Ana Belén Ríos", "derma", "7 años", 4.8),
    ("Dra. Sofía Campos", "pediatria", "9 años", 4.9),
    ("Dr. Renzo Díaz", "pediatria", "6 años", 4.6),
    ("Dra. Karen Huamán", "gineco", "11 años", 4.8),
    ("Lic. Daniela Torres", "psico", "6 años", 4.9),
    ("Lic. Mario Chávez", "psico", "4 años", 4.5),
    ("Dr. Iván Paredes", "neuro", "12 años", 4.7),
    ("Dra. Lucía Herrera", "gastro", "9 años", 4.8),
    ("Dr. Pablo Quispe", "otorrino", "8 años", 4.6),
    ("Dr. Sergio Medina", "trauma", "13 años", 4.8),
]

HORAS = ["09:00", "09:30", "10:00", "10:30", "11:30", "15:00", "15:30", "16:30", "17:00", "17:30"]

REGLAS = {
    "neuro": ["cabeza", "migraña", "migrana", "mareo", "vertigo", "vértigo", "hormigueo", "convulsion", "convulsión"],
    "cardio": ["pecho", "palpitacion", "palpitación", "presion", "presión", "corazon", "corazón", "falta de aire"],
    "general": ["fiebre", "tos", "gripe", "resfriado", "resfrio", "resfrío", "garganta", "malestar general", "cuerpo cortado"],
    "derma": ["piel", "erupcion", "erupción", "picazon", "picazón", "acne", "acné", "grano", "mancha", "alergia"],
    "gastro": ["estomago", "estómago", "nausea", "náusea", "diarrea", "acidez", "vomito", "vómito", "abdomen"],
    "psico": ["ansiedad", "estres", "estrés", "triste", "tristeza", "insomnio", "animo", "ánimo", "panico", "pánico"],
    "otorrino": ["oido", "oído", "sinusitis", "oido tapado", "oído tapado", "zumbido"],
    "gineco": ["embarazo", "menstruacion", "menstruación", "pelvico", "pélvico", "ginecolog"],
    "pediatria": ["niño", "nina", "niña", "bebe", "bebé", "vacuna", "pediatr"],
    "trauma": ["espalda", "fractura", "torcedura", "articulacion", "articulación", "rodilla", "hombro", "golpe"],
}


def seed(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Especialidad)):
        return
    db.add_all(Especialidad(id=i, nombre=n, icono=ic) for i, n, ic in ESPECIALIDADES)
    db.flush()
    for nombre, esp, exp, rating in MEDICOS:
        medico = Medico(nombre=nombre, especialidad_id=esp, experiencia=exp, rating=rating)
        db.add(medico)
        db.flush()
        db.add_all(HorarioBase(medico_id=medico.id, hora=h) for h in HORAS)
    for esp, palabras in REGLAS.items():
        db.add_all(ReglaSintoma(especialidad_id=esp, palabra=p) for p in palabras)
    db.commit()
