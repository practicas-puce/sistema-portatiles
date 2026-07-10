// ─── DATOS INICIALES ───────────────────────────────────────
var inventario = [
  { codigo:'LAP-001', nombre:'Laptop HP 14', categoria:'Tecnología', cantidad:5, prestados:2 },
  { codigo:'PRO-001', nombre:'Proyector Epson', categoria:'Audiovisual', cantidad:3, prestados:1 },
  { codigo:'CAL-001', nombre:'Calculadora Científica', categoria:'Laboratorio', cantidad:10, prestados:4 },
  { codigo:'TRI-001', nombre:'Trípode Fotográfico', categoria:'Audiovisual', cantidad:4, prestados:0 },
  { codigo:'LIB-001', nombre:'Microscopio Binocular', categoria:'Laboratorio', cantidad:6, prestados:2 },
  { codigo:'CAM-001', nombre:'Cámara Canon EOS', categoria:'Audiovisual', cantidad:2, prestados:1 },
];

var prestamos = [
  { id:'P-001', estudiante:'Ana Martínez', cedula:'0912345678', carrera:'Comunicación', correo:'a.martinez@uni.edu', articulo:'Proyector Epson', codigoArticulo:'PRO-001', fechaPrestamo:'2026-05-28', fechaDevolucion:'2026-06-10', estado:'activo', obs:'' },
  { id:'P-002', estudiante:'Carlos Vega', cedula:'1712345678', carrera:'Sistemas', correo:'c.vega@uni.edu', articulo:'Laptop HP 14', codigoArticulo:'LAP-001', fechaPrestamo:'2026-06-01', fechaDevolucion:'2026-06-15', estado:'activo', obs:'Batería al 80%' },
  { id:'P-003', estudiante:'Lucía Torres', cedula:'0756789012', carrera:'Medicina', correo:'l.torres@uni.edu', articulo:'Microscopio Binocular', codigoArticulo:'LIB-001', fechaPrestamo:'2026-05-20', fechaDevolucion:'2026-06-03', estado:'vencido', obs:'' },
  { id:'P-004', estudiante:'Diego Ramírez', cedula:'1756789012', carrera:'Arquitectura', correo:'d.ramirez@uni.edu', articulo:'Cámara Canon EOS', codigoArticulo:'CAM-001', fechaPrestamo:'2026-05-10', fechaDevolucion:'2026-05-25', estado:'devuelto', obs:'Devuelto en buen estado' },
  { id:'P-005', estudiante:'Sofía León', cedula:'0812345678', carrera:'Ingeniería Civil', correo:'s.leon@uni.edu', articulo:'Calculadora Científica', codigoArticulo:'CAL-001', fechaPrestamo:'2026-06-05', fechaDevolucion:'2026-06-20', estado:'activo', obs:'' },
];

var contadorId = 6;

(function() {
  var d = new Date();
  var opts = { weekday:'long', year:'numeric', month:'long', day:'numeric' };
  document.getElementById('headerDate').textContent = d.toLocaleDateString('es-ES', opts);
})();

function switchTab(tab) {
  document.querySelectorAll('.panel').forEach(function(p){ p.classList.remove('active'); });
  document.querySelectorAll('.tab-btn').forEach(function(b){ b.classList.remove('active'); });
  document.getElementById('panel-'+tab).classList.add('active');
  var btns = document.querySelectorAll('.tab-btn');
  var map = { prestamos:0, nuevo:1, devolucion:2, inventario:3 };
  btns[map[tab]].classList.add('active');
  if(tab==='prestamos') renderPrestamos();
  if(tab==='devolucion') renderDevolucion('');
  if(tab==='inventario') renderInventario();
  if(tab==='nuevo') llenarSelectArticulos();
}

