/* ======================= ESTADO ======================= */
const SESION_KEY = 'saludya_paciente';

let state = {
  paciente: null,          // paciente con sesión iniciada
  especialidades: [],      // catálogo del microservicio de médicos
  medicos: [],             // médicos de la especialidad elegida en el wizard
  citas: [],
  recetasPorCita: {},      // cita_id -> receta
  wizard: { especialidad: null, medico: null, dia: null, hora: null, _dias: [] },
};

function guardarSesion(p) {
  try { localStorage.setItem(SESION_KEY, JSON.stringify(p)); } catch (e) { /* sin almacenamiento */ }
}
function leerSesion() {
  try { return JSON.parse(localStorage.getItem(SESION_KEY)); } catch (e) { return null; }
}
function borrarSesion() {
  try { localStorage.removeItem(SESION_KEY); } catch (e) { /* sin almacenamiento */ }
}

/* ======================= UTILIDADES ======================= */
function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function iniciales(n) { return n.split(' ').filter(Boolean).map(p => p[0]).slice(0, 2).join('').toUpperCase(); }
function primerNombre(n) { return n.split(' ')[0]; }

function fechaLocalISO(d) {
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return d.getFullYear() + '-' + mm + '-' + dd;
}
function proximosDias(n) {
  const dias = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  const out = [];
  const hoy = new Date();
  for (let i = 1; i <= n; i++) {
    const d = new Date(hoy); d.setDate(hoy.getDate() + i);
    out.push({ iso: fechaLocalISO(d), dow: dias[d.getDay()], num: d.getDate(),
               label: d.toLocaleDateString('es-PE', { day: '2-digit', month: 'short' }) });
  }
  return out;
}

function especialidadPorId(id) {
  return state.especialidades.find(e => e.id === id) || { id, nombre: id, icono: '🩺' };
}

function toast(msg) {
  const t = document.getElementById('toast'); t.textContent = msg; t.classList.add('show');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => t.classList.remove('show'), 2600);
}

/* ======================= NAVEGACIÓN ======================= */
function go(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  window.scrollTo(0, 0);
  renderTopbar();
}
function renderTopbar() {
  const box = document.getElementById('topbarActions');
  if (state.paciente) {
    box.innerHTML = '<div class="avatar" title="' + esc(state.paciente.nombres) + '" onclick="doLogout()">' +
      esc(iniciales(state.paciente.nombres)) + '</div>';
  } else {
    box.innerHTML = '';
  }
}

/* ======================= CUENTA (microservicio pacientes) ======================= */
function entrar(paciente, mensaje) {
  state.paciente = paciente;
  guardarSesion(paciente);
  document.getElementById('bottomnav').style.display = 'flex';
  document.getElementById('homeNombre').textContent = primerNombre(paciente.nombres);
  if (mensaje) toast(mensaje);
  mostrarSub('home');
  go('view-app');
}

async function crearCuenta() {
  const valor = id => document.getElementById(id).value.trim();
  const datos = {
    nombres: valor('pNombre'),
    documento: valor('pDoc') || null,
    fecha_nacimiento: valor('pNac') || null,
    telefono: valor('pTelefono') || null,
    sexo: valor('pSexo') || null,
    email: valor('pEmail'),
    password: document.getElementById('pPass').value,
  };
  if (!datos.nombres) { toast('Ingresa tu nombre para continuar'); return; }
  if (!datos.email) { toast('Ingresa tu correo electrónico'); return; }
  if (datos.password.length < 6) { toast('La contraseña debe tener al menos 6 caracteres'); return; }
  try {
    const paciente = await Servicios.pacientes.registrar(datos);
    entrar(paciente, '¡Cuenta creada! Bienvenido(a), ' + primerNombre(paciente.nombres));
  } catch (e) {
    toast(e.message);
  }
}

async function doLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPass').value;
  if (!email || !password) { toast('Ingresa tu correo y contraseña'); return; }
  try {
    const paciente = await Servicios.pacientes.login(email, password);
    entrar(paciente, 'Bienvenido(a) de nuevo, ' + primerNombre(paciente.nombres));
  } catch (e) {
    toast(e.message);
  }
}

function doLogout() {
  state.paciente = null;
  borrarSesion();
  document.getElementById('bottomnav').style.display = 'none';
  go('view-bienvenida');
  toast('Sesión cerrada');
}

