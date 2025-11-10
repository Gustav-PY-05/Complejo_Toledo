# test_sistema.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# --- CONEXIÓN A LA BASE DE DATOS ---
engine = create_engine(
    "postgresql+psycopg2://postgres:KokorO09945%40@localhost:5432/reservas_canchas_db",
    echo=True  # IMPORTANTE: True para ver las queries
)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- MODELO BD ---
class ReservaCancha(Base):
    __tablename__ = "reservas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    horario = Column(String, nullable=False)
    cantidad_horas = Column(Integer, nullable=False)
    cancha = Column(String, nullable=False)

    def __repr__(self):
        return f"<Reserva({self.nombre} {self.apellido}, {self.cancha}, {self.horario})>"

# Crear tabla si no existe
Base.metadata.create_all(engine)

# --- CLASES DEL SISTEMA ---
class Cancha:
    def __init__(self, nombre, tipo):
        self.nombre = nombre
        self.tipo = tipo
        self.disponible = True

    def __str__(self):
        estado = "Disponible" if self.disponible else "Ocupada"
        return f"{self.nombre} ({self.tipo}) - {estado}"

class Cliente:
    def __init__(self, nombre, apellido):
        self.nombre = nombre
        self.apellido = apellido

class SistemaReservasCanchas:
    def __init__(self):
        self.session = Session()
        self.canchas = []
        print("✅ Sistema de Reservas de Canchas iniciado")
        print("🔍 Verificando conexión a la base de datos...")
        
        # Test de conexión
        try:
            result = self.session.execute("SELECT version()")
            print(f"✅ Conectado a: {result.fetchone()[0]}")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return

    def registrar_cancha(self, cancha):
        self.canchas.append(cancha)
        print(f"🏟️ Cancha '{cancha.nombre}' registrada en el sistema.")

    def mostrar_canchas(self):
        print("\n📋 Canchas en el sistema:")
        for c in self.canchas:
            print("-", c)

    def realizar_reserva(self, cliente, horario, horas, cancha):
        print(f"\n🔍 Intentando reserva: {cliente.nombre} para {cancha.nombre} a las {horario}")
        
        if not cancha.disponible:
            print(f"❌ La cancha {cancha.nombre} ya está ocupada en memoria.")
            return False

        # Verificar en la BD si ya existe una reserva
        reserva_existente = self.session.query(ReservaCancha).filter_by(
            cancha=cancha.nombre, 
            horario=horario
        ).first()
        
        if reserva_existente:
            print(f"❌ Ya existe reserva en BD para {cancha.nombre} a las {horario}")
            cancha.disponible = False
            return False

        # Crear nueva reserva
        reserva = ReservaCancha(
            nombre=cliente.nombre,
            apellido=cliente.apellido,
            horario=horario,
            cantidad_horas=horas,
            cancha=cancha.nombre
        )

        try:
            print("💾 Guardando reserva en la base de datos...")
            self.session.add(reserva)
            self.session.commit()
            print("✅ COMMIT realizado exitosamente")
            
            # Verificar que realmente se guardó
            reserva_guardada = self.session.query(ReservaCancha).filter_by(
                nombre=cliente.nombre,
                apellido=cliente.apellido,
                horario=horario
            ).first()
            
            if reserva_guardada:
                print(f"✅ Reserva confirmada en BD - ID: {reserva_guardada.id}")
                cancha.disponible = False
                return True
            else:
                print("❌ La reserva no se encontró después del commit")
                return False
                
        except Exception as e:
            self.session.rollback()
            print(f"⚠️ Error al guardar la reserva: {e}")
            return False

    def listar_reservas(self):
        print("\n🔍 Consultando reservas en la base de datos...")
        try:
            reservas = self.session.query(ReservaCancha).all()
            print(f"📅 Se encontraron {len(reservas)} reservas:")
            
            if not reservas:
                print(" (No hay reservas registradas)")
            else:
                for r in reservas:
                    print(f"- ID:{r.id} | {r.nombre} {r.apellido} | {r.cancha} | {r.horario} | {r.cantidad_horas}h")
            
            return reservas
        except Exception as e:
            print(f"❌ Error al listar reservas: {e}")
            return []

    def cancelar_reserva(self, nombre):
        print(f"\n🗑️ Intentando cancelar reservas de {nombre}...")
        reservas = self.session.query(ReservaCancha).filter_by(nombre=nombre).all()
        
        print(f"🔍 Se encontraron {len(reservas)} reservas para cancelar")
        
        if reservas:
            for reserva in reservas:
                print(f"Cancelando reserva ID: {reserva.id}")
                # Liberar la cancha correspondiente
                for cancha in self.canchas:
                    if cancha.nombre == reserva.cancha:
                        cancha.disponible = True
                        print(f"Cancha {cancha.nombre} liberada")
                
                self.session.delete(reserva)
            
            self.session.commit()
            print(f"✅ {len(reservas)} reserva(s) cancelada(s)")
        else:
            print("⚠️ No se encontraron reservas")

# --- PRUEBA DETALLADA ---
if __name__ == "__main__":
    print("=" * 50)
    print("INICIANDO PRUEBA DEL SISTEMA")
    print("=" * 50)
    
    sistema = SistemaReservasCanchas()

    # Crear canchas
    print("\n" + "=" * 30)
    print("REGISTRANDO CANCHAS")
    print("=" * 30)
    cancha1 = Cancha("Cancha 1", "Fútbol 5")
    cancha2 = Cancha("Cancha 2", "Fútbol 7")

    sistema.registrar_cancha(cancha1)
    sistema.registrar_cancha(cancha2)

    # Mostrar estado inicial
    sistema.mostrar_canchas()
    
    # Listar reservas iniciales
    sistema.listar_reservas()

    # Realizar reserva
    print("\n" + "=" * 30)
    print("REALIZANDO RESERVA")
    print("=" * 30)
    cliente1 = Cliente("Gustavo", "Benitez")
    exito = sistema.realizar_reserva(cliente1, "16:00 - 18:00", 2, cancha1)
    
    if exito:
        print("🎉 RESERVA EXITOSA")
    else:
        print("💥 RESERVA FALLIDA")

    # Mostrar estado después de reserva
    sistema.mostrar_canchas()
    
    # Listar reservas después de reservar
    sistema.listar_reservas()

    # Cancelar reserva
    print("\n" + "=" * 30)
    print("CANCELANDO RESERVA")
    print("=" * 30)
    sistema.cancelar_reserva("Gustavo")
    
    # Estado final
    sistema.mostrar_canchas()
    sistema.listar_reservas()

    print("\n" + "=" * 50)
    print("PRUEBA COMPLETADA")
    print("=" * 50)