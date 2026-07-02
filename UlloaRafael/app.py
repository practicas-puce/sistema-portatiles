import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# Configuración de la conexión a PostgreSQL
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(db_url)

# Ruta principal para servir el formulario HTML
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

# =========================================================================
# ENDPOINTS DE LA API (UNIVERSIDAD)
# =========================================================================

# Obtener carreras filtradas por escuela
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
        if conn:
            conn.close()

# =========================================================================
# ENDPOINTS DE LA API (USUARIOS)
# =========================================================================

# Registrar un nuevo usuario en la Base de Datos
@app.route('/api/usuarios', methods=['POST'])
def add_usuario():
    datos = request.get_json()
    
    tipo_id = datos.get('tipo_id')
    numero_id = datos.get('numero_id')
    nombre_completo = datos.get('nombre_completo')
    celular = datos.get('celular')
    correo = datos.get('correo')
    carrera_id = datos.get('carrera_id')

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query_text = """
            INSERT INTO usuarios (tipo_id, numero_id, nombre_completo, celular, correo, carrera_id)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
        """
        values = (tipo_id, numero_id, nombre_completo, celular, correo, carrera_id)
        
        cur.execute(query_text, values)
        nuevo_id = cur.fetchone()[0]
        conn.commit() # Guarda los cambios en la BDD
        cur.close()
        
        return jsonify({"message": "Usuario registrado con éxito", "id": nuevo_id}), 201
        
    except psycopg2.Error as err:
        if conn:
            conn.rollback() # Revierte la transacción si hubo error
        if err.pgcode == '23505':
            return jsonify({"error": "La identificación o el correo ya se encuentran registrados."}), 400
        else:
            return jsonify({"error": "Error de base de datos al registrar."}), 500
    except Exception as e:
        return jsonify({"error": "Error interno del servidor."}), 500
    finally:
        if conn:
            conn.close()

# Endpoint API: Buscar usuario por número de identificación
@app.route('/api/usuarios/buscar', methods=['GET'])
def buscar_usuario():
    numero_id = request.args.get('numero_id')
    if not numero_id:
        return jsonify({"error": "Debe proporcionar un número de identificación."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Hacemos un JOIN con la tabla carreras para devolver el nombre de la carrera y no solo el ID numérico
        query = """
            SELECT u.tipo_id, u.numero_id, u.nombre_completo, u.celular, u.correo, c.nombre AS carrera
            FROM usuarios u
            INNER JOIN carreras c ON u.carrera_id = c.id
            WHERE u.numero_id = %s;
        """
        cur.execute(query, (numero_id,))
        usuario = cur.fetchone()
        cur.close()

        if usuario:
            return jsonify(usuario), 200
        else:
            return jsonify({"error": "No se encontró ningún usuario con esa identificación."}), 404

    except Exception as e:
        return jsonify({"error": f"Error interno en el servidor: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Ejecuta el servidor en modo desarrollo en el puerto 5000
    app.run(debug=True, host='0.0.0.0' ,port=5000)