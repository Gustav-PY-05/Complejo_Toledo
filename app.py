from flask import Flask, render_template, request, jsonify, session
from database import Session, Cliente, Cancha, Reserva
from admin import admin_blueprint
from datetime import datetime, date
import json

app = Flask(__name__)
app.secret_key = 'complejo_toledo_secret_key_2024'

app.register_blueprint(admin_blueprint) 

HORARIOS = [
    "17:00 - 18:00", 
    "18:00 - 19:00",
    "19:00 - 20:00",
    "20:00 - 21:00", 
    "21:00 - 22:00",
    "22:00 - 23:00"
]

@app.route('/')
def index():
    session_db = Session()
    try:
        canchas = session_db.query(Cancha).filter_by(activa=True).all()
        return render_template('index.html', canchas=canchas, date_today=date.today().isoformat())
    finally:
        session_db.close()

@app.route('/disponibilidad')
def disponibilidad():
    session_db = Session()
    try:
        cancha_id = request.args.get('cancha_id')
        fecha_str = request.args.get('fecha', date.today().isoformat())
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except:
            fecha = date.today()
        
        reservas = session_db.query(Reserva).filter(
            Reserva.cancha_id == cancha_id,
            Reserva.fecha_reserva >= fecha,
            Reserva.fecha_reserva < fecha.replace(day=fecha.day + 1),
            Reserva.estado.in_(['pendiente', 'confirmada'])
        ).all()
        
        horarios_ocupados = [r.horario for r in reservas]
        horarios_disponibles = [h for h in HORARIOS if h not in horarios_ocupados]
        
        return jsonify({
            'cancha_id': cancha_id,
            'fecha': fecha.isoformat(),
            'horarios_disponibles': horarios_disponibles,
            'horarios_ocupados': horarios_ocupados
        })
    finally:
        session_db.close()

@app.route('/reservar', methods=['POST'])
def reservar():
    session_db = Session()
    try:
        datos = request.json
        
        required_fields = ['nombre', 'apellido', 'cedula', 'telefono', 'cancha_id', 'horario', 'metodo_pago']
        for field in required_fields:
            if field not in datos or not str(datos[field]).strip():
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        cliente = session_db.query(Cliente).filter_by(cedula=datos['cedula']).first()
        if not cliente:
            cliente = Cliente(
                cedula=datos['cedula'],
                nombre=datos['nombre'],
                apellido=datos['apellido'],
                telefono=datos['telefono'],
                email=datos.get('email', '')
            )
            session_db.add(cliente)
            session_db.flush()
        
        cancha = session_db.query(Cancha).get(datos['cancha_id'])
        if not cancha:
            return jsonify({'error': 'Cancha no encontrada'}), 400
        
        horas = 1
        monto_total = cancha.precio_hora * horas
        
        fecha_reserva = datetime.strptime(datos.get('fecha', date.today().isoformat()), '%Y-%m-%d').date()
        reserva_existente = session_db.query(Reserva).filter(
            Reserva.cancha_id == datos['cancha_id'],
            Reserva.fecha_reserva >= fecha_reserva,
            Reserva.fecha_reserva < fecha_reserva.replace(day=fecha_reserva.day + 1),
            Reserva.horario == datos['horario'],
            Reserva.estado.in_(['pendiente', 'confirmada'])
        ).first()
        
        if reserva_existente:
            return jsonify({'error': 'Este horario ya está reservado'}), 400
        
        reserva = Reserva(
            cliente_id=cliente.id,
            cancha_id=datos['cancha_id'],
            fecha_reserva=fecha_reserva,
            horario=datos['horario'],
            horas=horas,
            metodo_pago=datos['metodo_pago'],
            monto_total=monto_total,
            estado='pendiente'
        )
        
        session_db.add(reserva)
        session_db.commit()
        
        return jsonify({
            'success': True,
            'reserva_id': reserva.id,
            'mensaje': f'✅ Reserva confirmada. ID: {reserva.id}',
            'detalles': {
                'cliente': f"{datos['nombre']} {datos['apellido']}",
                'cancha': cancha.nombre,
                'tipo': cancha.tipo,
                'horario': datos['horario'],
                'fecha': fecha_reserva.strftime('%d/%m/%Y'),
                'metodo_pago': datos['metodo_pago'],
                'monto': f'Gs{monto_total:,}',
                'duracion':'una hora'
            }
        })
        
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': f'Error al procesar reserva: {str(e)}'}), 500
    finally:
        session_db.close()
@app.route('/reservar')
def landing_reservas():
    """Página de landing para compartir en WhatsApp"""
    return render_template('landing.html')

@app.route('/confirmacion/<int:reserva_id>')
def confirmacion(reserva_id):
    session_db = Session()
    try:
        reserva = session_db.query(Reserva).get(reserva_id)
        if not reserva:
            return "Reserva no encontrada", 404
        
        cliente = session_db.query(Cliente).get(reserva.cliente_id)
        cancha = session_db.query(Cancha).get(reserva.cancha_id)
        
        return render_template('confirmacion.html', 
                             reserva=reserva, 
                             cliente=cliente, 
                             cancha=cancha)
    finally:
        session_db.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
@app.route('/reservar')
def reservas():
    """Página de landing para compartir en WhatsApp"""
    return render_template('landing.html')