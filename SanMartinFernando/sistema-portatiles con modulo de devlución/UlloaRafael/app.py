import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "sistemaportatiles"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "1234"),
        port=os.environ.get("DB_PORT", "5432")
    )
    return conn

# =========================================================================
# VISTAS HTML
# =========================================================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/registro')
def registro_page():
    return render_template('form.html')

@app.route('/buscar')
def buscar_page():
    return render_template('buscar.html')

@app.route('/prestamo')
def prestamo_page():
    return render_template('prestamo.html')

@app.route('/devolucion')
def devolucion_page():
    return render_template('devolucion.html')

@app.route('/inventario')
def inventario_page():
    return render_template('inventario.html')

# =========================================================================
# ENDPOINTS DE LA API
# =========================================================================

@app.route('/api/carreras', methods=['GET'])
def get_carreras():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, nombre FROM carreras ORDER BY nombre;")
        carreras = cur.fetchall()
        cur.close()
        return jsonify(carreras)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/inventario', methods=['GET'])
def get_inventario():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT tipo_articulo, modelo, unidades_disponibles, unidades_prestadas, total_inventario FROM vista_disponibilidad_stock ORDER BY tipo_articulo, modelo;")
        inventario = cur.fetchall()
        cur.close()
        return jsonify({"inventario": inventario}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/usuarios/lista', methods=['GET'])
def get_usuarios_lista():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, nombre_completo, numero_id, rol FROM usuarios WHERE activo = TRUE ORDER BY nombre_completo;")
        usuarios = cur.fetchall()
        cur.close()
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/articulos/disponibles', methods=['GET'])
def get_articulos_disponibles():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, codigo_activo, modelo, tipo_articulo FROM articulos WHERE estado = 'disponible' AND activo = TRUE ORDER BY tipo_articulo;")
        articulos = cur.fetchall()
        cur.close()
        return jsonify(articulos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/usuarios', methods=['POST'])
def add_usuario():
    datos = request.get_json()
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query_text = """
            INSERT INTO usuarios (tipo_id, numero_id, nombre_completo, celular, correo, carrera_id, rol)
            VALUES (%s, %s, %s, %s, %s, %s, 'comun') RETURNING id;
        """
        cur.execute(query_text, (datos.get('tipo_id'), datos.get('numero_id'), datos.get('nombre_completo'), datos.get('celular'), datos.get('correo'), datos.get('carrera_id')))
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return jsonify({"message": "Usuario registrado con éxito", "id": nuevo_id}), 201
    except psycopg2.Error as err:
        if conn: conn.rollback()
        if err.pgcode == '23505':
            return jsonify({"error": "La identificación o el correo ya se encuentran registrados."}), 400
        return jsonify({"error": "Error de base de datos al registrar."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/usuarios/buscar', methods=['GET'])
def buscar_usuario():
    numero_id = request.args.get('numero_id')
    nombre = request.args.get('nombre')
    es_admin_param = request.args.get('es_administrador')
    
    if not numero_id and not nombre:
        return jsonify({"error": "Debe proporcionar un número de identificación o un nombre."}), 400

    rol_filtro = None
    if es_admin_param == 'true':
        rol_filtro = 'administrador'
    elif es_admin_param == 'false':
        rol_filtro = 'comun'

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if numero_id:
            if rol_filtro:
                query = """
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.numero_id = %s AND u.rol = %s AND u.activo = TRUE;
                """
                cur.execute(query, (numero_id, rol_filtro))
            else:
                query = """
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.numero_id = %s AND u.activo = TRUE;
                """
                cur.execute(query, (numero_id,))
            usuario = cur.fetchone()
            cur.close()
            if usuario:
                return jsonify(usuario), 200
            else:
                return jsonify({"error": "No se encontró ningún usuario con esa identificación."}), 404
        else:
            if rol_filtro:
                query = """
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.nombre_completo ILIKE %s AND u.rol = %s AND u.activo = TRUE
                    ORDER BY u.nombre_completo;
                """
                cur.execute(query, (f"%{nombre}%", rol_filtro))
            else:
                query = """
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.nombre_completo ILIKE %s AND u.activo = TRUE
                    ORDER BY u.nombre_completo;
                """
                cur.execute(query, (f"%{nombre}%",))
            usuarios = cur.fetchall()
            cur.close()
            return jsonify(usuarios), 200

    except Exception as e:
        return jsonify({"error": f"Error interno en el servidor: {str(e)}"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/usuarios/cambiar-rol', methods=['PUT'])
def cambiar_rol():
    datos = request.get_json()
    usuario_id = datos.get('usuario_id')
    es_administrador = datos.get('es_administrador')
    
    if usuario_id is None or es_administrador is None:
        return jsonify({"error": "Faltan campos obligatorios: usuario_id y es_administrador."}), 400
        
    rol = 'administrador' if es_administrador else 'comun'
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE usuarios 
            SET rol = %s 
            WHERE id = %s AND activo = TRUE;
        """, (rol, usuario_id))
        conn.commit()
        cur.close()
        return jsonify({"message": f"Rol de usuario actualizado a {rol} con éxito."}), 200
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": f"Error al actualizar el rol: {str(e)}"}), 500
    finally:
        if conn: conn.close()

@app.route('/api/prestamos', methods=['POST'])
def registrar_prestamo():
    datos = request.get_json()

    usuario_id = datos.get('usuario_id')
    administrador_id = datos.get('administrador_id')
    # SOLUCIÓN: Extraemos observaciones para evitar el NameError
    observaciones = datos.get('observaciones', '').strip()
    
    articulos_id_list = datos.get('articulos') or datos.get('articulos_id')

    print("=== DATOS RECIBIDOS EN BACKEND ===")
    print("usuario_id:", usuario_id)
    print("administrador_id:", administrador_id)
    print("articulos:", articulos_id_list)

    if not all([usuario_id, administrador_id]) or not articulos_id_list:
        return jsonify({"error": "Faltan campos obligatorios para el préstamo o el carrito está vacío."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query_text = """
            INSERT INTO prestamos (usuario_id, administrador_id, observaciones)
            VALUES (%s, %s, %s) RETURNING id;
        """
        cur.execute(query_text, (usuario_id, administrador_id, observaciones))
        nuevo_prestamo_id = cur.fetchone()[0]

        for art_id in articulos_id_list:
            cur.execute("""
                INSERT INTO detalles_prestamos (prestamo_id, articulo_id) 
                VALUES (%s, %s);
            """, (nuevo_prestamo_id, art_id))
            
            cur.execute("UPDATE articulos SET estado = 'prestado' WHERE id = %s;", (art_id,))
        
        conn.commit()
        cur.close()
        return jsonify({"message": "Préstamo múltiple procesado con éxito", "id": nuevo_prestamo_id}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/prestamos/activos', methods=['GET'])
def get_prestamos_activos():
    numero_id = request.args.get('numero_id')
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # ADAPTACIÓN: Ajustado para buscar en la intermedia detalles_prestamos
        query = """
            SELECT p.id, dp.articulo_id, p.fecha_devolucion_prevista, a.modelo, a.tipo_articulo, a.codigo_activo
            FROM prestamos p
            INNER JOIN usuarios u ON p.usuario_id = u.id
            INNER JOIN detalles_prestamos dp ON p.id = dp.prestamo_id
            INNER JOIN articulos a ON dp.articulo_id = a.id
            WHERE u.numero_id = %s AND p.estado_op = 'activo';
        """
        cur.execute(query, (numero_id,))
        prestamos = cur.fetchall()
        cur.close()
        return jsonify(prestamos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/prestamos/devolver', methods=['PUT'])
def finalizar_prestamo():
    datos = request.get_json()
    prestamo_id = datos.get('prestamo_id')
    articulo_id = datos.get('articulo_id')

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Marcar la cabecera del préstamo como devuelta con su regla de coherencia
        cur.execute("""
            UPDATE prestamos 
            SET fecha_devolucion_real = CURRENT_TIMESTAMP, estado_op = 'devuelto' 
            WHERE id = %s;
        """, (prestamo_id,))
        
        # 2. Liberar el estado del artículo individual seleccionado en el carrito
        cur.execute("UPDATE articulos SET estado = 'disponible' WHERE id = %s;", (articulo_id,))
        
        conn.commit()
        cur.close()
        return jsonify({"message": "Devolución procesada con éxito"}), 200
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)