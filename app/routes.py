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
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import datetime
import os
from werkzeug.utils import secure_filename
import base64

# ========================
# Helpers Base64
# ========================
def _file_to_b64(file_storage):
    """
    Convierte un FileStorage a (mime, base64str).
    Retorna (None, None) si no se subió archivo.
    OJO: esto consume el stream; si luego quieres .save(), haz file_storage.stream.seek(0).
    """
    if not file_storage or file_storage.filename == '':
        return None, None
    raw = file_storage.read()
    mime = getattr(file_storage, "mimetype", None) or "image/png"
    b64 = base64.b64encode(raw).decode('utf-8')
    return mime, b64

def _qr_to_b64(texto):
    """Genera un PNG en base64 de un QR a partir de 'texto'."""
    if not texto:
        return None
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


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
    if request.method == 'POST':   # <-- corregido (sin ])
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
# REGISTRO (con clave por rol)
# ========================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm-password', '')
        rol = request.form.get('rol', '').strip()
        # clave de registro escrita en el formulario
        clave = request.form.get('clave_registro', '').strip()

        if not all([nombre, apellido, email, telefono, password, confirm_password, rol]):
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for('registro'))

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for('registro'))

        if User.query.filter_by(email=email).first():
            flash("El correo ya está registrado.", "warning")
            return redirect(url_for('registro'))

        # Exigir clave solo para roles sensibles
        if rol in ('administrador', 'vendedor'):
            admin_key = app.config.get('ADMIN_REG_KEY')
            vend_key  = app.config.get('VENDEDOR_REG_KEY')
            expected  = admin_key if rol == 'administrador' else vend_key

            if not expected:
                flash("Falta configurar la clave de registro para el rol seleccionado.", "danger")
                return redirect(url_for('registro'))

            if clave != expected:
                flash("Clave de registro incorrecta para el rol seleccionado.", "danger")
                return redirect(url_for('registro'))

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
# NUEVA VENTA (admin + vendedor)
# ========================
@app.route('/nueva_venta', methods=['GET', 'POST'])
@login_required
def nueva_venta():
    if current_user.rol not in ('vendedor', 'administrador'):
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
# AGREGAR PRODUCTO
# ========================
@app.route('/agregar_producto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if request.method == 'POST':
        # 1️⃣ Datos
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        caracteristicas = request.form['caracteristicas']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        talla = request.form['talla']
        tipo_producto = request.form['tipo_producto']
        marca = request.form['marca']
        genero = request.form['genero']

        # 2️⃣ Imagen → Base64 (si se sube)
        imagen = request.files.get('imagen')
        imagen_local = None
        imagen_mime = None
        imagen_b64 = None
        if imagen and imagen.filename != '':
            imagen_mime, imagen_b64 = _file_to_b64(imagen)

            # (Opcional) Guardar archivo físico legacy SOLO si está activado
            if app.config.get('SAVE_UPLOADS_TO_DISK') and app.config.get('UPLOAD_FOLDER'):
                try:
                    imagen.stream.seek(0)
                except Exception:
                    pass
                filename = secure_filename(imagen.filename)
                ruta_imagen = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    imagen.save(ruta_imagen)
                    imagen_local = filename  # compatibilidad
                except Exception:
                    # No romper si el disco es efímero/no escribible
                    imagen_local = None

        # 3️⃣ Contar existentes para código secuencial
        existing_count = Producto.query.filter_by(
            genero=genero,
            tipo_producto=tipo_producto,
            talla=talla
        ).count()

        # 4️⃣ Crear producto
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
            imagen_local=imagen_local,  # compatibilidad
            imagen_mime=imagen_mime,
            imagen_b64=imagen_b64
        )

        # 5️⃣ Código de barras
        nuevo_producto.codigo_barras = generar_codigo_barras(nuevo_producto, existing_count)

        # 6️⃣ QR en Base64 (siempre) y archivo legacy opcional
        nuevo_producto.qr_b64 = _qr_to_b64(nuevo_producto.codigo_barras)
        if app.config.get('SAVE_UPLOADS_TO_DISK'):
            try:
                generar_qr(nuevo_producto.codigo_barras)  # legacy opcional
            except Exception:
                pass

        # 7️⃣ Guardar
        db.session.add(nuevo_producto)
        db.session.commit()

        flash("Producto agregado correctamente con código de barras y QR.", "success")
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
# EDITAR PRODUCTO
# ========================
@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        # Actualizar campos
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.caracteristicas = request.form['caracteristicas']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        producto.talla = request.form['talla']
        producto.tipo_producto = request.form['tipo_producto']
        producto.marca = request.form['marca']
        producto.genero = request.form['genero']

        # Imagen nueva (opcional)
        imagen = request.files.get('imagen')
        if imagen and imagen.filename != '':
            mime, img_b64 = _file_to_b64(imagen)
            if img_b64:
                producto.imagen_mime = mime
                producto.imagen_b64  = img_b64

            # Guardar archivo legacy opcional
            if app.config.get('SAVE_UPLOADS_TO_DISK') and app.config.get('UPLOAD_FOLDER'):
                try:
                    imagen.stream.seek(0)
                except Exception:
                    pass
                filename = secure_filename(imagen.filename)
                ruta_imagen = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    imagen.save(ruta_imagen)
                    producto.imagen_local = filename
                except Exception:
                    pass  # no romper en prod si no se puede escribir

        db.session.commit()
        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('productos'))

    return render_template('editar_producto.html', producto=producto)

