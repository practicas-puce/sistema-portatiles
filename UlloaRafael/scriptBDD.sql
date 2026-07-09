-- =========================================================================
-- 1. ENUMS Y EXTENSIONES (Restricciones de catálogo cerrado sin tildes)
-- =========================================================================
CREATE TYPE tipo_identificacion AS ENUM ('cedula', 'pasaporte');
CREATE TYPE rol_usuario AS ENUM ('comun', 'administrador');
CREATE TYPE estado_articulo AS ENUM ('disponible', 'prestado', 'mantenimiento');
CREATE TYPE estado_prestamo AS ENUM ('activo', 'devuelto');

-- =========================================================================
-- 2. TABLAS PRINCIPALES
-- =========================================================================

-- Tabla de Carreras
CREATE TABLE carreras (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Tabla de Usuarios (Con Roles, Borrado Lógico e índice INSENSIBLE a mayúsculas)
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    tipo_id tipo_identificacion NOT NULL,
    numero_id VARCHAR(20) NOT NULL UNIQUE,
    nombre_completo VARCHAR(150) NOT NULL,
    celular VARCHAR(15) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    rol rol_usuario DEFAULT 'comun' NOT NULL,
    activo BOOLEAN DEFAULT TRUE NOT NULL, -- Borrado lógico
    creado_en TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índice único en minúsculas para el correo (Evita Duplicados Aparentes)
CREATE UNIQUE INDEX idx_usuarios_correo_lower ON usuarios (LOWER(correo));

-- Tabla de Artículos (Con Identificación Física Única y Borrado Lógico)
CREATE TABLE articulos (
    id SERIAL PRIMARY KEY,
    codigo_activo VARCHAR(50) NOT NULL UNIQUE, -- Identificador físico (Código de barra / Serie)
    modelo VARCHAR(100) NOT NULL,              
    tipo_articulo VARCHAR(50) NOT NULL,        
    estado estado_articulo DEFAULT 'disponible' NOT NULL, -- Catálogo cerrado
    activo BOOLEAN DEFAULT TRUE NOT NULL,      -- Borrado lógico
    creado_en TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Tabla de Préstamos (Con doble referencia a usuarios, fechas comprometidas y reglas de coherencia)
CREATE TABLE prestamos (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,               -- El solicitante
    administrador_id INT NOT NULL,         -- El admin que gestiona [Ambas partes]
    articulo_id INT NOT NULL,              
    fecha_prestamo TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_devolucion_prevista TIMESTAMPTZ NOT NULL, -- Obligatoria para calcular retrasos
    fecha_devolucion_real TIMESTAMPTZ,              -- NULL si sigue activo
    observaciones TEXT,
    estado_op estado_prestamo DEFAULT 'activo' NOT NULL, -- Catálogo cerrado
    
    -- Llaves Foráneas
    CONSTRAINT fk_usuario_prestamo FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_admin_prestamo FOREIGN KEY (administrador_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_articulo_prestamo FOREIGN KEY (articulo_id) REFERENCES articulos(id) ON DELETE RESTRICT,
    
    -- Regla de Coherencia: Si está devuelto, exige fecha real y viceversa
    CONSTRAINT chk_coherencia_devolucion CHECK (
        (estado_op = 'devuelto' AND fecha_devolucion_real IS NOT NULL) OR 
        (estado_op = 'activo' AND fecha_devolucion_real IS NULL)
    )
);

-- =========================================================================
-- 3. ÍNDICES (Optimización de Llaves Foráneas y Reportes por Período)
-- =========================================================================
CREATE INDEX idx_usuarios_carrera_id ON usuarios(carrera_id) WHERE carrera_id IS NOT NULL; -- (Asegúrate de mapear carrera_id si la usas en usuarios)
CREATE INDEX idx_prestamos_usuario ON prestamos(usuario_id);
CREATE INDEX idx_prestamos_admin ON prestamos(administrador_id);
CREATE INDEX idx_prestamos_articulo ON prestamos(articulo_id);
CREATE INDEX idx_prestamos_fecha_prestamo ON prestamos(fecha_prestamo);

-- Alteración rápida para amarrar la carrera a usuarios que faltaba en el script base:
ALTER TABLE usuarios ADD COLUMN carrera_id INT REFERENCES carreras(id) ON DELETE RESTRICT;
CREATE INDEX idx_usuarios_carrera ON usuarios(carrera_id);

-- =========================================================================
-- 4. VISTAS (Datos derivables para evitar desincronización de Stock y Estados)
-- =========================================================================

-- Vista de Disponibilidad Real de Stock agrupado por Modelo
CREATE VIEW vista_disponibilidad_stock AS
SELECT 
    tipo_articulo,
    modelo,
    COUNT(*) FILTER (WHERE estado = 'disponible' AND activo = TRUE) AS unidades_disponibles,
    COUNT(*) FILTER (WHERE estado = 'prestado' AND activo = TRUE) AS unidades_prestadas,
    COUNT(*) AS total_inventario
FROM articulos
WHERE activo = TRUE
GROUP BY tipo_articulo, modelo;

-- Vista de Préstamos con cálculo dinámico de Atraso (Sin almacenar estado duplicado)
CREATE VIEW vista_prestamos_detallada AS
SELECT 
    p.id AS prestamo_id,
    u.nombre_completo AS solicitante,
    a.modelo AS equipo,
    a.codigo_activo,
    p.fecha_prestamo,
    p.fecha_devolucion_prevista,
    p.fecha_devolucion_real,
    p.estado_op,
    CASE 
        WHEN p.estado_op = 'activo' AND CURRENT_TIMESTAMP > p.fecha_devolucion_prevista THEN TRUE
        ELSE FALSE
    END AS atrasado
FROM prestamos p
INNER JOIN usuarios u ON p.usuario_id = u.id
INNER JOIN articulos a ON p.articulo_id = a.id;

-- =========================================================================
-- 5. AUDITORÍA GENÉRICA (Tabla de Logs + Trigger en PL/pgSQL para Reportes)
-- =========================================================================

CREATE TABLE auditoria_prestamos (
    id SERIAL PRIMARY KEY,
    prestamo_id INT NOT NULL,
    operacion VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    usuario_bd VARCHAR(50) DEFAULT CURRENT_USER,
    fecha_movimiento TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índice para optimizar reportes por rangos de fecha ("todos los movimientos del mes")
CREATE INDEX idx_auditoria_fecha ON auditoria_prestamos(fecha_movimiento);

-- Función del Trigger
CREATE OR REPLACE FUNCTION tg_auditar_prestamos()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO auditoria_prestamos (prestamo_id, operacion, datos_nuevos)
        VALUES (NEW.id, TG_OP, to_jsonb(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO auditoria_prestamos (prestamo_id, operacion, datos_anteriores, datos_nuevos)
        VALUES (NEW.id, TG_OP, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO auditoria_prestamos (prestamo_id, operacion, datos_anteriores)
        VALUES (OLD.id, TG_OP, to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Vinculación del Trigger a la tabla prestamos
CREATE TRIGGER trg_auditoria_prestamos
AFTER INSERT OR UPDATE OR DELETE ON prestamos
FOR EACH ROW
EXECUTE FUNCTION tg_auditar_prestamos();

-- =========================================================================
-- 6. DATA INICIAL DE PRUEBA
-- =========================================================================
INSERT INTO carreras (nombre) VALUES ('Desarrollo de Software'), ('Ciencia de Datos');
INSERT INTO usuarios (tipo_id, numero_id, nombre_completo, celular, correo, rol, carrera_id) VALUES 
('cedula', '1711111111', 'Admin Principal LTIC', '0999999991', 'admin.ltic@puce.edu.ec', 'administrador', NULL),
('cedula', '1722222222', 'Juan Perez Alumno', '0999999992', 'juan.perez@puce.edu.ec', 'comun', 1);

INSERT INTO articulos (codigo_activo, modelo, tipo_articulo) VALUES 
('LP-001', 'ASUS TUF A15', 'Laptop'),
('LP-002', 'Dell Latitude 3420', 'Laptop');