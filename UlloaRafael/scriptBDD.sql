-- 1. Type personalizado para el Tipo de ID
CREATE TYPE tipo_identificacion AS ENUM ('cédula', 'pasaporte');

-- 2. Tabla de Carreras
CREATE TABLE carreras (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

-- 3. Tabla de Usuarios/Registros
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    tipo_id tipo_identificacion NOT NULL,
    numero_id VARCHAR(20) NOT NULL UNIQUE,
    nombre_completo VARCHAR(150) NOT NULL,
    celular VARCHAR(15) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    carrera_id INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_carrera FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 4. Tabla de Artículos (Inventario) - ¡MOVIDA AQUÍ ARRIBA!
CREATE TABLE articulos (
    id SERIAL PRIMARY KEY,
    modelo VARCHAR(100) NOT NULL,              -- Ej: ASUS TUF, Dell Latitude 3420
    tipo_articulo VARCHAR(50) NOT NULL,        -- Ej: Laptop, Cargador, Mouse
    estado VARCHAR(20) DEFAULT 'disponible',   -- 'disponible', 'prestado', 'mantenimiento'
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabla de Préstamos (Ahora sí encuentra a 'usuarios' y 'articulos' arriba)
CREATE TABLE prestamos (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,                   
    articulo_id INT NOT NULL,                
    fecha_prestamo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_devolucion TIMESTAMP,
    observaciones TEXT,
    estado_prestamo VARCHAR(20) DEFAULT 'activo', -- 'activo' (no devuelto), 'devuelto', 'atrasado'
    
    CONSTRAINT fk_usuario_prestamo FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_articulo_prestamo FOREIGN KEY (articulo_id) REFERENCES articulos(id) ON DELETE RESTRICT
);


INSERT INTO carreras (nombre) 
VALUES ('Desarrollo de Software'), ('Finanzas'), ('Administración de Empresas'), ('Arquitectura'), ('Ciencia de Datos'), ('Derecho');