function renderStats() {
  var activos = prestamos.filter(function(p){ return p.estado==='activo'; }).length;
  var vencidos = prestamos.filter(function(p){ return p.estado==='vencido'; }).length;
  var devueltos = prestamos.filter(function(p){ return p.estado==='devuelto'; }).length;
  var total = prestamos.length;
  var html = [
    '<div class="stat-card"><span class="stat-icon">📋</span><div><div class="stat-num">'+total+'<\/div><div class="stat-label">Total Préstamos<\/div><\/div><\/div>',
    '<div class="stat-card blue"><span class="stat-icon">🔵</span><div><div class="stat-num">'+activos+'<\/div><div class="stat-label">Activos<\/div><\/div><\/div>',
    '<div class="stat-card red"><span class="stat-icon">⚠️</span><div><div class="stat-num">'+vencidos+'<\/div><div class="stat-label">Vencidos<\/div><\/div><\/div>',
    '<div class="stat-card green"><span class="stat-icon">✅</span><div><div class="stat-num">'+devueltos+'<\/div><div class="stat-label">Devueltos<\/div><\/div><\/div>',
  ].join('');
  document.getElementById('statsGrid').innerHTML = html;
}

function badge(estado) {
  var map = {
    activo: '<span class="badge badge-active">● Activo</span>',
    devuelto: '<span class="badge badge-returned">✓ Devuelto</span>',
    vencido: '<span class="badge badge-overdue">⚠ Vencido</span>',
    disponible: '<span class="badge badge-available">● Disponible</span>',
    prestado: '<span class="badge badge-loaned">● Prestado</span>',
  };
  return map[estado] || estado;
}

function renderPrestamos() {
  var q = (document.getElementById('searchPrestamos').value||'').toLowerCase();
  var f = document.getElementById('filterEstado').value;
  var lista = prestamos.filter(function(p) {
    var match = !q || p.estudiante.toLowerCase().indexOf(q)>-1 || p.articulo.toLowerCase().indexOf(q)>-1 || p.id.toLowerCase().indexOf(q)>-1 || p.cedula.indexOf(q)>-1;
    var est = !f || p.estado===f;
    return match && est;
  });
  var tb = document.getElementById('tablaPrestamos');
  var empty = document.getElementById('emptyPrestamos');
  if(!lista.length){ tb.innerHTML=''; empty.style.display='block'; return; }
  empty.style.display='none';
  tb.innerHTML = lista.map(function(p){
    return '<tr>'
      +'<td><strong>'+p.id+'</strong></td>'
      +'<td><strong>'+p.estudiante+'</strong><br><small style="color:var(--gray-text)">'+p.cedula+'</small></td>'
      +'<td>'+p.articulo+'</td>'
      +'<td>'+formatFecha(p.fechaPrestamo)+'</td>'
      +'<td>'+formatFecha(p.fechaDevolucion)+'</td>'
      +'<td>'+badge(p.estado)+'</td>'
      +'<td><button class="btn btn-outline btn-sm" onclick="verDetalle(\''+p.id+'\')">👁 Ver</button></td>'
      +'</tr>';
  }).join('');
}

function formatFecha(f) {
  if(!f) return '—';
  var p = f.split('-');
  return p[2]+'/'+p[1]+'/'+p[0];
}

function verDetalle(id) {
  var p = prestamos.find(function(x){ return x.id===id; });
  if(!p) return;
  document.getElementById('modalDetalleTitulo').textContent = 'Préstamo '+p.id;
  var rows = [
    ['Estudiante', p.estudiante],
    ['Cédula', p.cedula],
    ['Carrera', p.carrera||'—'],
    ['Correo', p.correo||'—'],
    ['Artículo', p.articulo],
    ['Fecha Préstamo', formatFecha(p.fechaPrestamo)],
    ['Fecha Devolución', formatFecha(p.fechaDevolucion)],
    ['Estado', badge(p.estado)],
    ['Observaciones', p.obs||'—'],
  ];
  document.getElementById('modalDetalleContenido').innerHTML = rows.map(function(r){
    return '<div class="modal-row"><span>'+r[0]+'</span><span>'+r[1]+'</span></div>';
  }).join('');
  var acc = '';
  if(p.estado==='activo'||p.estado==='vencido') {
    acc = '<button class="btn btn-gold btn-sm" onclick="devolverDesdeDetalle(\''+p.id+'\')">↩ Registrar Devolución</button>';
  }
  document.getElementById('modalDetalleAcciones').innerHTML = acc;
  document.getElementById('modalDetalle').classList.add('open');
}

