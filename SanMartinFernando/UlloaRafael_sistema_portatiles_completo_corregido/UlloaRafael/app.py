import os
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)


def get_db_connection():
    """Crea una conexión nueva con PostgreSQL usando las variables de .env."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "sistemaportatiles"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "1234"),
        port=os.environ.get("DB_PORT", "5432"),
    )


def json_error(message: str, status: int = 500):
    return jsonify({"error": message}), status


# =========================================================================
# VISTAS HTML
# =========================================================================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/registro")
def registro_page():
    return render_template("form.html")


@app.route("/buscar")
def buscar_page():
    return render_template("buscar.html")


@app.route("/prestamo")
def prestamo_page():
    return render_template("prestamo.html")


@app.route("/devolucion")
def devolucion_page():
    return render_template("devolucion.html")


@app.route("/devolucion/registrar/<int:prestamo_id>")
def registrar_devolucion_page(prestamo_id: int):
    return render_template("registrar_devolucion.html", prestamo_id=prestamo_id)


@app.route("/inventario")
def inventario_page():
    return render_template("inventario.html")


# =========================================================================
# ENDPOINTS GENERALES
# =========================================================================
@app.route("/api/salud", methods=["GET"])
def api_salud():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT current_database() AS base, CURRENT_TIMESTAMP AS fecha;")
            base, fecha = cur.fetchone()
        return jsonify({"estado": "ok", "base_datos": base, "fecha": fecha}), 200
    except Exception as exc:
        return json_error(f"No se pudo conectar con PostgreSQL: {exc}", 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/carreras", methods=["GET"])
def get_carreras():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nombre FROM carreras ORDER BY nombre;")
            carreras = cur.fetchall()
        return jsonify(carreras), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/inventario", methods=["GET"])
def get_inventario():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT tipo_articulo, modelo, unidades_disponibles,
                       unidades_prestadas, total_inventario
                FROM vista_disponibilidad_stock
                ORDER BY tipo_articulo, modelo;
                """
            )
            inventario = cur.fetchall()
        return jsonify({"inventario": inventario}), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/usuarios/lista", methods=["GET"])
def get_usuarios_lista():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, nombre_completo, numero_id, rol
                FROM usuarios
                WHERE activo = TRUE
                ORDER BY nombre_completo;
                """
            )
            usuarios = cur.fetchall()
        return jsonify(usuarios), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/responsables", methods=["GET"])
def get_responsables():
    """Lista únicamente responsables administradores habilitados."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, nombre_completo, numero_id
                FROM usuarios
                WHERE activo = TRUE AND rol = 'administrador'
                ORDER BY nombre_completo;
                """
            )
            responsables = cur.fetchall()
        return jsonify(responsables), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/articulos/disponibles", methods=["GET"])
def get_articulos_disponibles():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, codigo_activo, modelo, tipo_articulo
                FROM articulos
                WHERE estado = 'disponible' AND activo = TRUE
                ORDER BY tipo_articulo, modelo, codigo_activo;
                """
            )
            articulos = cur.fetchall()
        return jsonify(articulos), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


