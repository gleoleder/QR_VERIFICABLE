"""
models.py - Esquema de base de datos para el sistema de certificados

Este módulo define las tablas de la base de datos:
- certificates: Almacena metadatos de certificados (NUNCA PDFs)
- audit_logs: Registra cada verificación para auditoría
- revoked_tokens: Tokens revocados (opcional, para invalidación)

Autor: Sistema de Certificados QR
Fecha: 2026
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()


class Certificate(db.Model):
    """
    Tabla de certificados.
    
    Almacena únicamente metadatos necesarios para verificación.
    Los PDFs se generan en memoria bajo demanda, nunca se persisten.
    
    Atributos:
        id (int): Primary key autoincremental
        token (str): UUID v4 único para verificación (indexed)
        participant_name (str): Nombre del participante (sanitizado)
        participant_id (str): Identificador interno (DNI, código, etc.)
        course_name (str): Nombre del curso/certificación
        course_hours (int): Duración del curso en horas
        institution (str): Nombre de la institución emisora
        issue_date (datetime): Fecha de emisión
        expiry_date (datetime): Fecha de expiración (nullable)
        hmac_signature (str): Firma HMAC-SHA256 para integridad
        status (str): active | revoked | expired
        created_at (datetime): Timestamp de creación
        updated_at (datetime): Timestamp de última actualización
    """
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(36), unique=True, nullable=False, index=True)
    participant_name = db.Column(db.String(200), nullable=False)
    participant_id = db.Column(db.String(50), nullable=True)  # Opcional, para privacidad
    course_name = db.Column(db.String(200), nullable=False)
    course_hours = db.Column(db.Integer, nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=True)
    hmac_signature = db.Column(db.String(64), nullable=False)  # SHA256 = 64 hex chars
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relación con audit logs
    audit_logs = db.relationship('AuditLog', backref='certificate', lazy='dynamic')
    
    def __repr__(self):
        return f'<Certificate token={self.token}, status={self.status}>'
    
    def to_dict(self):
        """
        Convierte el certificado a diccionario para JSON.
        Excluye datos sensibles y campos internos.
        """
        return {
            'token': self.token,
            'participant_name': self.participant_name,
            'course_name': self.course_name,
            'course_hours': self.course_hours,
            'institution': self.institution,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status,
            'verification_url': f'{self.institution}/verify/{self.token}'
        }
    
    @classmethod
    def generate_token(cls):
        """Genera un UUID v4 único para el certificado."""
        return str(uuid.uuid4())
    
    def is_valid(self):
        """
        Verifica si el certificado es válido para emisión de PDF.
        
        Returns:
            bool: True si está activo y no expirado
        """
        if self.status != 'active':
            return False
        
        if self.expiry_date and datetime.utcnow() > self.expiry_date:
            return False
        
        return True


class AuditLog(db.Model):
    """
    Tabla de auditoría de verificaciones.
    
    Registra cada acceso al endpoint /verify para:
    - Detección de fraudes
    - Análisis de uso
    - Cumplimiento normativo
    
    Atributos:
        id (int): Primary key
        certificate_id (int): Foreign key a certificates
        token (str): Token verificado (para queries rápidas)
        ip_address (str): IP del solicitante (truncada para privacidad)
        user_agent (str): User-Agent del navegador
        verified_at (datetime): Timestamp de verificación
        success (bool): Si la verificación fue exitosa
        failure_reason (str): Motivo del fallo (si aplica)
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id'), nullable=False)
    token = db.Column(db.String(36), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 max length
    user_agent = db.Column(db.String(500), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    success = db.Column(db.Boolean, nullable=False, default=True)
    failure_reason = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<AuditLog token={self.token}, success={self.success}, at={self.verified_at}>'
    
    def to_dict(self):
        """Convierte el log a diccionario para reporting."""
        return {
            'id': self.id,
            'certificate_id': self.certificate_id,
            'token': self.token,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'success': self.success,
            'failure_reason': self.failure_reason
        }


class RevokedToken(db.Model):
    """
    Tabla opcional para tokens revocados.
    
    Útil cuando se necesita invalidar certificados antes de su expiración.
    En producción con PostgreSQL, considerar usar tabla particionada por fecha.
    
    Atributos:
        id (int): Primary key
        token (str): Token revocado
        revoked_at (datetime): Fecha de revocación
        reason (str): Motivo de revocación
        revoked_by (str): Usuario/sistema que revocó
    """
    __tablename__ = 'revoked_tokens'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(36), unique=True, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reason = db.Column(db.String(200), nullable=True)
    revoked_by = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<RevokedToken token={self.token}>'


def init_db(app):
    """
    Inicializa la base de datos con la aplicación Flask.
    
    Args:
        app: Aplicación Flask configurada
    
    Este método:
    1. Vincula SQLAlchemy con la app
    2. Crea todas las tablas definidas
    3. Crea índices adicionales si son necesarios
    """
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Crear índices adicionales para performance
        from sqlalchemy import text
        
        # Índice compuesto para búsquedas frecuentes
        try:
            db.session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_certificates_status_token "
                "ON certificates(status, token)"
            ))
            db.session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_verified_at "
                "ON audit_logs(verified_at DESC)"
            ))
            db.session.commit()
        except Exception as e:
            # Algunos backends no soportan CREATE INDEX IF NOT EXISTS
            db.session.rollback()
            app.logger.warning(f"No se pudieron crear índices adicionales: {e}")