function devolverDesdeDetalle(id) {
  cerrarModal('modalDetalle');
  switchTab('devolucion');
  document.getElementById('buscarDevolucion').value = id;
  buscarParaDevolucion();
}

function cerrarModal(id) {
  document.getElementById(id).classList.remove('open');
}

function llenarSelectArticulos() {
  var sel = document.getElementById('nArticulo');
  var disponibles = inventario.filter(function(a){ return a.cantidad - a.prestados > 0; });
  sel.innerHTML = '<option value="">Seleccione un artículo</option>' +
    disponibles.map(function(a){
      return '<option value="'+a.codigo+'">'+a.nombre+' ('+a.codigo+') — '+( a.cantidad - a.prestados )+' disp.</option>';
    }).join('');
  var hoy = new Date();
  var manana = new Date(hoy); manana.setDate(hoy.getDate()+1);
  document.getElementById('nFechaDevolucion').min = manana.toISOString().split('T')[0];
}

function registrarPrestamo() {
  var est = document.getElementById('nEstudiante').value.trim();
  var ced = document.getElementById('nCedula').value.trim();
  var art = document.getElementById('nArticulo').value;
  var fDev = document.getElementById('nFechaDevolucion').value;
  if(!est||!ced||!art||!fDev) { showToast('Por favor, completa todos los campos obligatorios.','error'); return; }
  var artObj = inventario.find(function(a){ return a.codigo===art; });
  if(!artObj || artObj.cantidad - artObj.prestados < 1) { showToast('El artículo no está disponible.','error'); return; }
  var hoy = new Date().toISOString().split('T')[0];
  var id = 'P-'+String(contadorId).padStart(3,'0'); contadorId++;
  prestamos.push({
    id: id,
    estudiante: est,
    cedula: ced,
    carrera: document.getElementById('nCarrera').value.trim(),
    correo: document.getElementById('nCorreo').value.trim(),
    articulo: artObj.nombre,
    codigoArticulo: art,
    fechaPrestamo: hoy,
    fechaDevolucion: fDev,
    estado: 'activo',
    obs: document.getElementById('nObservaciones').value.trim(),
  });
  artObj.prestados++;
  limpiarFormulario();
  renderStats();
  showToast('✅ Préstamo '+id+' registrado correctamente.','success');
  setTimeout(function(){ switchTab('prestamos'); }, 1200);
}

function limpiarFormulario() {
  ['nEstudiante','nCedula','nCarrera','nCorreo','nObservaciones'].forEach(function(id){
    document.getElementById(id).value='';
  });
  document.getElementById('nArticulo').value='';
  document.getElementById('nFechaDevolucion').value='';
}

function buscarParaDevolucion() {
  var q = (document.getElementById('buscarDevolucion').value||'').toLowerCase();
  renderDevolucion(q);
}

function renderDevolucion(q) {
  var lista = prestamos.filter(function(p){
    return (p.estado==='activo'||p.estado==='vencido') &&
      (!q || p.estudiante.toLowerCase().indexOf(q)>-1 || p.cedula.indexOf(q)>-1 || p.id.toLowerCase().indexOf(q)>-1);
  });
  var tb = document.getElementById('tablaDevolucion');
  var empty = document.getElementById('emptyDevolucion');
  if(!lista.length){ tb.innerHTML=''; empty.style.display='block'; return; }
  empty.style.display='none';
  tb.innerHTML = lista.map(function(p){
    return '<tr>'
      +'<td><strong>'+p.id+'</strong></td>'
      +'<td>'+p.estudiante+'<br><small style="color:var(--gray-text)">'+p.cedula+'</small></td>'
      +'<td>'+p.articulo+'</td>'
      +'<td>'+formatFecha(p.fechaDevolucion)+'</td>'
      +'<td>'+badge(p.estado)+'</td>'
      +'<td><button class="btn btn-gold btn-sm" onclick="procesarDevolucion(\''+p.id+'\')">↩ Devolver</button></td>'
      +'</tr>';
  }).join('');
}