# =========================================================================
# USUARIOS
# =========================================================================
@app.route("/api/usuarios", methods=["POST"])
def add_usuario():
    datos = request.get_json(silent=True) or {}
    obligatorios = [
        "tipo_id",
        "numero_id",
        "nombre_completo",
        "celular",
        "correo",
        "carrera_id",
    ]
    faltantes = [campo for campo in obligatorios if not datos.get(campo)]
    if faltantes:
        return json_error(f"Faltan campos obligatorios: {', '.join(faltantes)}.", 400)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO usuarios
                    (tipo_id, numero_id, nombre_completo, celular, correo, carrera_id, rol)
                VALUES (%s, %s, %s, %s, %s, %s, 'comun')
                RETURNING id;
                """,
                (
                    datos["tipo_id"],
                    str(datos["numero_id"]).strip(),
                    str(datos["nombre_completo"]).strip(),
                    str(datos["celular"]).strip(),
                    str(datos["correo"]).strip(),
                    datos["carrera_id"],
                ),
            )
            nuevo_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({"message": "Usuario registrado con éxito", "id": nuevo_id}), 201
    except psycopg2.Error as exc:
        if conn:
            conn.rollback()
        if exc.pgcode == "23505":
            return json_error("La identificación o el correo ya se encuentran registrados.", 400)
        return json_error(f"Error de base de datos al registrar: {exc}", 500)
    except Exception as exc:
        if conn:
            conn.rollback()
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/usuarios/buscar", methods=["GET"])
def buscar_usuario():
    numero_id = (request.args.get("numero_id") or "").strip()
    nombre = (request.args.get("nombre") or "").strip()
    es_admin_param = request.args.get("es_administrador")

    if not numero_id and not nombre:
        return json_error("Debe proporcionar una identificación o un nombre.", 400)

    rol_filtro = None
    if es_admin_param == "true":
        rol_filtro = "administrador"
    elif es_admin_param == "false":
        rol_filtro = "comun"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            condiciones = ["u.activo = TRUE"]
            parametros: list[Any] = []

            if numero_id:
                condiciones.append("u.numero_id = %s")
                parametros.append(numero_id)
            else:
                condiciones.append("u.nombre_completo ILIKE %s")
                parametros.append(f"%{nombre}%")

            if rol_filtro:
                condiciones.append("u.rol = %s")
                parametros.append(rol_filtro)

            cur.execute(
                f"""
                SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo,
                       u.celular, u.correo, c.nombre AS carrera, u.rol
                FROM usuarios u
                LEFT JOIN carreras c ON u.carrera_id = c.id
                WHERE {' AND '.join(condiciones)}
                ORDER BY u.nombre_completo;
                """,
                parametros,
            )
            resultados = cur.fetchall()

        if numero_id:
            if not resultados:
                return json_error("No se encontró ningún usuario con esa identificación.", 404)
            return jsonify(resultados[0]), 200
        return jsonify(resultados), 200
    except Exception as exc:
        return json_error(f"Error interno en el servidor: {exc}", 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/usuarios/cambiar-rol", methods=["PUT"])
def cambiar_rol():
    datos = request.get_json(silent=True) or {}
    usuario_id = datos.get("usuario_id")
    es_administrador = datos.get("es_administrador")

    if usuario_id is None or es_administrador is None:
        return json_error("Faltan usuario_id y es_administrador.", 400)

    rol = "administrador" if bool(es_administrador) else "comun"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET rol = %s WHERE id = %s AND activo = TRUE;",
                (rol, usuario_id),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return json_error("El usuario no existe o está inactivo.", 404)
        conn.commit()
        return jsonify({"message": f"Rol actualizado a {rol} con éxito."}), 200
    except Exception as exc:
        if conn:
            conn.rollback()
        return json_error(f"Error al actualizar el rol: {exc}", 500)
    finally:
        if conn:
            conn.close()


# =========================================================================
# PRÉSTAMOS
# =========================================================================
@app.route("/api/prestamos", methods=["POST"])
def registrar_prestamo():
    datos = request.get_json(silent=True) or {}
    usuario_id = datos.get("usuario_id")
    administrador_id = datos.get("administrador_id")
    observaciones = str(datos.get("observaciones") or "").strip()
    articulos = datos.get("articulos") or datos.get("articulos_id") or []

    try:
        articulos_id = list(dict.fromkeys(int(valor) for valor in articulos))
    except (TypeError, ValueError):
        return json_error("La lista de artículos no es válida.", 400)

    if not usuario_id or not administrador_id or not articulos_id:
        return json_error("Faltan datos obligatorios o el carrito está vacío.", 400)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id
                FROM usuarios
                WHERE id = %s AND activo = TRUE;
                """,
                (usuario_id,),
            )
            if not cur.fetchone():
                conn.rollback()
                return json_error("El estudiante no existe o está inactivo.", 404)

            cur.execute(
                """
                SELECT id
                FROM usuarios
                WHERE id = %s AND activo = TRUE AND rol = 'administrador';
                """,
                (administrador_id,),
            )
            if not cur.fetchone():
                conn.rollback()
                return json_error("El responsable seleccionado no es administrador.", 400)

            cur.execute(
                """
                SELECT id
                FROM articulos
                WHERE id = ANY(%s) AND activo = TRUE AND estado = 'disponible'
                FOR UPDATE;
                """,
                (articulos_id,),
            )
            disponibles = {fila["id"] for fila in cur.fetchall()}
            if disponibles != set(articulos_id):
                conn.rollback()
                return json_error("Uno o más artículos ya no están disponibles.", 409)

            cur.execute(
                """
                INSERT INTO prestamos (usuario_id, administrador_id, observaciones)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (usuario_id, administrador_id, observaciones),
            )
            nuevo_prestamo_id = cur.fetchone()["id"]

            cur.executemany(
                """
                INSERT INTO detalles_prestamos (prestamo_id, articulo_id)
                VALUES (%s, %s);
                """,
                [(nuevo_prestamo_id, articulo_id) for articulo_id in articulos_id],
            )
            cur.execute(
                "UPDATE articulos SET estado = 'prestado' WHERE id = ANY(%s);",
                (articulos_id,),
            )

        conn.commit()
        return jsonify(
            {
                "message": "Préstamo múltiple procesado con éxito",
                "id": nuevo_prestamo_id,
            }
        ), 201
    except Exception as exc:
        if conn:
            conn.rollback()
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/prestamos/activos", methods=["GET"])
def get_prestamos_activos():
    """Compatibilidad: devuelve préstamos activos, una fila por artículo."""
    numero_id = (request.args.get("numero_id") or "").strip()
    if not numero_id:
        return json_error("Debe proporcionar la identificación del estudiante.", 400)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.id,
                       u.nombre_completo AS estudiante,
                       u.numero_id AS identificacion,
                       admin.nombre_completo AS responsable_prestamo,
                       p.fecha_prestamo,
                       p.fecha_devolucion_prevista,
                       dp.articulo_id,
                       a.modelo,
                       a.tipo_articulo,
                       a.codigo_activo
                FROM prestamos p
                INNER JOIN usuarios u ON p.usuario_id = u.id
                INNER JOIN usuarios admin ON p.administrador_id = admin.id
                INNER JOIN detalles_prestamos dp ON p.id = dp.prestamo_id
                INNER JOIN articulos a ON dp.articulo_id = a.id
                WHERE u.numero_id = %s AND p.estado_op = 'activo'
                ORDER BY p.fecha_prestamo DESC, dp.id;
                """,
                (numero_id,),
            )
            prestamos = cur.fetchall()
        return jsonify(prestamos), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


