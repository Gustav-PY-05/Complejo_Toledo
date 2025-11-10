from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import Session, Reserva, Cliente, Cancha
from datetime import datetime, date, timedelta
import json

# Blueprint para el admin
admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix='/admin')

# Contraseña simple para desarrollo
ADMIN_PASSWORD = "toledo123"

@admin_blueprint.route('/')
def admin_login():
    return render_template('admin_login.html')

@admin_blueprint.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Contraseña incorrecta'})

@admin_blueprint.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin')

def check_admin():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    return None

@admin_blueprint.route('/dashboard')
def dashboard():
    redirect_response = check_admin()
    if redirect_response:
        return redirect_response
    
    session_db = Session()
    try:
        # Estadísticas para el dashboard
        total_reservas = session_db.query(Reserva).count()
        
        reservas_hoy = session_db.query(Reserva).filter(
            Reserva.fecha_reserva >= date.today(),
            Reserva.fecha_reserva < date.today() + timedelta(days=1)
        ).count()
        
        reservas_pendientes = session_db.query(Reserva).filter_by(estado='pendiente').count()
        reservas_confirmadas = session_db.query(Reserva).filter_by(estado='confirmada').count()
        
        # Últimas 5 reservas
        ultimas_reservas = session_db.query(Reserva).order_by(Reserva.fecha_creacion.desc()).limit(5).all()
        
        # Preparar datos para las últimas reservas
        reservas_data = []
        for reserva in ultimas_reservas:
            cliente = session_db.query(Cliente).get(reserva.cliente_id)
            cancha = session_db.query(Cancha).get(reserva.cancha_id)
            reservas_data.append({
                'id': reserva.id,
                'cliente': f"{cliente.nombre} {cliente.apellido}",
                'cancha': cancha.nombre,
                'fecha': reserva.fecha_reserva.strftime('%d/%m/%Y'),
                'horario': reserva.horario,
                'estado': reserva.estado,
                'monto': reserva.monto_total
            })
        
        return render_template('admin_dashboard.html',
                             total_reservas=total_reservas,
                             reservas_hoy=reservas_hoy,
                             reservas_pendientes=reservas_pendientes,
                             reservas_confirmadas=reservas_confirmadas,
                             ultimas_reservas=reservas_data)
    finally:
        session_db.close()

@admin_blueprint.route('/reservas')
def gestion_reservas():
    redirect_response = check_admin()
    if redirect_response:
        return redirect_response
    
    session_db = Session()
    try:
        # Obtener parámetros de filtro
        estado = request.args.get('estado', 'todas')
        fecha = request.args.get('fecha', '')
        
        # Construir query base
        query = session_db.query(Reserva)
        
        # Aplicar filtros
        if estado != 'todas':
            query = query.filter(Reserva.estado == estado)
        
        if fecha:
            try:
                fecha_filtro = datetime.strptime(fecha, '%Y-%m-%d').date()
                query = query.filter(
                    Reserva.fecha_reserva >= fecha_filtro,
                    Reserva.fecha_reserva < fecha_filtro + timedelta(days=1)
                )
            except:
                pass
        
        reservas = query.order_by(Reserva.fecha_reserva.desc()).all()
        
        # Preparar datos para la tabla
        reservas_data = []
        for reserva in reservas:
            cliente = session_db.query(Cliente).get(reserva.cliente_id)
            cancha = session_db.query(Cancha).get(reserva.cancha_id)
            reservas_data.append({
                'id': reserva.id,
                'cliente_nombre': f"{cliente.nombre} {cliente.apellido}",
                'cliente_telefono': cliente.telefono,
                'cancha_nombre': cancha.nombre,
                'cancha_tipo': cancha.tipo,
                'fecha_reserva': reserva.fecha_reserva.strftime('%d/%m/%Y'),
                'horario': reserva.horario,
                'estado': reserva.estado,
                'metodo_pago': reserva.metodo_pago,
                'monto': reserva.monto_total,
                'fecha_creacion': reserva.fecha_creacion.strftime('%d/%m/%Y %H:%M')
            })
        
        return render_template('admin_reservas.html', 
                             reservas=reservas_data,
                             filtro_estado=estado,
                             filtro_fecha=fecha)
    finally:
        session_db.close()

@admin_blueprint.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    redirect_response = check_admin()
    if redirect_response:
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    data = request.json
    reserva_id = data.get('reserva_id')
    nuevo_estado = data.get('nuevo_estado')
    
    session_db = Session()
    try:
        reserva = session_db.query(Reserva).get(reserva_id)
        if reserva:
            reserva.estado = nuevo_estado
            session_db.commit()
            return jsonify({'success': True, 'mensaje': 'Estado actualizado correctamente'})
        else:
            return jsonify({'success': False, 'error': 'Reserva no encontrada'})
    except Exception as e:
        session_db.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        session_db.close()