function procesarDevolucion(id) {
  var p = prestamos.find(function(x){ return x.id===id; });
  if(!p) return;
  var estadoItem = document.getElementById('estadoDevolucion').value;
  var obs = document.getElementById('obsDevolucion').value.trim();
  p.estado = 'devuelto';
  p.obs = 'Devuelto — '+estadoItem+(obs?': '+obs:'');
  var artObj = inventario.find(function(a){ return a.codigo===p.codigoArticulo; });
  if(artObj && artObj.prestados>0) artObj.prestados--;
  renderStats();
  buscarParaDevolucion();
  showToast('↩️ Devolución de '+p.articulo+' registrada.','success');
}

function renderInventario() {
  var q = (document.getElementById('searchInventario').value||'').toLowerCase();
  var lista = inventario.filter(function(a){
    return !q || a.nombre.toLowerCase().indexOf(q)>-1 || a.codigo.toLowerCase().indexOf(q)>-1 || a.categoria.toLowerCase().indexOf(q)>-1;
  });
  var tb = document.getElementById('tablaInventario');
  tb.innerHTML = lista.map(function(a){
    var disp = a.cantidad - a.prestados;
    var est = disp>0 ? badge('disponible') : badge('prestado');
    return '<tr>'
      +'<td><code>'+a.codigo+'</code></td>'
      +'<td><strong>'+a.nombre+'</strong></td>'
      +'<td>'+a.categoria+'</td>'
      +'<td style="text-align:center">'+a.cantidad+'</td>'
      +'<td style="text-align:center"><strong style="color:'+(disp>0?'var(--success)':'var(--danger)')+'">'+disp+'</strong></td>'
      +'<td>'+est+'</td>'
      +'<td><button class="btn btn-danger btn-sm" onclick="eliminarArticulo(\''+a.codigo+'\')">🗑</button></td>'
      +'</tr>';
  }).join('');
}

function actualizarArticuloInfo() {
  // Placeholder para mantener la referencia desde el HTML.
}

function abrirModalInventario() {
  document.getElementById('invNombre').value='';
  document.getElementById('invCodigo').value='';
  document.getElementById('invCantidad').value='1';
  document.getElementById('modalInventario').classList.add('open');
}

function agregarArticulo() {
  var nombre = document.getElementById('invNombre').value.trim();
  var codigo = document.getElementById('invCodigo').value.trim();
  var cat = document.getElementById('invCategoria').value;
  var cant = parseInt(document.getElementById('invCantidad').value)||1;
  if(!nombre||!codigo){ showToast('Completa nombre y código.','error'); return; }
  if(inventario.find(function(a){ return a.codigo===codigo; })){ showToast('Ya existe un artículo con ese código.','error'); return; }
  inventario.push({ codigo:codigo, nombre:nombre, categoria:cat, cantidad:cant, prestados:0 });
  cerrarModal('modalInventario');
  renderInventario();
  showToast('📦 Artículo "'+nombre+'" agregado.','success');
}

function eliminarArticulo(codigo) {
  var a = inventario.find(function(x){ return x.codigo===codigo; });
  if(a && a.prestados>0){ showToast('No se puede eliminar: tiene préstamos activos.','error'); return; }
  inventario = inventario.filter(function(x){ return x.codigo!==codigo; });
  renderInventario();
  showToast('🗑 Artículo eliminado.','success');
}

function showToast(msg, tipo) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = tipo||'';
  t.classList.add('show');
  setTimeout(function(){ t.classList.remove('show'); }, 3000);
}

document.querySelectorAll('.modal-overlay').forEach(function(overlay){
  overlay.addEventListener('click', function(e){
    if(e.target===overlay) overlay.classList.remove('open');
  });
});

renderStats();
renderPrestamos();
llenarSelectArticulos();
renderInventario();
