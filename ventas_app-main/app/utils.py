import qrcode
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from flask import send_file



def generar_qr(codigo_barras):
    # Ruta donde se guardará la imagen QR
    qr_path = f'app/static/qr/{codigo_barras}.png'

    # Crear el QR con el dato (puede ser solo el código de barras, o más)
    qr = qrcode.make(codigo_barras)

    # Asegurarse de que la carpeta exista
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)

    # Guardar la imagen
    qr.save(qr_path)

    return qr_path  # Retorna la ruta para poder mostrarla después

# app/utils.py

CATEGORIAS = {
    'Hombre': '01',
    'Mujer': '02',
}

TIPOS = {
    'Polerón': '01',
    'Chaqueta': '02',
    'Pantalón': '03',
    'Camisa': '04',
    'Polera': '05',
    'Shorts': '06',
    'Blusa': '07',
    'Buzos': '08'
}

TALLAS = {
    'XS': '01',
    'S': '02',
    'M': '03',
    'L': '04',
    'XL': '05',
    'XXL': '06'
}

def generar_codigo_barras(producto, existing_count):
    categoria = CATEGORIAS.get(producto.genero, '00')
    tipo = TIPOS.get(producto.tipo_producto, '00')
    talla = TALLAS.get(producto.talla, '00')
    secuencial = str(existing_count + 1).zfill(4)  # Ej: 0001
    return f"{categoria}{tipo}{talla}{secuencial}"

def generar_boleta_pdf(ventas, metodo_pago, cliente=None, vuelto=0):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "BOLETA DE VENTA")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Método de Pago: {metodo_pago}")
    if metodo_pago == "Fiado":
        c.drawString(250, height - 70, f"Cliente: {cliente}")
    if metodo_pago == "Efectivo":
        c.drawString(250, height - 70, f"Vuelto: ${vuelto}")

    c.drawString(50, height - 90, f"Fecha: {ventas[0].fecha.strftime('%d-%m-%Y %H:%M:%S')}")
    c.drawString(50, height - 110, f"Vendedor: {ventas[0].usuario.username}")

    y = height - 140
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Producto")
    c.drawString(250, y, "Cantidad")
    c.drawString(350, y, "Precio Unit.")
    c.drawString(450, y, "Subtotal")
    y -= 20

    total = 0
    c.setFont("Helvetica", 10)
    for venta in ventas:
        prod = venta.producto
        precio = prod.precio  # Asegúrate de tener un campo 'precio' en Producto
        subtotal = precio * venta.cantidad
        total += subtotal

        c.drawString(50, y, prod.nombre)
        c.drawString(250, y, str(venta.cantidad))
        c.drawString(350, y, f"${precio}")
        c.drawString(450, y, f"${subtotal}")
        y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 10, f"TOTAL: ${total}")
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