/* ======================= SUGERENCIA (microservicio médicos) ======================= */
async function sugerirEnRegistro() {
  const texto = document.getElementById('pSintomas').value.trim();
  const box = document.getElementById('sugerenciaRegistro');
  if (!texto) { box.innerHTML = '<p class="helper">Escribe algunos síntomas para recibir una sugerencia.</p>'; return; }
  try {
    const top = await Servicios.medicos.sugerir(texto);
    const e = top[0];
    box.innerHTML = '<p class="helper" style="margin-bottom:8px">Especialidad sugerida según tus síntomas:</p>' +
      '<div class="chip-card selected"><div class="chip-main"><span style="font-size:20px;margin-right:8px">' + esc(e.icono) + '</span>' +
      '<div><div class="chip-title">' + esc(e.nombre) + '</div><div class="chip-sub">Basado en tu descripción</div></div></div></div>';
  } catch (err) {
    toast(err.message);
  }
}

async function sugerirEnCita() {
  const texto = document.getElementById('citaSintomas').value.trim();
  if (!texto) { toast('Escribe tus síntomas primero'); return; }
  try {
    const top = await Servicios.medicos.sugerir(texto);
    document.getElementById('top3Helper').style.display = 'block';
    document.getElementById('top3Box').innerHTML = top.map((e, idx) =>
      '<div class="chip-card" id="chip-' + esc(e.especialidad_id) + '" onclick="elegirEspecialidad(\'' + esc(e.especialidad_id) + '\')">' +
      '<div class="chip-main"><span class="rank">' + (idx + 1) + '</span>' +
      '<div><div class="chip-title">' + esc(e.icono) + ' ' + esc(e.nombre) + '</div>' +
      '<div class="chip-sub">Coincidencia con tus síntomas</div></div></div></div>'
    ).join('');
  } catch (err) {
    toast(err.message);
  }
}

/* ======================= SUB-VISTAS DE LA APP ======================= */
function mostrarSub(nombre) {
  ['home', 'cita', 'citas', 'receta'].forEach(s => {
    document.getElementById('sub-' + s).style.display = (s === nombre) ? 'block' : 'none';
  });
  document.querySelectorAll('#bottomnav button').forEach(b => b.classList.remove('active'));
  const target = nombre === 'receta' ? 'citas' : nombre;
  const btn = document.querySelector('#bottomnav button[data-target="' + target + '"]');
  if (btn) btn.classList.add('active');
  if (nombre === 'home') renderHome();
  if (nombre === 'citas') renderCitas();
  window.scrollTo(0, 0);
}

/* Citas (microservicio citas) + recetas (microservicio recetas) del paciente */
let cargaActual = 0;
async function cargarCitasYRecetas() {
  const id = state.paciente.id;
  const turno = ++cargaActual;
  const [citas, recetas] = await Promise.all([
    Servicios.citas.dePaciente(id),
    Servicios.recetas.dePaciente(id),
  ]);
  // Si mientras tanto empezó otra carga, se descarta esta respuesta (ya es vieja).
  if (turno !== cargaActual) return;
  state.citas = citas;
  state.recetasPorCita = {};
  recetas.forEach(r => { state.recetasPorCita[r.cita_id] = r; });
}

async function renderHome() {
  const box = document.getElementById('proximaCitaBox');
  try {
    await cargarCitasYRecetas();
  } catch (e) {
    box.innerHTML = '<div class="empty"><div class="icon">⚠️</div>' + esc(e.message) + '</div>';
    return;
  }
  const hoy = fechaLocalISO(new Date());
  const prox = state.citas
    .filter(c => c.estado === 'Confirmada' && c.fecha >= hoy)
    .sort((a, b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora))[0];
  box.innerHTML = prox ? renderCitaCard(prox)
    : '<div class="empty"><div class="icon">📭</div>No tienes citas próximas.</div>';
}

/* ======================= WIZARD DE CITA ======================= */
function irAAgendar() {
  state.wizard = { especialidad: null, medico: null, dia: null, hora: null, _dias: [] };
  document.getElementById('citaSintomas').value = '';
  document.getElementById('top3Box').innerHTML = '';
  document.getElementById('top3Helper').style.display = 'none';
  document.getElementById('btnPaso1').disabled = true;
  document.getElementById('selEspecialidadDirecta').innerHTML =
    '<option value="">Selecciona una especialidad...</option>' +
    state.especialidades.map(e => '<option value="' + esc(e.id) + '">' + esc(e.icono) + ' ' + esc(e.nombre) + '</option>').join('');
  irPaso(1);
  mostrarSub('cita');
}

