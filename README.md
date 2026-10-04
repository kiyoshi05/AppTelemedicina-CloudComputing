# SaludYa · Telemedicina (MVP)

Aplicación web responsive para agendar citas médicas en línea: registro de pacientes, sugerencia de especialidad según síntomas, reserva de citas con médicos y consulta de recetas digitales.

El frontend está separado del backend, y el backend está dividido en **4 microservicios FastAPI, uno por dominio**, cada uno con su propia base **SQLite**. Todo corre con **Docker Compose** en una sola **EC2 t2.micro** de AWS.

## Arquitectura

```
                Navegador (PC o celular)
                          │  HTTP :80
                          ▼
   ┌─────────────── EC2 t2.micro (Docker Compose) ───────────────┐
   │                                                             │
   │   frontend  ·  Nginx :80                                    │
   │   - sirve el front (HTML, CSS, JS)                          │
   │   - API gateway: /api/<servicio>/... → microservicio        │
   │        │             │              │             │         │
   │        ▼             ▼              ▼             ▼         │
   │   pacientes      medicos          citas        recetas      │
   │   :8001          :8002            :8003        :8004        │
   │     │              │                │             │         │
   │ pacientes.db   medicos.db       citas.db     recetas.db     │
   │   (SQLite)      (SQLite)        (SQLite)      (SQLite)      │
   └─────────────────────────────────────────────────────────────┘
```

| Microservicio | Dominio | Responsabilidad | Tablas |
|---|---|---|---|
| `pacientes` | Paciente | Registro, login y perfil | `pacientes` |
| `medicos` | Médicos | Especialidades, médicos, horarios y sugerencia por síntomas | `especialidades`, `medicos`, `horarios`, `reglas_sintomas` |
| `citas` | Agenda | Disponibilidad, reserva, cancelación e historial | `citas` |
| `recetas` | Medicinas | Recetas digitales y catálogo de medicamentos | `medicamentos`, `recetas`, `receta_items` |

**Reglas de diseño**

- Cada microservicio es dueño de su base de datos; ninguno lee el `.db` de otro.
- Las relaciones entre dominios se guardan por id (`paciente_id`, `medico_id`), sin llaves foráneas entre bases.
- `citas` valida al paciente y al médico llamando por HTTP a `pacientes` y `medicos` dentro de la red de Docker.
- Solo Nginx publica un puerto (80). Los microservicios no son accesibles desde Internet.

## Estructura del repositorio

```
saludya-telemedicina/
├── frontend/                  # Front + API gateway (Nginx)
│   ├── Dockerfile
│   ├── nginx.conf
│   └── public/
│       ├── index.html
│       ├── css/styles.css
│       └── js/
│           ├── api.js         # llamadas a los microservicios
│           └── app.js         # lógica de la interfaz
├── backend/
│   ├── pacientes/             # cada microservicio tiene la misma forma:
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py        # endpoints
│   │       ├── models.py      # tablas (SQLAlchemy)
│   │       ├── schemas.py     # validación (Pydantic)
│   │       ├── database.py    # conexión a SQLite
│   │       └── seed.py        # datos iniciales
│   ├── medicos/
│   ├── citas/                 # + clients.py (llamadas a pacientes y medicos)
│   └── recetas/
├── postman/saludya.postman_collection.json
├── scripts/ec2-setup.sh       # prepara la EC2 (Docker, Compose, swap)
├── docs/DEPLOY_AWS.md         # guía paso a paso para AWS
└── docker-compose.yml
```

## Ejecutar en local

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) abierto.

```bash
docker compose up -d --build
```

Abre http://localhost. Si el puerto 80 está ocupado, usa otro, por ejemplo `FRONT_PORT=8080 docker compose up -d --build`, y abre http://localhost:8080.

Usuario de demostración: `maria.rojas@gmail.com` / `demo1234` (ya tiene una cita confirmada y una cita completada con receta).

Para detener todo:

```bash
docker compose down
```

`docker compose down -v` además borra los volúmenes, es decir, todas las bases SQLite.

## Endpoints

Todos pasan por el gateway. La documentación interactiva (Swagger) de cada servicio está en `/api/<servicio>/docs`, por ejemplo http://localhost/api/citas/docs.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/pacientes/registro` | Registrar paciente |
| POST | `/api/pacientes/login` | Iniciar sesión |
| GET | `/api/pacientes/{id}` | Datos del paciente |
| GET | `/api/medicos/especialidades` | Especialidades |
| GET | `/api/medicos/?especialidad=cardio` | Médicos de una especialidad |
| GET | `/api/medicos/{id}` | Datos de un médico |
| GET | `/api/medicos/{id}/horario` | Horas de atención |
| POST | `/api/medicos/sugerir` | Top 3 de especialidades según síntomas |
| GET | `/api/citas/?paciente_id=1` | Citas de un paciente |
| GET | `/api/citas/disponibilidad?medico_id=3&fecha=AAAA-MM-DD` | Horas libres y ocupadas |
| POST | `/api/citas/` | Agendar cita |
| PATCH | `/api/citas/{id}/cancelar` | Cancelar cita |
| PATCH | `/api/citas/{id}/completar` | Marcar cita como atendida |
| GET | `/api/recetas/?paciente_id=1` | Recetas de un paciente |
| GET | `/api/recetas/cita/{cita_id}` | Receta de una cita |
| POST | `/api/recetas/` | Emitir receta |
| GET | `/api/recetas/medicamentos` | Catálogo de medicamentos |

La colección de Postman está en `postman/`. Cambia la variable `base_url` según dónde pruebes.

## Despliegue en AWS

Ver la guía paso a paso: [docs/DEPLOY_AWS.md](docs/DEPLOY_AWS.md).

## Limitaciones del MVP y próximos pasos

- **Autenticación:** el login valida la contraseña (guardada con hash PBKDF2), pero los demás servicios no verifican un token. Siguiente paso: JWT emitido por `pacientes` y validado en el gateway.
- **HTTPS:** la app se sirve por HTTP. Siguiente paso: dominio propio y certificado de Let's Encrypt en Nginx.
- **SQLite** permite una escritura a la vez por base; para más usuarios, migrar a PostgreSQL o Amazon RDS.
- **Sugerencia por síntomas:** se basa en palabras clave, no en IA.
