from flask import render_template, request, redirect, url_for, flash, make_response, send_file
from app import app, login_manager, db, bcrypt
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User, Producto, Venta
import pandas as pd
from io import BytesIO
import calendar
from app.utils import generar_codigo_barras, generar_qr
import qrcode
import json
from flask import session, make_response, render_template_string
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import datetime
from app import db
import os
from app.models import Producto
from werkzeug.utils import secure_filename
from app.cloudinary_utils import upload_image, delete_image
import cloudinary
import cloudinary.uploader



UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')



# ========================
# RUTA RAÍZ
# ========================
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.rol == 'administrador':
            return redirect(url_for('admin_index'))
        elif current_user.rol == 'vendedor':
            return redirect(url_for('ventas'))
    return redirect(url_for('login'))

# ========================
# LOGIN
# ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Correo y contraseña son obligatorios.", "danger")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            if user.rol == 'administrador':
                return redirect(url_for('admin_index'))
            else:
                return redirect(url_for('ventas'))

        flash("Email o contraseña incorrectos.", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')

# ========================
# REGISTRO (robusto)
# ========================
from flask import current_app

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email    = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm-password', '')
        rol      = request.form.get('rol', '').strip()
        clave_rol = request.form.get('clave_rol', '').strip()

        # Validaciones básicas
        if not all([nombre, apellido, email, telefono, password, confirm_password, rol, clave_rol]):
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for('registro'))

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('registro'))

        # Traer claves desde la config de manera segura
        clave_admin_cfg    = current_app.config.get('CLAVE_ADMIN', '')
        clave_vendedor_cfg = current_app.config.get('CLAVE_VENDEDOR', '')

        # Si faltan en config, avisar (en vez de crashear)
        if rol == 'administrador':
            if not clave_admin_cfg:
                flash("Falta configurar CLAVE_ADMIN en el servidor.", "danger")
                return redirect(url_for('registro'))
            if clave_rol != clave_admin_cfg:
                flash("Clave incorrecta para registrar un administrador.", "danger")
                return redirect(url_for('registro'))

        elif rol == 'vendedor':
            if not clave_vendedor_cfg:
                flash("Falta configurar CLAVE_VENDEDOR en el servidor.", "danger")
                return redirect(url_for('registro'))
            if clave_rol != clave_vendedor_cfg:
                flash("Clave incorrecta para registrar un vendedor.", "danger")
                return redirect(url_for('registro'))

        else:
            flash("Rol inválido.", "danger")
            return redirect(url_for('registro'))

        # Correo único
        if User.query.filter_by(email=email).first():
            flash("El correo ya está registrado.", "warning")
            return redirect(url_for('registro'))

        # Crear usuario
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        nuevo_usuario = User(
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono,
            password=hashed_password,
            rol=rol
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("¡Usuario registrado correctamente! Ahora puedes iniciar sesión.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ========================
# SISTEMA DE VENTAS
# ========================
@app.route('/ventas')
@login_required
def ventas():
    return render_template('ventas.html')

# ========================
# NUEVA VENTA (ACTUALIZADO)
# ========================
@app.route('/nueva_venta', methods=['GET', 'POST'])
@login_required
def nueva_venta():
    if current_user.rol not in ['vendedor', 'administrador']:
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('login'))

    productos = Producto.query.all()

    if request.method == 'POST':
        datos = request.form.get("productos_seleccionados")
        metodo_pago = request.form.get("metodo_pago")
        efectivo_entregado = request.form.get("efectivo_entregado")
        cliente = request.form.get("cliente") if metodo_pago == "Fiado" else None

        try:
            productos_lista = json.loads(datos)
        except Exception as e:
            flash("Error al procesar los productos.", "danger")
            print("Error JSON:", e)
            return redirect(url_for('nueva_venta'))

        total = 0
        for item in productos_lista:
            producto = Producto.query.get(item["id"])
            if not producto or producto.stock < item["cantidad"]:
                flash(f"Stock insuficiente para {producto.nombre}", "danger")
                return redirect(url_for("nueva_venta"))

        for item in productos_lista:
            producto = Producto.query.get(item["id"])
            cantidad = item["cantidad"]
            producto.stock -= cantidad
            venta = Venta(
                producto_id=producto.id,
                usuario_id=current_user.id,
                cantidad=cantidad,
                metodo_pago=metodo_pago,
                cliente=cliente
            )
            db.session.add(venta)
            total += producto.precio * cantidad

        db.session.commit()
        flash(f"¡Venta registrada exitosamente! Total: ${total}", "success")

        return redirect(url_for("nueva_venta", mostrar_mensaje="1"))

    mostrar_mensaje = request.args.get("mostrar_mensaje") == "1"

    productos_json = json.dumps([{
        "id": p.id,
        "nombre": p.nombre,
        "precio": p.precio,
        "codigo_barras": p.codigo_barras
    } for p in productos])

    return render_template(
        'nueva_venta.html',
        productos=productos,
        productos_json=productos_json,
        mostrar_mensaje=mostrar_mensaje
    )



# ========================
# AGREGAR PRODUCTO (Cloudinary)
# ========================
@app.route('/agregar_producto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        caracteristicas = request.form['caracteristicas']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        talla = request.form['talla']
        tipo_producto = request.form['tipo_producto']
        marca = request.form['marca']
        genero = request.form['genero']

        imagen_local = None

        # 📌 Subida de imagen a Cloudinary
        imagen = request.files.get('imagen')
        if imagen and imagen.filename != '':
            upload_result = cloudinary.uploader.upload(
                imagen,
                folder="productos",  # Carpeta en Cloudinary
                resource_type="image"
            )
            imagen_local = upload_result['public_id']  # Guardamos el public_id

        existing_count = Producto.query.filter_by(
            genero=genero,
            tipo_producto=tipo_producto,
            talla=talla
        ).count()

        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            caracteristicas=caracteristicas,
            precio=precio,
            stock=stock,
            talla=talla,
            tipo_producto=tipo_producto,
            marca=marca,
            genero=genero,
            imagen_local=imagen_local
        )

        nuevo_producto.codigo_barras = generar_codigo_barras(nuevo_producto, existing_count)
        db.session.add(nuevo_producto)
        db.session.commit()

        generar_qr(nuevo_producto.codigo_barras)

        flash("Producto agregado correctamente con código de barras, QR y foto optimizada.", "success")
        return redirect(url_for('productos'))

    return render_template('agregar_producto.html')



# ========================
# PRODUCTOS
# ========================
@app.route('/productos')
@login_required
def productos():
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('login'))

    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)