# =========================================================================
# DEVOLUCIONES
# =========================================================================
@app.route("/api/devoluciones/pendientes", methods=["GET"])
def get_devoluciones_pendientes():
    """Devuelve una fila por préstamo y sus artículos agrupados."""
    numero_id = (request.args.get("numero_id") or "").strip()
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            condiciones = ["p.estado_op = 'activo'"]
            parametros: list[Any] = []
            if numero_id:
                condiciones.append("u.numero_id ILIKE %s")
                parametros.append(f"%{numero_id}%")

            cur.execute(
                f"""
                SELECT p.id,
                       u.nombre_completo AS estudiante,
                       u.numero_id AS identificacion,
                       admin.nombre_completo AS responsable_prestamo,
                       p.fecha_prestamo,
                       p.fecha_devolucion_prevista,
                       JSON_AGG(
                           JSON_BUILD_OBJECT(
                               'id', a.id,
                               'tipo_articulo', a.tipo_articulo,
                               'modelo', a.modelo,
                               'codigo_activo', a.codigo_activo
                           ) ORDER BY dp.id
                       ) AS articulos
                FROM prestamos p
                INNER JOIN usuarios u ON p.usuario_id = u.id
                INNER JOIN usuarios admin ON p.administrador_id = admin.id
                INNER JOIN detalles_prestamos dp ON p.id = dp.prestamo_id
                INNER JOIN articulos a ON dp.articulo_id = a.id
                WHERE {' AND '.join(condiciones)}
                GROUP BY p.id, u.nombre_completo, u.numero_id,
                         admin.nombre_completo, p.fecha_prestamo,
                         p.fecha_devolucion_prevista
                ORDER BY p.fecha_prestamo DESC;
                """,
                parametros,
            )
            prestamos = cur.fetchall()
        return jsonify({"prestamos": prestamos, "total": len(prestamos)}), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/devoluciones/<int:prestamo_id>", methods=["GET"])
