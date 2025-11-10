from database import Session, Cancha, Reserva
from datetime import datetime, date
import json

class WhatsAppBotSimulado:
    def __init__(self):
        self.session = Session()
    
    def procesar_mensaje(self, mensaje, numero_telefono):
        mensaje = mensaje.lower().strip()
        
        if any(palabra in mensaje for palabra in ['hola', 'buenos', 'buenas']):
            return self._generar_saludo()
        
        elif 'precio' in mensaje or 'precios' in mensaje:
            return self._obtener_precios()
        
        elif 'disponibilidad' in mensaje or 'disponible' in mensaje or 'horario' in mensaje:
            return self._obtener_disponibilidad_hoy()
        
        elif 'reservar' in mensaje or 'reserva' in mensaje:
            return self._generar_enlace_reserva()
        
        else:
            return self._menu_principal()
    
    def _generar_saludo(self):
        return """¡Hola! 👋 Soy el asistente del *Complejo Deportivo Toledo*.

⏰ *Horarios:* 17:00 hs a 23:00 hs (reservas de 1 hora)

🎯 *Para reservar directamente:*
🔗 https://tudominio.com/reservar

¿En qué más puedo ayudarte?
• 💰 Conocer precios 
• 📅 Ver disponibilidad
• ℹ️ Más información"""
    
    def _obtener_precios(self):
        canchas = self.session.query(Cancha).filter_by(activa=True).all()
        
        respuesta = "🏟️ *PRECIOS DE CANCHAS*\n\n"
        for cancha in canchas:
            respuesta += f"• {cancha.nombre} ({cancha.tipo}): ₡{cancha.precio_hora:,} por hora\n"
        
        respuesta += "\n⏰ *Horario:* 17:00 - 23:00 hs"
        respuesta += "\n\n🎯 *Reservar ahora:*"
        respuesta += "\n🔗 http://localhost:5000/reservar"
        return respuesta
    
    def _obtener_disponibilidad_hoy(self):
        hoy = date.today()
        disponibilidad = {}
        
        canchas = self.session.query(Cancha).filter_by(activa=True).all()
        horarios = ["17:00 - 18:00", "18:00 - 19:00", "19:00 - 20:00", 
                   "20:00 - 21:00", "21:00 - 22:00", "22:00 - 23:00"]
        
        for cancha in canchas:
            reservas_hoy = self.session.query(Reserva).filter(
                Reserva.cancha_id == cancha.id,
                Reserva.fecha_reserva >= hoy,
                Reserva.fecha_reserva < hoy.replace(day=hoy.day + 1),
                Reserva.estado.in_(['pendiente', 'confirmada'])
            ).all()
            
            horarios_ocupados = [r.horario for r in reservas_hoy]
            disponibilidad[cancha.nombre] = {
                'disponibles': [h for h in horarios if h not in horarios_ocupados],
                'ocupados': horarios_ocupados
            }
        
        respuesta = "📅 *DISPONIBILIDAD HOY*\n\n"
        for cancha_nombre, info in disponibilidad.items():
            respuesta += f"*{cancha_nombre}:*\n"
            disponibles_count = len(info['disponibles'])
            respuesta += f"• {disponibles_count} horarios disponibles\n\n"
        
        respuesta += "🎯 *Ver disponibilidad completa y reservar:*"
        respuesta += "\n🔗 http://localhost:5000/reservar"
        return respuesta
    
    def _generar_enlace_reserva(self):
        return """🎯 *RESERVA EN LÍNEA*

¡Perfecto! Para realizar tu reserva:

🔗 *Enlace directo:*
http://localhost:5000/reservar

En el sistema podrás:
• 📅 Ver todos los horarios disponibles
• 🏟️ Elegir tu cancha preferida  
• 👤 Completar tus datos fácilmente
• 💳 Seleccionar método de pago
• ✅ Recibir confirmación inmediata

⏰ *Horarios:* 17:00 - 23:00 hs
⏱️ *Duración:* 1 hora por reserva

¡Te esperamos! ⚽🎾"""
    
    def _menu_principal(self):
        return """¡Hola! ¿Quieres reservar una cancha? 

🎯 *Enlace directo para reservar:*
🔗 http://localhost:5000/reservar

O pregúntame sobre:
• *Precios* - Ver tarifas
• *Disponibilidad* - Horarios libres
• *Reservar* - Volver a ver el enlace

⏰ Horarios: 17:00 - 23:00 hs"""