# ========================
# ELIMINAR PRODUCTO
# ========================
@app.route('/eliminar_producto/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado correctamente.', 'success')
    return redirect(url_for('productos'))

# ========================
# EDITAR PRODUCTO (Cloudinary)
# ========================
@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.caracteristicas = request.form['caracteristicas']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        producto.talla = request.form['talla']
        producto.tipo_producto = request.form['tipo_producto']
        producto.marca = request.form['marca']
        producto.genero = request.form['genero']

        # 📌 Subida de nueva imagen a Cloudinary si se sube
        imagen = request.files.get('imagen')
        if imagen and imagen.filename != '':
            upload_result = cloudinary.uploader.upload(
                imagen,
                folder="productos",
                resource_type="image"
            )
            producto.imagen_local = upload_result['public_id']

        db.session.commit()
        flash('Producto actualizado correctamente con imagen optimizada.', 'success')
        return redirect(url_for('productos'))

    return render_template('editar_producto.html', producto=producto)


# ========================
# PANEL ADMINISTRADOR
# ========================
@app.route('/admin')  # Ruta protegida: solo accesible para administradores
@login_required       # Solo usuarios autenticados pueden ingresar
def admin_index():
    # Si el usuario actual no es administrador, bloquear acceso
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('login'))

    # Obtener parámetros GET desde la URL
    search = request.args.get('search')   # Palabra buscada
    activos = request.args.get('activos') # Checkbox activos=1 si está marcado

    # Si hay texto en el buscador, filtrar usuarios por nombre, apellido, email o rol
    if search:
        usuarios = User.query.filter(
            (User.nombre.ilike(f'%{search}%')) |
            (User.apellido.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.rol.ilike(f'%{search}%'))
        ).all()
    else:
        # Si no se está buscando, traer todos los usuarios
        usuarios = User.query.all()

    # Si el checkbox "Solo usuarios con ventas" está marcado
    if activos == '1':
        # Filtrar solo usuarios que tengan al menos 1 venta
        usuarios = [u for u in usuarios if len(u.ventas) > 0]

    # 🔥 Indicadores dinámicos para las tarjetas

    # Total de usuarios registrados (sin filtro)
    total_usuarios = User.query.count()

    # Total de ventas realizadas en el sistema
    total_ventas = Venta.query.count()

    # Definir el stock mínimo para que un producto sea considerado crítico
    stock_minimo = 5 
    # Contar productos cuyo stock sea menor al stock mínimo
    productos_stock_critico = Producto.query.filter(Producto.stock < stock_minimo).count()

    # Enviar todos los datos al template HTML
    return render_template(
        'admin_index.html',
        usuarios=usuarios,                     
        search=search,                         
        activos=activos,                       
        total_usuarios=total_usuarios,         
        total_ventas=total_ventas,             
        productos_stock_critico=productos_stock_critico  
    )

