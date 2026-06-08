# 📋 Requerimiento de Desarrollo: Formulario de Registro de Usuarios

## Contexto del Objetivo

Se requiere desarrollar la interfaz del módulo de **Registro de Usuarios** para el sistema de la universidad. El objetivo es condensar las funcionalidades esenciales del sistema actual (tomando como referencia la captura de pantalla compartida en el grupo de WhatsApp) en una interfaz moderna, limpia y preparada para un entorno de producción.

---

## 🎯 Instrucciones Generales

### 1. Estructura y campos obligatorios

El formulario deberá capturar los siguientes datos y todos los campos deberán contar con validación de obligatoriedad:

#### Datos institucionales
- Carrera (ejemplo: Tecnología en Desarrollo de Software)
- Escuela
- Facultad

#### Identificación
- Tipo de identificación (selector con opciones: Cédula o Pasaporte)
- Número de identificación

#### Datos personales
- Nombre completo
- Número de celular (validación de formato telefónico)
- Correo electrónico (validación de formato de correo institucional o personal)

### 2. Stack tecnológico y diseño
- Pueden utilizar el framework CSS que consideren más adecuado para el proyecto:
  - Tailwind CSS
  - Bootstrap
  - Bulma
  - Otros

## 3. Estructura de carpetas

Para evitar sobrescribir archivos de otros compañeros, cada propuesta debe almacenarse dentro de una carpeta individual.

Ejemplo:

```text
ApellidoNombre/
└── templates/
    └── form.html
```

## 4. Entregable esperado

Cada integrante deberá entregar:

- Su propuesta de formulario funcional.
- Todos los archivos dentro de una carpeta propia.
- Una rama independiente en GitHub.
- Un Pull Request correctamente documentado.

### Criterios de revisión

- Calidad visual del diseño.
- Organización del código.
- Buenas prácticas de desarrollo frontend.