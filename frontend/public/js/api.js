/* Cliente HTTP del front. Todas las rutas /api/* pasan por el gateway Nginx,
   que las reparte a cada microservicio. */
const API = {
  async request(method, url, body) {
    const opciones = { method, headers: {} };
    if (body !== undefined) {
      opciones.headers['Content-Type'] = 'application/json';
      opciones.body = JSON.stringify(body);
    }

    let respuesta;
    try {
      respuesta = await fetch(url, opciones);
    } catch (e) {
      throw new Error('No se pudo conectar con el servidor');
    }

    const texto = await respuesta.text();
    let datos = null;
    if (texto) {
      try { datos = JSON.parse(texto); } catch (e) { datos = texto; }
    }

    if (!respuesta.ok) {
      const detalle = datos && datos.detail;
      // FastAPI devuelve un texto en errores de negocio y una lista en errores de validación.
      const mensaje = typeof detalle === 'string' ? detalle
        : Array.isArray(detalle) ? 'Revisa los datos del formulario'
        : 'Error ' + respuesta.status;
      throw new Error(mensaje);
    }
    return datos;
  },
  get(url) { return this.request('GET', url); },
  post(url, body) { return this.request('POST', url, body); },
  patch(url, body) { return this.request('PATCH', url, body); },
};

/* Endpoints de cada microservicio */
const Servicios = {
  pacientes: {
    registrar: (datos) => API.post('/api/pacientes/registro', datos),
    login: (email, password) => API.post('/api/pacientes/login', { email, password }),
  },
  medicos: {
    especialidades: () => API.get('/api/medicos/especialidades'),
    porEspecialidad: (id) => API.get('/api/medicos/?especialidad=' + encodeURIComponent(id)),
    sugerir: (texto) => API.post('/api/medicos/sugerir', { texto }),
  },
  citas: {
    dePaciente: (pacienteId) => API.get('/api/citas/?paciente_id=' + pacienteId),
    disponibilidad: (medicoId, fecha) =>
      API.get('/api/citas/disponibilidad?medico_id=' + medicoId + '&fecha=' + fecha),
    crear: (datos) => API.post('/api/citas/', datos),
    cancelar: (id) => API.patch('/api/citas/' + id + '/cancelar'),
  },
  recetas: {
    dePaciente: (pacienteId) => API.get('/api/recetas/?paciente_id=' + pacienteId),
  },
};
