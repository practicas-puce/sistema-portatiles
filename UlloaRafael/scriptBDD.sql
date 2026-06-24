-- Type personalizado para el Tipo de ID
CREATE TYPE tipo_identificacion AS ENUM ('cédula', 'pasaporte');

-- Facultades
CREATE TABLE facultades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Tabla de Escuelas (Depende de Facultades)
CREATE TABLE escuelas (
    id SERIAL PRIMARY KEY,
    facultad_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    CONSTRAINT fk_facultad FOREIGN KEY (facultad_id) REFERENCES facultades(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla de Carreras (Depende de Escuelas)
CREATE TABLE carreras (
    id SERIAL PRIMARY KEY,
    escuela_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    CONSTRAINT fk_escuela FOREIGN KEY (escuela_id) REFERENCES escuelas(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla de Usuarios/Registros (Depende de Carreras)
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