# ========================
# LOGOUT
# ========================
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# ========================
# CARGA DE USUARIO
# ========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========================
# EDITAR USUARIO
# ========================
@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('login'))

    usuario = User.query.get_or_404(id)

    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.apellido = request.form['apellido']
        usuario.email = request.form['email']
        usuario.telefono = request.form['telefono']
        usuario.rol = request.form['rol']

        if usuario.id == current_user.id and usuario.rol != request.form['rol']:
            flash("No puedes cambiar tu propio rol.", "warning")
            return redirect(url_for('editar_usuario', id=id))

        db.session.commit()
        flash("Usuario actualizado exitosamente.", "success")
        return redirect(url_for('admin_index'))

    return render_template('editar_usuario.html', usuario=usuario)

# ========================
# ELIMINAR USUARIO
# ========================
@app.route('/admin/eliminar/<int:id>')
@login_required
def eliminar_usuario(id):
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('login'))

    usuario = User.query.get_or_404(id)

    # 🚫 Evitar que se elimine a sí mismo
    if usuario.id == current_user.id:
        flash("No puedes eliminarte a ti mismo.", "warning")
        return redirect(url_for('admin_index'))

    # 🚫 Evitar eliminar si tiene ventas asociadas
    if usuario.ventas and len(usuario.ventas) > 0:
        flash("Este usuario no puede eliminarse porque tiene ventas registradas.", "warning")
        return redirect(url_for('admin_index'))

    db.session.delete(usuario)
    db.session.commit()
    flash("Usuario eliminado exitosamente.", "success")
    return redirect(url_for('admin_index'))


# ========================
# CONSULTAR STOCK
# ========================
@app.route('/consultar_stock')
@login_required
def consultar_stock():
    productos = Producto.query.all()
    return render_template('consultar_stock.html', productos=productos)

# ========================
# CATÁLOGO
# ========================
@app.route('/catalogo')
@login_required
def catalogo():
    genero = request.args.get('genero')
    tipo_producto = request.args.get('tipo_producto')

    query = Producto.query

    if genero:
        query = query.filter_by(genero=genero)
    if tipo_producto:
        query = query.filter_by(tipo_producto=tipo_producto)

    productos = query.all()
    return render_template('catalogo.html', productos=productos)




# ========================
# VER DETALLES DE PRODUCTO
# ========================
@app.route('/producto/<int:id>')
@login_required
def ver_detalles(id):
    producto = Producto.query.get_or_404(id)
    return render_template('detalle_producto.html', producto=producto)


