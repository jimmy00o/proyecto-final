# ---------------------- IMPORTS Y CONFIGURACIÓN BÁSICA ----------------------
from flask import Flask, render_template, request, url_for, redirect, session, flash, Response, make_response
from flask_mysqldb import MySQL
from passlib.hash import pbkdf2_sha256
import csv
import io
from datetime import datetime
import os                           
from werkzeug.utils import secure_filename  

# Crea la aplicación Flask
app = Flask(__name__)

# Clave usada para firmar cookies de sesión y habilitar mensajes flash
app.secret_key = 'appsecretkey'

# Instancia de la extensión MySQL
mysql = MySQL()

# ---------------------- CONFIGURACIÓN DE LA BASE DE DATOS -------------------
app.config['MYSQL_HOST'] = 'bvuffejraclapywdnlay-mysql.services.clever-cloud.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'uk4yl53qg4jhkdff'
app.config['MYSQL_PASSWORD'] = 'pk95eZztVPti1gZwJTVz'
app.config['MYSQL_DB'] = 'bvuffejraclapywdnlay'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql.init_app(app)

# ---------------------- CONFIG SUBIDA FOTO PERFIL ADMIN (NUEVO) ------------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================== RUTAS PÚBLICAS ==============================
@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/accesologin', methods=['GET', 'POST'])
def accesologin():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuario WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        try:
            if user and pbkdf2_sha256.verify(password, user['password']):
                session['logueado'] = True
                session['id'] = user['id']
                session['nombre'] = user.get('nombre', 'Usuario')

                if user['id_rol'] == 1:
                    return redirect(url_for('admin'))
                elif user['id_rol'] == 2:
                    return redirect(url_for('usuario'))
        except:
            pass

        flash('Usuario o contraseña incorrecta', 'danger')
        return render_template('login.html')
    
    return render_template('login.html', mensaje="Credenciales incorrectas")


# ============================== REGISTRO DE USUARIOS ========================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        id_rol = 2

        # 🚨 VALIDACIÓN: Verificar si el correo ya existe
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuario WHERE email=%s", (email,))
        existe = cur.fetchone()

        if existe:
            cur.close()
            flash("El correo ya está registrado, usa otro.", "danger")
            return redirect(url_for('registro'))

        # Encriptación
        password = pbkdf2_sha256.hash(password)

        cur.execute(
            "INSERT INTO usuario (email, nombre, password, id_rol) VALUES (%s, %s, %s, %s)",
            (email, nombre, password, id_rol)
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('inicio'))

    return render_template("registro.html")


# =============================== DEMOS FORMULARIO ===========================
@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    user = {'nombre': '', 'email': '', 'mensaje': ''}
    if request.method == 'GET':
        user['nombre'] = request.args.get('nombre', '')
        user['email'] = request.args.get('email', '')
        user['mensaje'] = request.args.get('mensaje', '')
    return render_template("contacto.html", usuario=user)

@app.route('/contactopost', methods=['GET', 'POST'])
def contactopost():
    user = {'nombre': '', 'email': '', 'mensaje': ''}
    if request.method == 'POST':
        user['nombre'] = request.form.get('nombre', '')
        user['email'] = request.form.get('email', '')
        user['mensaje'] = request.form.get('mensaje', '')
    return render_template("contactopost.html", usuario=user)


# ============================ RUTAS DE AUTENTICACIÓN ========================
@app.route('/login')
def login():
    return render_template("login.html")


# ============================ PANEL ADMIN =====================
@app.route('/admin')
def admin():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS total_usuarios FROM usuario")
    total_usuarios = cur.fetchone()['total_usuarios']

    cur.execute("SELECT COUNT(*) AS total_productos FROM producto")
    total_productos = cur.fetchone()['total_productos']

    cur.execute("SELECT id, nombre, email FROM usuario ORDER BY id DESC LIMIT 5")
    ult_usuarios = cur.fetchall()

    cur.execute("SELECT id, nombre, precio, fecha FROM producto ORDER BY id DESC LIMIT 5")
    ult_productos = cur.fetchall()
    cur.close()

    return render_template(
        "admin.html",
        total_usuarios=total_usuarios,
        total_productos=total_productos,
        ult_usuarios=ult_usuarios,
        ult_productos=ult_productos
    )


@app.route('/usuario')
def usuario():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))
    return render_template("usuario.html")


@app.route('/acercade')
def acercade():
    return render_template("acercade.html")


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))


