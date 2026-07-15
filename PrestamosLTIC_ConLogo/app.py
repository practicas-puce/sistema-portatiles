import os
from flask import Flask, render_template, request, jsonify, Response, send_file, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import uuid
import openpyxl
from io import BytesIO
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkeyltic2026")

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "sistema-prestamos"),
        user=os.environ.get("DB_USER", "administrador"),
        password=os.environ.get("DB_PASS", "ewq123dsa456cxz!"),
        port=os.environ.get("DB_PORT", "5432")
    )
    return conn

def run_migrations():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS contrasena VARCHAR(255);")
        
        # Generar hash de la contraseña de producción solicitada
        hashed_prod = generate_password_hash('ewq123dsa456cxz!')
        
        # Verificar si ya existe un usuario con identificación o correo 'administrador'
        cur.execute("SELECT id FROM usuarios WHERE correo = 'administrador' OR numero_id = 'administrador';")
        admin_row = cur.fetchone()
        if admin_row:
            cur.execute("""
                UPDATE usuarios 
                SET contrasena = %s, rol = 'administrador', nombre_completo = 'Administrador General', celular = '0999999999'
                WHERE id = %s;
            """, (hashed_prod, admin_row[0]))
        else:
            cur.execute("""
                INSERT INTO usuarios (tipo_id, numero_id, nombre_completo, celular, correo, rol, contrasena)
                VALUES ('cedula', 'administrador', 'Administrador General', '0999999999', 'administrador', 'administrador', %s);
            """, (hashed_prod,))
            
        # Para el resto de administradores sin contraseña (por si acaso), asignamos clave por defecto 'admin123'
        cur.execute("SELECT id FROM usuarios WHERE rol = 'administrador' AND contrasena IS NULL;")
        admin_rows = cur.fetchall()
        if admin_rows:
            hashed_default = generate_password_hash('admin123')
            for row in admin_rows:
                cur.execute("UPDATE usuarios SET contrasena = %s WHERE id = %s;", (hashed_default, row[0]))
        
        conn.commit()
        cur.close()
        print("Migraciones de base de datos completadas exitosamente.")
    except Exception as e:
        print("Error al ejecutar migraciones de base de datos:", e)
    finally:
        if conn: conn.close()

run_migrations()