# ========================
# PANEL ADMINISTRADOR
# ========================
@app.route('/admin')
@login_required
def admin_index():
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('login'))

    search = request.args.get('search')
    activos = request.args.get('activos')

    if search:
        usuarios = User.query.filter(
            (User.nombre.ilike(f'%{search}%')) |
            (User.apellido.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.rol.ilike(f'%{search}%'))
        ).all()
    else:
        usuarios = User.query.all()

    if activos == '1':
        usuarios = [u for u in usuarios if len(u.ventas) > 0]

    total_usuarios = User.query.count()
    total_ventas = Venta.query.count()

    stock_minimo = 5
    productos_stock_critico = Producto.query.filter(Producto.stock < stock_minimo).count()

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
# EDITAR USUARIO (bloqueo vendedor -> admin)
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

        nuevo_rol = request.form['rol']

        # 🚫 No permitir elevar de vendedor → administrador
        if usuario.rol == 'vendedor' and nuevo_rol == 'administrador':
            flash("No se puede cambiar el rol de 'vendedor' a 'administrador' desde esta pantalla.", "warning")
            return redirect(url_for('editar_usuario', id=id))

        # 🚫 No permitir cambiarse el propio rol
        if usuario.id == current_user.id and usuario.rol != nuevo_rol:
            flash("No puedes cambiar tu propio rol.", "warning")
            return redirect(url_for('editar_usuario', id=id))

        usuario.rol = nuevo_rol
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

    if usuario.id == current_user.id:
        flash("No puedes eliminarte a ti mismo.", "warning")
        return redirect(url_for('admin_index'))

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

# ========================
# HISTORIAL VENTAS
# ========================
@app.route('/historial_ventas', methods=['GET'])
@login_required
def historial_ventas():
    if current_user.rol != 'administrador':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('login'))

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
        datetime=datetime,
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

    mes = request.args.get('mes')  # formato: YYYY-MM
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
# ETIQUETAS (PDF con QR en memoria)
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

    # Crear PDF en memoria (80x50 mm)
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(80 * mm, 50 * mm))
    c.setFont("Helvetica-Bold", 12)

    # Nombre del producto
    c.drawString(10 * mm, 40 * mm, f"{producto.nombre}")

    # Precio
    c.setFont("Helvetica", 10)
    c.drawString(10 * mm, 35 * mm, f"Precio: ${producto.precio:,.0f}")

    # Insertar QR
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

# ========================
# Endpoint de salud
# ========================
@app.get("/healthz")
def healthz():
    # Respuesta súper simple y rápida, sin DB
    return "ok", 200