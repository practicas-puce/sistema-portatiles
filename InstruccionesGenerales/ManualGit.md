
# 🛠️ Guía de Git (Flujo de Trabajo)

Para mantener una organización adecuada y evitar conflictos de código, sigan el siguiente flujo de trabajo.

## 1. Clonar el repositorio

Si el repositorio está vacío, pueden ignorar el mensaje de advertencia (*warning*).

```bash
git clone https://github.com/practicas-puce/sistema-portatiles.git
cd sistema-portatiles
```

## 2. Crear una rama de trabajo

> ⚠️ Importante: No trabajen directamente sobre la rama `main`.

Cada integrante debe crear una rama propia utilizando su apellido:

```bash
git checkout -b "ApellidoNombre-NombreTarea"
```

## 3. Estructura de carpetas
Cada estudiante deberá crear su propia carpeta:

```text
SuApellido/
```

y colocar dentro de ella todos los archivos o carpetas relacionados con su trabajo (`HTML`, `CSS`, `JS`, imágenes, etc.).

## 4. Registrar cambios (Commit)

Una vez finalizado el diseño, agreguen sus archivos y realicen un commit descriptivo:

```bash
git status
git add [archivos o carpetas modificados]
git commit -m "Descripción válida del trabajo realizado"
```

Ejemplos:

```bash
git commit -m "Creación de propuesta de formulario con Tailwind CSS"
git commit -m "Modificación del SQL de Estudiantes"
```

## 5. Subir la rama a GitHub

La primera vez que publiquen su rama, configuren el repositorio remoto con:

```bash
git push --set-upstream origin NombreDeLaRama
```

## 6. Crear el Pull Request

Una vez que GitHub confirme la subida de la rama:

1. Ingresen al repositorio en GitHub.
2. Seleccionen la opción **Compare & pull request**.
3. Describan brevemente:
   - Framework utilizado.
   - Principales características de la propuesta.
   - Cualquier consideración técnica relevante.
4. Envíen el Pull Request para revisión.