function irPaso(n) {
  for (let i = 1; i <= 4; i++) {
    document.getElementById('wizStep' + i).style.display = (i === n) ? 'block' : 'none';
  }
  document.querySelectorAll('.step').forEach(s => {
    const num = parseInt(s.dataset.step);
    s.classList.toggle('active', num === n);
    s.classList.toggle('done', num < n);
  });
  if (n === 2) renderDoctores();
  if (n === 3) renderDiasHoras();
  if (n === 4) renderResumen();
}

function elegirEspecialidad(id) {
  state.wizard.especialidad = id;
  document.querySelectorAll('.chip-card').forEach(c => c.classList.remove('selected'));
  const el = document.getElementById('chip-' + id); if (el) el.classList.add('selected');
  document.getElementById('selEspecialidadDirecta').value = id;
  document.getElementById('btnPaso1').disabled = false;
}
function elegirEspecialidadDirecta() {
  const id = document.getElementById('selEspecialidadDirecta').value;
  if (!id) { document.getElementById('btnPaso1').disabled = true; return; }
  elegirEspecialidad(id);
}

async function renderDoctores() {
  const e = especialidadPorId(state.wizard.especialidad);
  document.getElementById('espElegidaLbl').textContent = e.icono + ' ' + e.nombre;
  document.getElementById('btnPaso2').disabled = true;
  const list = document.getElementById('doctorList');
  list.innerHTML = '<p class="helper">Cargando médicos...</p>';
  try {
    state.medicos = await Servicios.medicos.porEspecialidad(e.id);
  } catch (err) {
    list.innerHTML = '<p class="helper">' + esc(err.message) + '</p>';
    return;
  }
  list.innerHTML = state.medicos.map((m, idx) =>
    '<div class="doctor-card" id="doc-' + idx + '" onclick="elegirDoctor(' + idx + ')">' +
    '<div class="doctor-avatar">' + esc(iniciales(m.nombre)) + '</div>' +
    '<div><div class="doctor-name">' + esc(m.nombre) + '</div>' +
    '<div class="doctor-meta">' + esc(m.experiencia) + ' de experiencia · <span class="stars">★ ' + m.rating + '</span></div></div></div>'
  ).join('') || '<p class="helper">No hay médicos disponibles para esta especialidad en este momento.</p>';
}
function elegirDoctor(idx) {
  state.wizard.medico = state.medicos[idx];
  document.querySelectorAll('.doctor-card').forEach(c => c.classList.remove('selected'));
  document.getElementById('doc-' + idx).classList.add('selected');
  document.getElementById('btnPaso2').disabled = false;
}

function renderDiasHoras() {
  document.getElementById('medElegidoLbl').textContent = state.wizard.medico.nombre;
  const dias = proximosDias(6);
  document.getElementById('dayTabs').innerHTML = dias.map((d, idx) =>
    '<div class="day-tab" id="day-' + idx + '" onclick="elegirDia(' + idx + ')">' +
    '<span>' + d.dow + '</span><span class="d">' + d.num + '</span></div>'
  ).join('');
  document.getElementById('hourChips').innerHTML = '';
  state.wizard._dias = dias;
  state.wizard.dia = null;
  state.wizard.hora = null;
  document.getElementById('btnPaso3').disabled = true;
}

async function elegirDia(idx) {
  state.wizard.dia = state.wizard._dias[idx];
  state.wizard.hora = null;
  document.querySelectorAll('.day-tab').forEach(d => d.classList.remove('selected'));
  document.getElementById('day-' + idx).classList.add('selected');
  document.getElementById('btnPaso3').disabled = true;
  const box = document.getElementById('hourChips');
  box.innerHTML = '<p class="helper">Consultando disponibilidad...</p>';
  try {
    const horas = await Servicios.citas.disponibilidad(state.wizard.medico.id, state.wizard.dia.iso);
    box.innerHTML = horas.map(h => h.disponible
      ? '<div class="hour-chip" onclick="elegirHora(\'' + esc(h.hora) + '\', this)">' + esc(h.hora) + '</div>'
      : '<div class="hour-chip taken">' + esc(h.hora) + '</div>'
    ).join('');
  } catch (e) {
    box.innerHTML = '<p class="helper">' + esc(e.message) + '</p>';
  }
}
function elegirHora(h, el) {
  state.wizard.hora = h;
  document.querySelectorAll('.hour-chip').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('btnPaso3').disabled = false;
}