@admin_blueprint.route('/reporte_diario')
def reporte_diario():
    redirect_response = check_admin()
    if redirect_response:
        return redirect_response
    
    session_db = Session()
    try:
        fecha_reporte = request.args.get('fecha', date.today().isoformat())
        
        try:
            fecha = datetime.strptime(fecha_reporte, '%Y-%m-%d').date()
        except:
            fecha = date.today()
        
        # Obtener reservas del día
        reservas_dia = session_db.query(Reserva).filter(
            Reserva.fecha_reserva >= fecha,
            Reserva.fecha_reserva < fecha + timedelta(days=1)
        ).all()
        
        # Calcular estadísticas
        total_reservas = len(reservas_dia)
        ingresos_totales = sum(r.monto_total or 0 for r in reservas_dia if r.estado in ['confirmada', 'completada'])
        
        reservas_por_estado = {}
        for reserva in reservas_dia:
            reservas_por_estado[reserva.estado] = reservas_por_estado.get(reserva.estado, 0) + 1
        
        # Preparar datos detallados
        reservas_detalle = []
        for reserva in reservas_dia:
            cliente = session_db.query(Cliente).get(reserva.cliente_id)
            cancha = session_db.query(Cancha).get(reserva.cancha_id)
            reservas_detalle.append({
                'id': reserva.id,
                'cliente': f"{cliente.nombre} {cliente.apellido}",
                'cancha': cancha.nombre,
                'horario': reserva.horario,
                'estado': reserva.estado,
                'metodo_pago': reserva.metodo_pago,
                'monto': reserva.monto_total
            })
        
        return jsonify({
            'fecha': fecha.isoformat(),
            'total_reservas': total_reservas,
            'ingresos_totales': ingresos_totales,
            'reservas_por_estado': reservas_por_estado,
            'reservas_detalle': reservas_detalle
        })
    finally:
        session_db.close()
        
@admin_blueprint.route('/backup')
def backup_datos():
    redirect_response = check_admin()
    if redirect_response:
        return redirect_response
    
    session_db = Session()
    try:
        from datetime import datetime
        import json
        
        # Obtener todos los datos
        reservas = session_db.query(Reserva).all()
        clientes = session_db.query(Cliente).all()
        canchas = session_db.query(Cancha).all()
        
        # Preparar datos para backup
        backup_data = {
            'fecha_backup': datetime.now().isoformat(),
            'reservas': [],
            'clientes': [],
            'canchas': []
        }
        
        for reserva in reservas:
            backup_data['reservas'].append({
                'id': reserva.id,
                'cliente_id': reserva.cliente_id,
                'cancha_id': reserva.cancha_id,
                'fecha_reserva': reserva.fecha_reserva.isoformat(),
                'horario': reserva.horario,
                'estado': reserva.estado,
                'monto_total': reserva.monto_total,
                'fecha_creacion': reserva.fecha_creacion.isoformat()
            })
        
        for cliente in clientes:
            backup_data['clientes'].append({
                'id': cliente.id,
                'cedula': cliente.cedula,
                'nombre': cliente.nombre,
                'apellido': cliente.apellido,
                'telefono': cliente.telefono,
                'fecha_registro': cliente.fecha_registro.isoformat()
            })
        
        for cancha in canchas:
            backup_data['canchas'].append({
                'id': cancha.id,
                'nombre': cancha.nombre,
                'tipo': cancha.tipo,
                'precio_hora': cancha.precio_hora
            })
        
        # Crear archivo de backup
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{fecha_str}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': f'Backup creado: {filename}',
            'filename': filename,
            'estadisticas': {
                'reservas': len(backup_data['reservas']),
                'clientes': len(backup_data['clientes']),
                'canchas': len(backup_data['canchas'])
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        session_db.close()
@admin_blueprint.route('/limpiar_reservas_antiguas', methods=['POST'])
def limpiar_reservas_antiguas():
    """Elimina reservas de hace más de 30 días (para admin)"""
    redirect_response = check_admin()
    if redirect_response:
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    session_db = Session()
    try:
        from datetime import timedelta
        
        # Reservas de hace más de 30 días
        fecha_limite = date.today() - timedelta(days=30)
        
        reservas_antiguas = session_db.query(Reserva).filter(
            Reserva.fecha_reserva < fecha_limite
        ).all()
        
        count = len(reservas_antiguas)
        
        # Crear backup antes de eliminar
        backup_data = []
        for reserva in reservas_antiguas:
            backup_data.append({
                'id': reserva.id,
                'cliente_id': reserva.cliente_id,
                'cancha_id': reserva.cancha_id,
                'fecha': reserva.fecha_reserva.isoformat(),
                'horario': reserva.horario,
                'estado': reserva.estado
            })
        
        # Eliminar reservas antiguas
        for reserva in reservas_antiguas:
            session_db.delete(reserva)
        
        session_db.commit()
        
        return jsonify({
            'success': True, 
            'mensaje': f'Se eliminaron {count} reservas antiguas (anteriores a {fecha_limite.strftime("%d/%m/%Y")})',
            'eliminadas': count
        })
        
    except Exception as e:
        session_db.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        session_db.close()