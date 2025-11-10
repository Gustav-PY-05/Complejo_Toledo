from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# Configuración de la base de datos
DATABASE_URL = "postgresql+psycopg2://postgres:KokorO09945%40@localhost:5432/proyecto_complejo_toledo"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cedula = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100))
    fecha_registro = Column(DateTime, default=func.now())

class Cancha(Base):
    __tablename__ = "canchas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    tipo = Column(String(50), nullable=False)
    precio_hora = Column(Integer, nullable=False)
    activa = Column(Boolean, default=True)

class Reserva(Base):
    __tablename__ = "reservas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=False)
    cancha_id = Column(Integer, nullable=False)
    fecha_reserva = Column(DateTime, nullable=False)
    horario = Column(String(50), nullable=False)
    horas = Column(Integer, nullable=False, default=2)
    estado = Column(String(20), default='pendiente')
    metodo_pago = Column(String(20))
    monto_total = Column(Integer)
    fecha_creacion = Column(DateTime, default=func.now())
    notas = Column(Text)

def init_db():
    Base.metadata.create_all(engine)
    print("✅ Base de datos inicializada")

def insertar_datos_ejemplo():
    session = Session()
    
    if session.query(Cancha).count() == 0:
        canchas = [
            Cancha(nombre="Cancha 1", tipo="Fútbol 5vs5(sintetico)", precio_hora=70000),
            Cancha(nombre="Cancha 2", tipo="Fútbol 7vs7", precio_hora=90000),
            Cancha(nombre="Cancha 3", tipo="Futbol 6vs6(sintetico)", precio_hora=90000),
            Cancha(nombre="Cancha 4", tipo="Futbol 6vs6(Cacha VIP)", precio_hora=140000),
        ]
        session.add_all(canchas)
        session.commit()
        print("✅ Datos de ejemplo insertados")
    
    session.close()

if __name__ == "__main__":
    init_db()
    insertar_datos_ejemplo()