function renderResumen() {
  const e = especialidadPorId(state.wizard.especialidad);
  const w = state.wizard;
  document.getElementById('resumenCitaBox').innerHTML =
    '<h3 style="margin-top:0">Resumen de tu cita</h3>' +
    '<p><strong>Especialidad:</strong> ' + esc(e.icono) + ' ' + esc(e.nombre) + '</p>' +
    '<p><strong>Médico:</strong> ' + esc(w.medico.nombre) + '</p>' +
    '<p><strong>Fecha:</strong> ' + esc(w.dia.label) + ' (' + esc(w.dia.dow) + ')</p>' +
    '<p><strong>Hora:</strong> ' + esc(w.hora) + '</p>' +
    '<p style="color:var(--muted); font-size:13px; margin-top:14px">Recibirás un enlace de videollamada 10 minutos antes de tu cita.</p>';
}

async function confirmarCita() {
  const w = state.wizard;
  try {
    await Servicios.citas.crear({
      paciente_id: state.paciente.id,
      medico_id: w.medico.id,
      fecha: w.dia.iso,
      hora: w.hora,
    });
    toast('Cita confirmada con éxito ✅');
    mostrarSub('citas');
  } catch (e) {
    toast(e.message);
  }
}

/* ======================= MIS CITAS Y RECETAS ======================= */
function renderCitaCard(c) {
  const e = especialidadPorId(c.especialidad_id);
  const badgeClass = c.estado === 'Confirmada' ? 'badge-info' : c.estado === 'Completada' ? 'badge-ok' : 'badge-warn';
  let actions = '';
  if (c.estado === 'Completada' && state.recetasPorCita[c.id]) {
    actions = '<div class="appt-actions"><button class="btn btn-secondary btn-sm" onclick="verReceta(' + c.id + ')">Ver receta</button></div>';
  } else if (c.estado === 'Confirmada') {
    actions = '<div class="appt-actions"><button class="btn btn-secondary btn-sm" onclick="cancelarCita(' + c.id + ')">Cancelar</button></div>';
  }
  return '<div class="appt-card"><div class="appt-top">' +
    '<div><div class="appt-date">' + esc(e.icono) + ' ' + esc(e.nombre) + '</div>' +
    '<div class="appt-doc">' + esc(c.medico_nombre) + ' · ' + esc(c.fecha) + ' · ' + esc(c.hora) + '</div></div>' +
    '<span class="badge ' + badgeClass + '">' + esc(c.estado) + '</span></div>' + actions + '</div>';
}

async function renderCitas() {
  const list = document.getElementById('citasList');
  try {
    await cargarCitasYRecetas();
  } catch (e) {
    list.innerHTML = '<div class="empty"><div class="icon">⚠️</div>' + esc(e.message) + '</div>';
    return;
  }
  list.innerHTML = state.citas.length
    ? state.citas.map(renderCitaCard).join('')
    : '<div class="empty"><div class="icon">📭</div>Aún no tienes citas registradas.</div>';
}

async function cancelarCita(id) {
  try {
    await Servicios.citas.cancelar(id);
    toast('Cita cancelada');
    await renderCitas();
  } catch (e) {
    toast(e.message);
  }
}

function verReceta(citaId) {
  const c = state.citas.find(x => x.id === citaId);
  const r = state.recetasPorCita[citaId];
  if (!c || !r) { toast('No se encontró la receta'); return; }
  const e = especialidadPorId(c.especialidad_id);
  document.getElementById('recetaBox').innerHTML = '<div class="card">' +
    '<p class="page-sub" style="margin-top:0">' + esc(e.icono) + ' ' + esc(e.nombre) + ' · ' + esc(r.medico_nombre) + ' · ' + esc(r.fecha) + '</p>' +
    '<h3 style="margin-top:0">Indicaciones</h3><p>' + esc(r.indicaciones) + '</p>' +
    '<h3>Medicamentos recetados</h3>' +
    r.items.map(m => '<div class="rx-item"><span class="rx-name">' + esc(m.medicamento) + '</span><span class="rx-dose">' + esc(m.dosis) + '</span></div>').join('') +
    '</div>';
  mostrarSub('receta');
}

/* ======================= INICIO ======================= */
(async function init() {
  try {
    state.especialidades = await Servicios.medicos.especialidades();
  } catch (e) {
    toast('No se pudo cargar el catálogo de especialidades');
  }
  const paciente = leerSesion();
  if (paciente) entrar(paciente);
  renderTopbar();
})();
