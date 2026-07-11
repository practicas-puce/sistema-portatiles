# Sistema de préstamos de portátiles LTIC

Aplicación web desarrollada con Flask, PostgreSQL, HTML, JavaScript y Bootstrap.

## Módulos incluidos

- Página principal.
- Registro y consulta de usuarios.
- Cambio de rol de usuario.
- Registro de préstamos con uno o varios artículos.
- Devoluciones completas con certificación del responsable.
- Consulta del inventario.

## Preparación

1. Cree o utilice la base PostgreSQL `sistemaportatiles`.
2. Para una base nueva, ejecute `scriptBDD.sql`.
3. Para una base que ya existía antes del módulo de devoluciones, ejecute `migracion_devoluciones.sql`.
4. Copie `.env.example` como `.env` y coloque su contraseña de PostgreSQL.
5. Instale dependencias:

```powershell
py -m pip install -r requirements.txt
```

6. Inicie el servidor:

```powershell
py app.py
```

7. Abra `http://127.0.0.1:5000`.

## Flujo de devoluciones

La página `/devolucion` presenta horizontalmente los préstamos pendientes. El botón **Registrar devolución** dirige a `/devolucion/registrar/<id>`, donde se selecciona al responsable y se confirma cada artículo. El servidor solo permite completar la operación cuando coinciden todos los artículos asociados al préstamo.