@app.route('/historial_ventas', methods=['GET'])
@login_required
def historial_ventas():
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('login'))

    # Obtener filtros
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    metodo_pago = request.args.get('metodo_pago')
    vendedor_id = request.args.get('vendedor_id')

    ventas = Venta.query

    if fecha_inicio:
        ventas = ventas.filter(Venta.fecha >= fecha_inicio)
    if fecha_fin:
        ventas = ventas.filter(Venta.fecha <= fecha_fin)
    if metodo_pago and metodo_pago != 'Todos':
        ventas = ventas.filter(Venta.metodo_pago == metodo_pago)
    if vendedor_id and vendedor_id != 'Todos':
        ventas = ventas.filter(Venta.usuario_id == vendedor_id)

    ventas = ventas.order_by(Venta.fecha.desc()).all()
    usuarios = User.query.all()

    return render_template(
        'historial_ventas.html',
        ventas=ventas,
        usuarios=usuarios,
        datetime=datetime,  # 👈 Esta línea permite usar datetime en el HTML
        filtros={
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'metodo_pago': metodo_pago,
            'vendedor_id': vendedor_id
        }
    )

# ========================
# EXPORTAR HISTORIAL A EXCEL
# ========================
@app.route('/exportar_excel_mes')
@login_required
def exportar_excel_mes():
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('login'))

    mes = request.args.get('mes')  # formato: 2025-06
    if not mes:
        flash("Debes seleccionar un mes", "warning")
        return redirect(url_for('historial_ventas'))

    anio, mes_num = map(int, mes.split('-'))
    inicio = f"{anio}-{mes_num:02d}-01"
    ultimo_dia = calendar.monthrange(anio, mes_num)[1]
    fin = f"{anio}-{mes_num:02d}-{ultimo_dia}"

    ventas = Venta.query.filter(
        Venta.fecha >= inicio,
        Venta.fecha <= fin
    ).order_by(Venta.fecha.asc()).all()

    data = []
    for v in ventas:
        data.append({
            'Fecha': v.fecha.strftime('%d/%m/%Y %H:%M'),
            'Producto': v.producto.nombre,
            'Cantidad': v.cantidad,
            'Método de Pago': v.metodo_pago,
            'Cliente': v.cliente or '-',
            'Vendedor': f"{v.usuario.nombre} {v.usuario.apellido}"
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=f'Ventas_{mes}')
        worksheet = writer.sheets[f'Ventas_{mes}']
        for column_cells in worksheet.columns:
            max_length = max(len(str(cell.value)) for cell in column_cells)
            col_letter = column_cells[0].column_letter
            worksheet.column_dimensions[col_letter].width = max_length + 2

    

    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f'ventas_{mes}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ========================
# etiquetas
# ========================

@app.route('/descargar_etiqueta/<int:id>')
@login_required
def descargar_etiqueta(id):
    producto = Producto.query.get_or_404(id)

    # Crear imagen QR en memoria
    qr = qrcode.make(producto.codigo_barras)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Convertir a imagen compatible con ReportLab
    qr_image = ImageReader(qr_buffer)

    # Crear PDF en memoria
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(80 * mm, 50 * mm))  # Tamaño de etiqueta aproximado
    c.setFont("Helvetica-Bold", 12)

    # Nombre del producto
    c.drawString(10 * mm, 40 * mm, f"{producto.nombre}")

    # Precio
    c.setFont("Helvetica", 10)
    c.drawString(10 * mm, 35 * mm, f"Precio: ${producto.precio:,.0f}")

    # Insertar QR correctamente
    c.drawImage(qr_image, 10 * mm, 5 * mm, 30 * mm, 30 * mm)

    c.save()
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'etiqueta_{producto.nombre}.pdf',
        mimetype='application/pdf'
    )


# ========================
# ELIMINAR VENTA
# ========================

@app.route('/eliminar_venta/<int:venta_id>', methods=['POST'])
@login_required
def eliminar_venta(venta_id):
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('historial_ventas'))

    venta = Venta.query.get_or_404(venta_id)

    db.session.delete(venta)
    db.session.commit()

    flash("Venta eliminada correctamente", "success")
    return redirect(url_for('historial_ventas'))