# ============================== PERFIL ADMIN ===============================
@app.route('/perfil')
def perfil_admin():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_rol, nombre FROM usuario WHERE id=%s", (session.get('id'),))
    me = cur.fetchone()

    if not me or me.get('id_rol') != 1:
        cur.close()
        flash('No tienes permisos', 'danger')
        return redirect(url_for('usuario'))

    cur.execute("SELECT COUNT(*) AS total FROM usuario")
    total_usuarios = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM producto")
    total_productos = cur.fetchone()['total']

    cur.execute("SELECT id, nombre, email FROM usuario ORDER BY id DESC LIMIT 5")
    ult_usuarios = cur.fetchall()

    cur.execute("SELECT id, nombre, precio, fecha FROM producto ORDER BY id DESC LIMIT 5")
    ult_productos = cur.fetchall()
    cur.close()

    return render_template(
        'perfil_admin.html',
        admin_nombre=me.get('nombre', 'Administrador'),
        total_usuarios=total_usuarios,
        total_productos=total_productos,
        ult_usuarios=ult_usuarios,
        ult_productos=ult_productos
    )


# ---------------------- SUBIDA FOTO PERFIL ADMIN ---------------------------
@app.route('/perfil/foto', methods=['POST'])
def subir_foto_perfil():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_rol FROM usuario WHERE id=%s", (session.get('id'),))
    me = cur.fetchone()
    cur.close()

    if not me or me.get('id_rol') != 1:
        flash('No tienes permisos', 'danger')
        return redirect(url_for('perfil_admin'))

    file = request.files.get('avatar')

    if not file or file.filename == '':
        flash('No se seleccionó ningún archivo', 'warning')
        return redirect(url_for('perfil_admin'))

    if not allowed_file(file.filename):
        flash('Formato no permitido', 'warning')
        return redirect(url_for('perfil_admin'))

    avatar_filename = 'admin_avatar.png'
    avatar_folder = os.path.join(app.root_path, 'static', 'img')
    os.makedirs(avatar_folder, exist_ok=True)
    avatar_path = os.path.join(avatar_folder, avatar_filename)

    try:
        file.save(avatar_path)
        flash('Foto actualizada', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')

    return redirect(url_for('perfil_admin'))


# ====================================================================
# ======================= CRUD USUARIOS ===============================
# ====================================================================
@app.route('/usuarios')
def lista_usuarios():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, email, password, id_rol FROM usuario ORDER BY id")
    usuarios = cur.fetchall()
    cur.close()

    return render_template('lista_usuarios.html', usuarios=usuarios)


# ---------------------- CREAR USUARIO (ADMIN) -----------------------------
@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
def crear_usuario():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        id_rol = 2

        if not (nombre and email and password):
            flash('Todos los campos son obligatorios', 'warning')
            return redirect(url_for('crear_usuario'))

        # 🚨 VALIDACIÓN: evitar correos repetidos
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuario WHERE email=%s", (email,))
        existe = cur.fetchone()

        if existe:
            cur.close()
            flash("Ese correo ya existe.", "danger")
            return redirect(url_for('crear_usuario'))

        password = pbkdf2_sha256.hash(password)

        cur.execute(
            "INSERT INTO usuario (nombre, email, password, id_rol) VALUES (%s, %s, %s, %s)",
            (nombre, email, password, id_rol)
        )
        mysql.connection.commit()
        cur.close()

        flash('Usuario creado correctamente', 'success')
        return redirect(url_for('lista_usuarios'))

    usuario = {'id': None, 'nombre': '', 'email': '', 'password': '', 'id_rol': 2}
    return render_template('usuario_form.html', usuario=usuario, modo='crear')


# ==================== EDITAR USUARIO ============================
@app.route('/usuarios/<int:uid>/editar', methods=['GET', 'POST'])
def editar_usuario(uid):
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        cur = mysql.connection.cursor()

        try:
            # No validar correo repetido aquí (solo si quieres lo agrego)
            if password:
                password = pbkdf2_sha256.hash(password)
                cur.execute(
                    "UPDATE usuario SET nombre=%s, email=%s, password=%s WHERE id=%s",
                    (nombre, email, password, uid)
                )
            else:
                cur.execute(
                    "UPDATE usuario SET nombre=%s, email=%s WHERE id=%s",
                    (nombre, email, uid)
                )

            mysql.connection.commit()
            flash('Usuario actualizado correctamente', 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f'No se pudo actualizar: {e}', 'danger')
        finally:
            cur.close()

        return redirect(url_for('lista_usuarios'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, email, password FROM usuario WHERE id=%s", (uid,))
    usuario = cur.fetchone()
    cur.close()

    if not usuario:
        flash('Usuario no encontrado', 'warning')
        return redirect(url_for('lista_usuarios'))

    return render_template('usuario_form.html', usuario=usuario, modo='editar')


# ========================== ELIMINAR USUARIO ==============================
@app.route('/usuarios/<int:uid>/eliminar', methods=['POST'])
def eliminar_usuario(uid):
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM usuario WHERE id=%s", (uid,))
        mysql.connection.commit()
        flash('Usuario eliminado', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al eliminar: {e}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('lista_usuarios'))


# ========================= EXPORTAR USUARIOS ==============================
@app.route('/usuarios/exportar')
def exportar_usuarios():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, email FROM usuario ORDER BY id")
    usuarios = cur.fetchall()
    cur.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nombre', 'Correo'])

    for u in usuarios:
        writer.writerow([u['id'], u['nombre'], u['email']])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=usuarios.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


# ====================================================================
# ========================= PRODUCTOS CRUD ===========================
# ====================================================================
@app.route('/productos/agregar', methods=['GET', 'POST'])
def listar_productos_agregados():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        precio = request.form.get('precio', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha_form = request.form.get('fecha', '').strip()

        if not nombre or not precio or not fecha_form:
            flash('Nombre, precio y fecha son obligatorios', 'warning')
        else:
            cur = mysql.connection.cursor()
            try:
                fecha_ingresada = datetime.strptime(fecha_form, '%Y-%m-%d').date()
                hoy = datetime.now().date()

                if fecha_ingresada > hoy:
                    flash('No se pueden registrar fechas futuras', 'warning')
                else:
                    fecha_actualizada = datetime.now()
                    fecha_final = datetime.combine(fecha_ingresada, fecha_actualizada.time())

                    cur.execute(
                        "INSERT INTO producto (nombre, precio, descripcion, fecha) VALUES (%s, %s, %s, %s)",
                        (nombre, precio, descripcion, fecha_final)
                    )
                    mysql.connection.commit()
                    flash('Producto agregado correctamente', 'success')
                    return redirect(url_for('listar_productos_agregados'))
            except Exception as e:
                mysql.connection.rollback()
                flash(f'Error al agregar producto: {e}', 'danger')
            finally:
                cur.close()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, precio, descripcion, fecha FROM producto ORDER BY id")
    productos = cur.fetchall()
    cur.close()

    return render_template('productos_agregar.html', productos=productos)


@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
def editar_producto(pid):
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        precio = request.form.get('precio', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha_form = request.form.get('fecha', '').strip()

        if not nombre or not precio or not fecha_form:
            flash('Todos los campos son obligatorios', 'warning')
            return redirect(url_for('editar_producto', pid=pid))

        cur = mysql.connection.cursor()
        try:
            fecha_ingresada = datetime.strptime(fecha_form, '%Y-%m-%d').date()
            hoy = datetime.now().date()

            if fecha_ingresada > hoy:
                flash('No se pueden registrar fechas futuras', 'warning')
                return redirect(url_for('editar_producto', pid=pid))

            fecha_actualizada = datetime.now()
            fecha_final = datetime.combine(fecha_ingresada, fecha_actualizada.time())

            cur.execute("""
                UPDATE producto
                   SET nombre=%s, precio=%s, descripcion=%s, fecha=%s
                 WHERE id=%s
            """, (nombre, precio, descripcion, fecha_final, pid))
            
            mysql.connection.commit()
            flash('Producto actualizado correctamente', 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f'No se pudo actualizar: {e}', 'danger')
        finally:
            cur.close()

        return redirect(url_for('productos_listar'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, precio, descripcion, fecha FROM producto WHERE id=%s", (pid,))
    producto = cur.fetchone()
    cur.close()

    if not producto:
        flash('Producto no encontrado', 'warning')
        return redirect(url_for('productos_listar'))

    return render_template('productos_form.html', producto=producto, modo='editar')


@app.route('/productos/listar')
def productos_listar():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, precio, descripcion, fecha FROM producto ORDER BY id DESC")
    productos = cur.fetchall()
    cur.close()

    return render_template('productos_listar.html', productos=productos)


@app.route('/productos/<int:pid>/eliminar', methods=['POST'])
def eliminar_producto(pid):
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM producto WHERE id=%s", (pid,))
        mysql.connection.commit()
        flash('Producto eliminado', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al eliminar: {e}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('productos_listar'))


# ========================= EXPORTAR PRODUCTOS ==============================
@app.route('/productos/exportar')
def exportar_productos():
    if not session.get('logueado'):
        flash('Primero inicia sesión', 'warning')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, precio, descripcion, fecha FROM producto ORDER BY id DESC")
    productos = cur.fetchall()
    cur.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nombre', 'Precio', 'Descripción', 'Fecha'])

    for p in productos:
        writer.writerow([
            p['id'],
            p['nombre'],
            p['precio'],
            p['descripcion'],
            p['fecha']
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=productos.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


# =============================== EJECUCIÓN ================================
@app.route('/productos')
def listar_productos():
    return redirect(url_for('productos_listar'))


if __name__ == '__main__':
    app.run(debug=True, port=8000)
