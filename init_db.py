"""
init_db.py - Script de inicialización de base de datos

Este script crea las tablas necesarias y opcionalmente
inserta datos de prueba para desarrollo.

Uso:
    python init_db.py              # Solo crear tablas
    python init_db.py --seed       # Crear tablas + datos de prueba

Autor: Sistema de Certificados QR
Fecha: 2026
"""

import sys
import os
from datetime import datetime, timedelta

# Añadir directorio padre al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from app import app, db
from models import Certificate, AuditLog
from utils import generate_hmac_signature

# Cargar variables de entorno
load_dotenv()


def init_database():
    """
    Inicializa la base de datos creando todas las tablas.
    """
    print("=" * 60)
    print("INICIALIZACIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("✓ Tablas creadas exitosamente")
        
        # Verificar tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\nTablas creadas: {', '.join(tables)}")
        print("\n✓ Base de datos inicializada correctamente")
    
    return True


def seed_data():
    """
    Inserta datos de prueba para desarrollo.
    """
    print("\n" + "=" * 60)
    print("INSERTANDO DATOS DE PRUEBA")
    print("=" * 60)
    
    with app.app_context():
        # Verificar si ya hay datos
        existing_count = Certificate.query.count()
        
        if existing_count > 0:
            print(f"\n⚠ La base de datos ya tiene {existing_count} certificados")
            response = input("¿Desea continuar e insertar datos de prueba? (y/n): ")
            if response.lower() != 'y':
                print("Operación cancelada")
                return
        
        # Datos de prueba
        test_certificates = [
            {
                'participant_name': 'Juan Pérez García',
                'participant_id': '12345678',
                'course_name': 'Python Avanzado y Flask',
                'course_hours': 40,
                'institution': 'Universidad Tecnológica'
            },
            {
                'participant_name': 'María Rodríguez López',
                'participant_id': '87654321',
                'course_name': 'JavaScript Moderno ES6+',
                'course_hours': 32,
                'institution': 'Academia Digital'
            },
            {
                'participant_name': 'Carlos Mendoza Silva',
                'participant_id': '11223344',
                'course_name': 'Docker y Kubernetes',
                'course_hours': 24,
                'institution': 'Cloud Academy'
            },
            {
                'participant_name': 'Ana Patricia Torres',
                'participant_id': '44332211',
                'course_name': 'Machine Learning con Python',
                'course_hours': 60,
                'institution': 'AI Institute'
            },
            {
                'participant_name': 'Luis Fernando Castro',
                'participant_id': '55667788',
                'course_name': 'Desarrollo Web Full Stack',
                'course_hours': 80,
                'institution': 'Universidad Tecnológica'
            }
        ]
        
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        
        for i, cert_data in enumerate(test_certificates, 1):
            # Generar token único
            token = Certificate.generate_token()
            
            # Fechas escalonadas para prueba
            issue_date = datetime.utcnow() - timedelta(days=i * 5)
            
            # Calcular expiración (si está configurada)
            expiry_days = int(os.getenv('CERTIFICATE_EXPIRY_DAYS', '0'))
            expiry_date = None
            if expiry_days > 0:
                expiry_date = issue_date + timedelta(days=expiry_days)
            
            # Generar firma HMAC
            hmac_data = {
                'participant_name': cert_data['participant_name'],
                'course_name': cert_data['course_name'],
                'course_hours': cert_data['course_hours'],
                'institution': cert_data['institution'],
                'issue_date': issue_date.isoformat(),
                'token': token
            }
            hmac_signature = generate_hmac_signature(hmac_data)
            
            # Crear certificado
            certificate = Certificate(
                token=token,
                participant_name=cert_data['participant_name'],
                participant_id=cert_data['participant_id'],
                course_name=cert_data['course_name'],
                course_hours=cert_data['course_hours'],
                institution=cert_data['institution'],
                issue_date=issue_date,
                expiry_date=expiry_date,
                hmac_signature=hmac_signature,
                status='active'
            )
            
            db.session.add(certificate)
            
            print(f"  ✓ Certificado {i}: {cert_data['participant_name']} - {cert_data['course_name']}")
            print(f"    Token: {token[:8]}...{token[-4:]}")
            print(f"    URL: {base_url}/verify/{token}")
        
        # Guardar cambios
        db.session.commit()
        
        print(f"\n✓ {len(test_certificates)} certificados de prueba insertados")
        
        # Mostrar resumen
        total = Certificate.query.count()
        active = Certificate.query.filter_by(status='active').count()
        
        print(f"\n{'=' * 60}")
        print("RESUMEN")
        print("=" * 60)
        print(f"Total certificados: {total}")
        print(f"Activos: {active}")
        print(f"\nURLs de prueba:")
        
        for cert in Certificate.query.limit(3).all():
            print(f"  - {base_url}/verify/{cert.token}")


def main():
    """
    Función principal.
    """
    # Determinar modo de operación
    seed_mode = '--seed' in sys.argv or '-s' in sys.argv
    
    # Inicializar base de datos
    if not init_database():
        print("\n✗ Error al inicializar la base de datos")
        sys.exit(1)
    
    # Insertar datos de prueba si se solicitó
    if seed_mode:
        seed_data()
    
    print("\n" + "=" * 60)
    print("¡LISTO!")
    print("=" * 60)
    print("\nPara iniciar el servidor:")
    print("  python app.py")
    print("\nPara pruebas con datos de ejemplo:")
    print("  python init_db.py --seed")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