def get_devolucion_detalle(prestamo_id: int):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.id,
                       u.nombre_completo AS estudiante,
                       u.numero_id AS identificacion,
                       admin.nombre_completo AS responsable_prestamo,
                       p.fecha_prestamo,
                       p.fecha_devolucion_prevista,
                       p.estado_op,
                       p.observaciones
                FROM prestamos p
                INNER JOIN usuarios u ON p.usuario_id = u.id
                INNER JOIN usuarios admin ON p.administrador_id = admin.id
                WHERE p.id = %s;
                """,
                (prestamo_id,),
            )
            prestamo = cur.fetchone()
            if not prestamo:
                return json_error("El préstamo solicitado no existe.", 404)
            if prestamo["estado_op"] != "activo":
                return json_error("Este préstamo ya fue devuelto.", 409)

            cur.execute(
                """
                SELECT a.id, a.tipo_articulo, a.modelo, a.codigo_activo, a.estado
                FROM detalles_prestamos dp
                INNER JOIN articulos a ON dp.articulo_id = a.id
                WHERE dp.prestamo_id = %s
                ORDER BY dp.id;
                """,
                (prestamo_id,),
            )
            articulos = cur.fetchall()

            cur.execute(
                """
                SELECT id, nombre_completo, numero_id
                FROM usuarios
                WHERE activo = TRUE AND rol = 'administrador'
                ORDER BY nombre_completo;
                """
            )
            responsables = cur.fetchall()

        prestamo["articulos"] = articulos
        prestamo["responsables"] = responsables
        return jsonify(prestamo), 200
    except Exception as exc:
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


def procesar_devolucion(prestamo_id: int, datos: dict[str, Any]):
    responsable_id = datos.get("responsable_id") or datos.get("administrador_id")
    articulos = datos.get("articulos") or datos.get("articulos_id") or []

    try:
        responsable_id = int(responsable_id)
        articulos_id = list(dict.fromkeys(int(valor) for valor in articulos))
    except (TypeError, ValueError):
        return json_error("El responsable o la lista de artículos no son válidos.", 400)

    if not responsable_id or not articulos_id:
        return json_error("Seleccione al responsable y confirme todos los artículos.", 400)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, estado_op FROM prestamos WHERE id = %s FOR UPDATE;",
                (prestamo_id,),
            )
            prestamo = cur.fetchone()
            if not prestamo:
                conn.rollback()
                return json_error("El préstamo no existe.", 404)
            if prestamo["estado_op"] != "activo":
                conn.rollback()
                return json_error("El préstamo ya fue devuelto.", 409)

            cur.execute(
                """
                SELECT id
                FROM usuarios
                WHERE id = %s AND activo = TRUE AND rol = 'administrador';
                """,
                (responsable_id,),
            )
            if not cur.fetchone():
                conn.rollback()
                return json_error("El responsable seleccionado no es válido.", 400)

            cur.execute(
                """
                SELECT dp.articulo_id, a.estado
                FROM detalles_prestamos dp
                INNER JOIN articulos a ON dp.articulo_id = a.id
                WHERE dp.prestamo_id = %s
                ORDER BY dp.id
                FOR UPDATE OF a;
                """,
                (prestamo_id,),
            )
            articulos_prestamo = cur.fetchall()
            esperados = {fila["articulo_id"] for fila in articulos_prestamo}
            confirmados = set(articulos_id)

            if not esperados:
                conn.rollback()
                return json_error("El préstamo no tiene artículos asociados.", 409)
            if confirmados != esperados:
                conn.rollback()
                return json_error(
                    "Debe confirmar todos los artículos del préstamo para registrar la devolución completa.",
                    400,
                )
            if any(fila["estado"] != "prestado" for fila in articulos_prestamo):
                conn.rollback()
                return json_error(
                    "Uno o más artículos no se encuentran en estado prestado. Revise el inventario.",
                    409,
                )

            cur.execute(
                "UPDATE articulos SET estado = 'disponible' WHERE id = ANY(%s);",
                (list(esperados),),
            )
            cur.execute(
                """
                UPDATE prestamos
                SET responsable_devolucion_id = %s,
                    fecha_devolucion_real = CURRENT_TIMESTAMP,
                    estado_op = 'devuelto'
                WHERE id = %s;
                """,
                (responsable_id, prestamo_id),
            )

        conn.commit()
        return jsonify(
            {
                "message": "Devolución registrada correctamente.",
                "prestamo_id": prestamo_id,
                "articulos_recibidos": len(articulos_id),
            }
        ), 200
    except psycopg2.errors.UndefinedColumn:
        if conn:
            conn.rollback()
        return json_error(
            "Falta la columna responsable_devolucion_id. Ejecute migracion_devoluciones.sql en la base sistemaportatiles.",
            500,
        )
    except Exception as exc:
        if conn:
            conn.rollback()
        return json_error(str(exc), 500)
    finally:
        if conn:
            conn.close()


@app.route("/api/devoluciones/<int:prestamo_id>", methods=["PUT"])
def registrar_devolucion_api(prestamo_id: int):
    datos = request.get_json(silent=True) or {}
    return procesar_devolucion(prestamo_id, datos)


@app.route("/api/prestamos/devolver", methods=["PUT"])
def finalizar_prestamo_compatibilidad():
    """Ruta compatible con versiones anteriores del módulo."""
    datos = request.get_json(silent=True) or {}
    prestamo_id = datos.get("prestamo_id")
    if not prestamo_id:
        return json_error("Falta prestamo_id.", 400)
    if "articulos" not in datos and datos.get("articulo_id") is not None:
        datos["articulos"] = [datos["articulo_id"]]
    return procesar_devolucion(int(prestamo_id), datos)


@app.errorhandler(404)
def no_encontrado(_error):
    if request.path.startswith("/api/"):
        return json_error("La ruta solicitada no existe.", 404)
    return render_template("404.html"), 404


@app.errorhandler(405)
def metodo_no_permitido(_error):
    if request.path.startswith("/api/"):
        return json_error("Método HTTP no permitido para esta ruta.", 405)
    return render_template("404.html"), 405


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