from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "No autorizado. Inicie sesión."}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    datos = request.get_json()
    identificador = datos.get('username')
    contrasena = datos.get('password')

    if not identificador or not contrasena:
        return jsonify({"error": "Usuario y contraseña son requeridos."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, nombre_completo, contrasena 
            FROM usuarios 
            WHERE (correo = %s OR numero_id = %s) AND rol = 'administrador' AND activo = TRUE;
        """, (identificador, identificador))
        admin = cur.fetchone()
        cur.close()

        if not admin or not check_password_hash(admin['contrasena'], contrasena):
            return jsonify({"error": "Credenciales inválidas o no tiene permisos de administrador."}), 401

        session['admin_id'] = admin['id']
        session['admin_name'] = admin['nombre_completo']
        return jsonify({"message": "Sesión iniciada con éxito."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    return redirect(url_for('login_page'))

@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'db': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'db_error': str(e)}), 500

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
@login_required
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


@app.route('/api/carreras', methods=['POST'])
def add_carrera():
    datos = request.get_json()
    nombre = datos.get('nombre')
    if not nombre or not nombre.strip():
        return jsonify({"error": "El nombre de la carrera es obligatorio."}), 400
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar si ya existe
        cur.execute("SELECT id FROM carreras WHERE LOWER(nombre) = LOWER(%s);", (nombre.strip(),))
        if cur.fetchone():
            cur.close()
            return jsonify({"error": "La carrera ya existe en el sistema."}), 400
            
        cur.execute("INSERT INTO carreras (nombre) VALUES (%s) RETURNING id;", (nombre.strip(),))
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return jsonify({"message": "Carrera agregada con éxito.", "id": nuevo_id, "nombre": nombre.strip()}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/inventario', methods=['GET'])
@login_required
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

@app.route('/api/articulos/todos', methods=['GET'])
@login_required
def get_todos_articulos():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, codigo_activo, modelo, tipo_articulo, estado FROM articulos WHERE activo = TRUE ORDER BY tipo_articulo, modelo, codigo_activo;")
        articulos = cur.fetchall()
        cur.close()
        return jsonify({"articulos": articulos}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/articulos/<int:articulo_id>', methods=['PUT'])
@login_required
def actualizar_articulo(articulo_id):
    datos = request.get_json()
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        modelo = datos.get('modelo')
        tipo_articulo = datos.get('tipo_articulo')
        estado = datos.get('estado')
        codigo_activo = datos.get('codigo_activo')
        
        if not all([modelo, tipo_articulo, estado, codigo_activo]):
            return jsonify({"error": "Faltan campos requeridos."}), 400
        
        cur.execute("""
            UPDATE articulos 
            SET modelo = %s, tipo_articulo = %s, estado = %s, codigo_activo = %s
            WHERE id = %s AND activo = TRUE;
        """, (modelo, tipo_articulo, estado, codigo_activo, articulo_id))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Artículo no encontrado."}), 404
        
        conn.commit()
        cur.close()
        return jsonify({"message": "Artículo actualizado con éxito."}), 200
    except Exception as e:
        if conn: conn.rollback()
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

@app.route('/api/responsables', methods=['GET'])
def get_responsables():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, nombre_completo, numero_id FROM usuarios WHERE rol = 'administrador' AND activo = TRUE ORDER BY nombre_completo;")
        responsables = cur.fetchall()
        cur.close()
        return jsonify(responsables), 200
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


@app.route('/api/articulos', methods=['POST'])
@login_required
def add_articulos():
    datos = request.get_json()
    tipo = datos.get('tipo_articulo')
    modelo = datos.get('modelo')
    codigos = datos.get('codigos')
    cantidad = int(datos.get('cantidad', 0))

    if not tipo or not modelo:
        return jsonify({"error": "Debe proporcionar tipo_articulo y modelo."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        inserted = 0

        if codigos and isinstance(codigos, list):
            # Validar que ninguno de los códigos nuevos exista ya en la base de datos (activos)
            for codigo in codigos:
                cur.execute("SELECT id FROM articulos WHERE codigo_activo = %s AND activo = TRUE;", (codigo,))
                if cur.fetchone():
                    return jsonify({"error": f"El código de activo '{codigo}' ya existe en el inventario."}), 400

            for codigo in codigos:
                cur.execute(
                    "INSERT INTO articulos (codigo_activo, modelo, tipo_articulo, estado, activo) VALUES (%s, %s, %s, %s, TRUE);",
                    (codigo, modelo, tipo, 'disponible')
                )
                inserted += 1
        else:
            if cantidad <= 0:
                return jsonify({"error": "Debe proporcionar una cantidad válida."}), 400
            for i in range(cantidad):
                codigo = f"{modelo}-{uuid.uuid4().hex[:8]}"
                cur.execute(
                    "INSERT INTO articulos (codigo_activo, modelo, tipo_articulo, estado, activo) VALUES (%s, %s, %s, %s, TRUE);",
                    (codigo, modelo, tipo, 'disponible')
                )
                inserted += 1

        conn.commit()
        cur.close()
        return jsonify({"message": f"Se agregaron {inserted} artículos."}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


@app.route('/api/articulos/<int:articulo_id>', methods=['DELETE'])
@login_required
def delete_articulo_individual(articulo_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT estado, activo FROM articulos WHERE id = %s;", (articulo_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Artículo no encontrado."}), 404
            
        estado, activo = row
        if not activo:
            return jsonify({"error": "El artículo ya está dado de baja."}), 400
            
        if estado == 'prestado':
            return jsonify({"error": "No se puede dar de baja un artículo que está prestado actualmente."}), 400
            
        cur.execute("UPDATE articulos SET activo = FALSE WHERE id = %s;", (articulo_id,))
        conn.commit()
        cur.close()
        return jsonify({"message": "Artículo dado de baja de forma lógica."}), 200
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


@app.route('/api/articulos', methods=['DELETE'])
@login_required
def delete_articulos():
    datos = request.get_json()
    tipo = datos.get('tipo_articulo')
    modelo = datos.get('modelo')
    cantidad = int(datos.get('cantidad', 0))

    if not tipo or not modelo or cantidad <= 0:
        return jsonify({"error": "Debe proporcionar tipo_articulo, modelo y cantidad válida."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Realizar borrado lógico de hasta `cantidad` artículos disponibles
        cur.execute(
            """
            UPDATE articulos 
            SET activo = FALSE 
            WHERE id IN (
                SELECT id 
                FROM articulos 
                WHERE tipo_articulo = %s AND modelo = %s AND estado = 'disponible' AND activo = TRUE 
                LIMIT %s
            ) RETURNING id;
            """,
            (tipo, modelo, cantidad)
        )
        deleted = len(cur.fetchall())
        conn.commit()
        cur.close()
        return jsonify({"message": f"Se eliminaron {deleted} artículos de forma lógica."}), 200
    except Exception as e:
        if conn: conn.rollback()
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

@app.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
def actualizar_usuario(usuario_id):
    datos = request.get_json()
    nombre = datos.get('nombre_completo')
    celular = datos.get('celular')
    correo = datos.get('correo')
    carrera_id = datos.get('carrera_id')
    rol = datos.get('rol')

    if not nombre or not celular or not correo:
        return jsonify({"error": "Nombre, celular y correo son campos obligatorios."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Construir la consulta dinámicamente según si se incluye rol
        if rol:
            cur.execute("""
                UPDATE usuarios 
                SET nombre_completo = %s, celular = %s, correo = %s, carrera_id = %s, rol = %s
                WHERE id = %s AND activo = TRUE;
            """, (nombre, celular, correo, carrera_id or None, rol, usuario_id))
        else:
            cur.execute("""
                UPDATE usuarios 
                SET nombre_completo = %s, celular = %s, correo = %s, carrera_id = %s
                WHERE id = %s AND activo = TRUE;
            """, (nombre, celular, correo, carrera_id or None, usuario_id))

        if cur.rowcount == 0:
            return jsonify({"error": "Usuario no encontrado o inactivo."}), 404

        conn.commit()
        cur.close()
        return jsonify({"message": "Datos de usuario actualizados correctamente."}), 200
    except psycopg2.Error as err:
        if conn: conn.rollback()
        if err.pgcode == '23505':
            return jsonify({"error": "La identificación o el correo ya se encuentran registrados."}), 400
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def delete_usuario(usuario_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Validar si tiene préstamos activos
        cur.execute("SELECT COUNT(*) FROM prestamos WHERE usuario_id = %s AND estado_op = 'activo';", (usuario_id,))
        if cur.fetchone()[0] > 0:
            return jsonify({"error": "No se puede dar de baja a un usuario que tiene préstamos activos pendientes."}), 400
        
        cur.execute("UPDATE usuarios SET activo = FALSE WHERE id = %s;", (usuario_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "Usuario no encontrado."}), 404
            
        conn.commit()
        cur.close()
        return jsonify({"message": "Usuario dado de baja correctamente."}), 200
    except Exception as e:
        if conn: conn.rollback()
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
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, u.carrera_id, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.numero_id = %s AND u.rol = %s AND u.activo = TRUE;
                """
                cur.execute(query, (numero_id, rol_filtro))
            else:
                query = """
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, u.carrera_id, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.numero_id = %s AND u.activo = TRUE;
                """
                cur.execute(query, (numero_id,))
            usuario = cur.fetchone()
            if usuario:
                cur_check = conn.cursor()
                cur_check.execute("SELECT COUNT(*) FROM prestamos WHERE usuario_id = %s AND estado_op = 'activo';", (usuario['id'],))
                usuario['tiene_prestamo_activo'] = cur_check.fetchone()[0] > 0
                cur_check.close()
                cur.close()
                return jsonify(usuario), 200
            else:
                cur.close()
                return jsonify({"error": "No se encontró ningún usuario con esa identificación."}), 404
        else:
            if rol_filtro:
                query = """
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, u.carrera_id, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.nombre_completo ILIKE %s AND u.rol = %s AND u.activo = TRUE
                    ORDER BY u.nombre_completo;
                """
                cur.execute(query, (f"%{nombre}%", rol_filtro))
            else:
                query = """
                    SELECT u.id, u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, u.carrera_id, c.nombre AS carrera, u.rol
                    FROM usuarios u
                    LEFT JOIN carreras c ON u.carrera_id = c.id
                    WHERE u.nombre_completo ILIKE %s AND u.activo = TRUE
                    ORDER BY u.nombre_completo;
                """
                cur.execute(query, (f"%{nombre}%",))
            usuarios = cur.fetchall()
            cur_check = conn.cursor()
            for u in usuarios:
                cur_check.execute("SELECT COUNT(*) FROM prestamos WHERE usuario_id = %s AND estado_op = 'activo';", (u['id'],))
                u['tiene_prestamo_activo'] = cur_check.fetchone()[0] > 0
            cur_check.close()
            cur.close()
            return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
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
        # Validar si el estudiante ya tiene un préstamo activo
        cur.execute("SELECT COUNT(*) FROM prestamos WHERE usuario_id = %s AND estado_op = 'activo';", (usuario_id,))
        if cur.fetchone()[0] > 0:
            cur.close()
            return jsonify({"error": "El estudiante ya tiene un préstamo activo en curso. Por favor, añada artículos a su préstamo existente en el módulo de Devoluciones."}), 400

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
        if numero_id:
            query = """
                SELECT p.id, dp.articulo_id, p.fecha_devolucion_prevista, a.modelo, a.tipo_articulo, a.codigo_activo,
                       u.nombre_completo AS estudiante, u.numero_id AS identificacion, p.fecha_prestamo,
                       adm.nombre_completo AS responsable
                FROM prestamos p
                INNER JOIN usuarios u ON p.usuario_id = u.id
                INNER JOIN detalles_prestamos dp ON p.id = dp.prestamo_id
                INNER JOIN articulos a ON dp.articulo_id = a.id
                LEFT JOIN usuarios adm ON p.administrador_id = adm.id
                WHERE (u.numero_id = %s OR u.nombre_completo ILIKE %s) 
                  AND p.estado_op = 'activo' AND a.estado = 'prestado'
                ORDER BY p.fecha_prestamo DESC;
            """
            cur.execute(query, (numero_id, f"%{numero_id}%"))
        else:
            query = """
                SELECT p.id, dp.articulo_id, p.fecha_devolucion_prevista, a.modelo, a.tipo_articulo, a.codigo_activo,
                       u.nombre_completo AS estudiante, u.numero_id AS identificacion, p.fecha_prestamo,
                       adm.nombre_completo AS responsable
                FROM prestamos p
                INNER JOIN usuarios u ON p.usuario_id = u.id
                INNER JOIN detalles_prestamos dp ON p.id = dp.prestamo_id
                INNER JOIN articulos a ON dp.articulo_id = a.id
                LEFT JOIN usuarios adm ON p.administrador_id = adm.id
                WHERE p.estado_op = 'activo' AND a.estado = 'prestado'
                ORDER BY p.fecha_prestamo DESC;
            """
            cur.execute(query)
        prestamos = cur.fetchall()
        cur.close()
        return jsonify(prestamos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/prestamos/<int:prestamo_id>/articulos', methods=['POST'])
def add_articulo_to_prestamo(prestamo_id):
    datos = request.get_json()
    articulo_id = datos.get('articulo_id')
    
    if not articulo_id:
        return jsonify({"error": "Debe proporcionar un ID de artículo."}), 400
        
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Validar préstamo activo
        cur.execute("SELECT estado_op FROM prestamos WHERE id = %s;", (prestamo_id,))
        prestamo_row = cur.fetchone()
        if not prestamo_row:
            return jsonify({"error": "Préstamo no encontrado."}), 404
        if prestamo_row[0] != 'activo':
            return jsonify({"error": "No se pueden añadir artículos a un préstamo que no está activo."}), 400
            
        # Validar artículo disponible
        cur.execute("SELECT estado, activo FROM articulos WHERE id = %s;", (articulo_id,))
        articulo_row = cur.fetchone()
        if not articulo_row:
            return jsonify({"error": "Artículo no encontrado."}), 404
        estado, activo = articulo_row
        if not activo or estado != 'disponible':
            return jsonify({"error": "El artículo no está disponible para préstamo."}), 400
            
        # Insertar detalle y actualizar estado del artículo
        cur.execute("INSERT INTO detalles_prestamos (prestamo_id, articulo_id) VALUES (%s, %s);", (prestamo_id, articulo_id))
        cur.execute("UPDATE articulos SET estado = 'prestado' WHERE id = %s;", (articulo_id,))
        
        conn.commit()
        cur.close()
        return jsonify({"message": "Artículo añadido correctamente al préstamo."}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


@app.route('/api/prestamos/devolver', methods=['PUT'])
def finalizar_prestamo():
    datos = request.get_json()
    prestamo_id = datos.get('prestamo_id')
    responsable_id = datos.get('responsable_id')
    articulos_id = datos.get('articulos_id') or datos.get('articulos')

    if not all([prestamo_id, responsable_id]) or not articulos_id:
        return jsonify({"error": "Faltan campos obligatorios para procesar la devolución."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Liberar el estado de cada artículo seleccionado en el lote de devolución
        for art_id in articulos_id:
            cur.execute("UPDATE articulos SET estado = 'disponible' WHERE id = %s;", (art_id,))
        
        # 2. Verificar si quedan artículos en estado 'prestado' asociados a este préstamo
        cur.execute("""
            SELECT COUNT(*) 
            FROM detalles_prestamos dp
            INNER JOIN articulos a ON dp.articulo_id = a.id
            WHERE dp.prestamo_id = %s AND a.estado = 'prestado';
        """, (prestamo_id,))
        articulos_pendientes = cur.fetchone()[0]
        
        # 3. Solo si no quedan más artículos pendientes en este préstamo, se marca la cabecera como devuelta
        if articulos_pendientes == 0:
            cur.execute("""
                UPDATE prestamos 
                SET fecha_devolucion_real = CURRENT_TIMESTAMP, estado_op = 'devuelto' 
                WHERE id = %s;
            """, (prestamo_id,))
        
        # 4. Obtener el nombre del responsable para responder al frontend
        cur.execute("SELECT nombre_completo FROM usuarios WHERE id = %s;", (responsable_id,))
        responsable_row = cur.fetchone()
        responsable_nombre = responsable_row[0] if responsable_row else "Administrador"
        
        conn.commit()
        cur.close()
        return jsonify({
            "message": "Devolución procesada con éxito",
            "responsable": responsable_nombre
        }), 200
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/prestamos/exportar', methods=['GET'])
def exportar_prestamos():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    query = """
        SELECT p.id, 
               u.nombre_completo AS estudiante, 
               u.numero_id AS identificacion, 
               u.celular AS celular,
               u.correo AS correo,
               adm.nombre_completo AS responsable_prestamo, 
               p.fecha_prestamo, 
               p.fecha_devolucion_real, 
               p.estado_op AS estado,
               STRING_AGG(a.tipo_articulo || ' - ' || a.modelo, ', ') AS articulos
        FROM prestamos p
        INNER JOIN usuarios u ON p.usuario_id = u.id
        LEFT JOIN usuarios adm ON p.administrador_id = adm.id
        INNER JOIN detalles_prestamos dp ON p.id = dp.prestamo_id
        INNER JOIN articulos a ON dp.articulo_id = a.id
        WHERE 1=1
    """
    params = []
    
    if fecha_inicio:
        query += " AND p.fecha_prestamo >= %s"
        params.append(f"{fecha_inicio} 00:00:00")
    if fecha_fin:
        query += " AND p.fecha_prestamo <= %s"
        params.append(f"{fecha_fin} 23:59:59")
        
    query += """
        GROUP BY p.id, u.nombre_completo, u.numero_id, u.celular, u.correo, adm.nombre_completo, p.fecha_prestamo, p.fecha_devolucion_real, p.estado_op
        ORDER BY p.fecha_prestamo DESC;
    """
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, tuple(params))
        filas = cur.fetchall()
        cur.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()
        
    # Crear el libro de Excel y la hoja de trabajo
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Historial Préstamos"
    
    # Cabeceras
    headers = [
        'ID Préstamo', 'Estudiante', 'Identificación', 
        'Celular', 'Correo',
        'Responsable Préstamo', 'Fecha Préstamo', 
        'Fecha Devolución Real', 'Estado', 'Artículos'
    ]
    ws.append(headers)
    
    # Escribir los datos
    for fila in filas:
        f_prestamo = fila['fecha_prestamo'].strftime('%Y-%m-%d %H:%M') if fila['fecha_prestamo'] else ''
        f_devolucion = fila['fecha_devolucion_real'].strftime('%Y-%m-%d %H:%M') if fila['fecha_devolucion_real'] else 'Pendiente'
        ws.append([
            fila['id'],
            fila['estudiante'],
            fila['identificacion'],
            fila['celular'] or 'N/A',
            fila['correo'] or 'N/A',
            fila['responsable_prestamo'] or 'N/A',
            f_prestamo,
            f_devolucion,
            fila['estado'].upper(),
            fila['articulos']
        ])
        
    # Autoajustar el ancho de las columnas
    for col in ws.columns:
        max_len = 0
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)
        
    # Guardar en buffer binario en memoria
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    
    fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(
        file_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"reporte_prestamos_{fecha_archivo}.xlsx"
    )

if __name__ == '__main__':
    print('Iniciando servidor Flask en toda la red local (0.0.0.0:5000)')
    app.run(debug=True, host='0.0.0.0', port=5000)