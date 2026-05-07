"""
app.py - Aplicación principal del sistema de certificados QR

Endpoints:
    POST /issue      - Emitir nuevo certificado
    GET  /verify/<token> - Verificar y descargar certificado PDF
    PUT  /revoke/<token> - Revocar certificado
    GET  /health     - Health check
    GET  /           - Página de verificación web

Autor: Sistema de Certificados QR
Fecha: 2026
"""

import os
import logging
from datetime import datetime
from functools import wraps

from flask import (
    Flask, 
    request, 
    jsonify, 
    send_file, 
    render_template,
    make_response
)
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import db, Certificate, AuditLog, init_db
from utils import (
    generate_hmac_signature,
    verify_hmac_signature,
    generate_qr_code,
    generate_qr_bytes,
    sanitize_input,
    truncate_ip,
    get_client_ip,
    validate_certificate_data,
    calculate_expiry_date
)
from generador_pdf import (
    generate_certificate_pdf,
    get_pdf_content_type,
    get_pdf_filename
)

# ==========================================
# CARGAR CONFIGURACIÓN
# ==========================================

load_dotenv()

app = Flask(__name__)

# Configuración desde variables de entorno
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'sqlite:///certificados.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request

# Configuración de certificados
app.config['CERTIFICATE_EXPIRY_DAYS'] = int(os.getenv('CERTIFICATE_EXPIRY_DAYS', '0'))
app.config['INSTITUTION_NAME'] = os.getenv('INSTITUTION_NAME', 'Institución')

# ==========================================
# LOGGING
# ==========================================

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# RATE LIMITING
# ==========================================

rate_limit = int(os.getenv('RATE_LIMIT_PER_MINUTE', '10'))

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# ==========================================
# INICIALIZAR BASE DE DATOS
# ==========================================

init_db(app)

# ==========================================
# MIDDLEWARE DE SEGURIDAD
# ==========================================

@app.after_request
def add_security_headers(response):
    """
    Añade headers de seguridad HTTP a todas las respuestas.
    
    Headers incluidos:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Cache-Control: no-store (para respuestas con datos sensibles)
    - Strict-Transport-Security: max-age=31536000 (solo en prod)
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # HSTS solo en producción con HTTPS
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )
    
    return response

# ==========================================
# MODELO DE AUDITORÍA
# ==========================================

def log_verification(
    token: str, 
    certificate_id: int, 
    success: bool, 
    failure_reason: str = None
):
    """
    Registra intento de verificación en audit_logs.
    
    Args:
        token: Token verificado
        certificate_id: ID del certificado en BD
        success: Si la verificación fue exitosa
        failure_reason: Motivo del fallo (si aplica)
    """
    try:
        ip_address = truncate_ip(get_client_ip(request))
        user_agent = request.headers.get('User-Agent', '')[:500]
        
        audit_log = AuditLog(
            token=token,
            certificate_id=certificate_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
        logger.info(
            f"Audit: token={token[:8]}... success={success} ip={ip_address}"
        )
        
    except Exception as e:
        logger.error(f"Error al registrar audit log: {e}")
        db.session.rollback()

# ==========================================
# ENDPOINT: HEALTH CHECK
# ==========================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint para monitoreo.
    
    Returns:
        JSON: Estado del servicio
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'certificados-qr',
        'version': '1.0.0'
    }), 200

# ==========================================
# ENDPOINT: EMITIR CERTIFICADO
# ==========================================

@app.route('/issue', methods=['POST'])
@limiter.limit("20 per minute")
def issue_certificate():
    """
    Emite un nuevo certificado.
    
    Request Body (JSON):
        {
            "participant_name": "Juan Pérez",
            "participant_id": "12345678",  # Opcional
            "course_name": "Python Avanzado",
            "course_hours": 40,
            "institution": "Universidad XYZ"
        }
    
    Response (JSON):
        {
            "success": true,
            "token": "uuid-v4-token",
            "verification_url": "https://dominio.com/verify/uuid-v4-token",
            "qr_code": "data:image/png;base64,...",
            "certificate_id": 123
        }
    
    Security:
        - Rate limiting: 20 requests/minuto
        - Validación de inputs
        - Sanitización de datos
        - Firma HMAC-SHA256
    """
    try:
        # Validar Content-Type
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type debe ser application/json'
            }), 400
        
        data = request.get_json()
        
        # Validar datos requeridos
        is_valid, error_msg = validate_certificate_data(data)
        if not is_valid:
            logger.warning(f"Datos inválidos: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Sanitizar inputs
        participant_name = sanitize_input(data['participant_name'])
        participant_id = sanitize_input(data.get('participant_id', ''), max_length=50)
        course_name = sanitize_input(data['course_name'])
        institution = sanitize_input(data['institution'])
        course_hours = int(data['course_hours'])
        
        # Generar token único
        token = Certificate.generate_token()
        
        # Calcular fecha de emisión y expiración
        issue_date = datetime.utcnow()
        expiry_days = app.config['CERTIFICATE_EXPIRY_DAYS']
        expiry_date = calculate_expiry_date(issue_date, expiry_days)
        
        # Generar firma HMAC
        hmac_data = {
            'participant_name': participant_name,
            'course_name': course_name,
            'course_hours': course_hours,
            'institution': institution,
            'issue_date': issue_date.isoformat(),
            'token': token
        }
        hmac_signature = generate_hmac_signature(hmac_data)
        
        # Guardar en base de datos
        certificate = Certificate(
            token=token,
            participant_name=participant_name,
            participant_id=participant_id if participant_id else None,
            course_name=course_name,
            course_hours=course_hours,
            institution=institution,
            issue_date=issue_date,
            expiry_date=expiry_date,
            hmac_signature=hmac_signature,
            status='active'
        )
        
        db.session.add(certificate)
        db.session.commit()
        
        # Generar URL de verificación
        base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
        verification_url = f"{base_url}/verify/{token}"
        
        # Generar QR
        qr_code = generate_qr_code(verification_url)
        
        logger.info(f"Certificado emitido: token={token[:8]}... participant={participant_name}")
        
        return jsonify({
            'success': True,
            'token': token,
            'verification_url': verification_url,
            'qr_code': qr_code,
            'certificate_id': certificate.id,
            'hmac_signature': hmac_signature
        }), 201
        
    except Exception as e:
        logger.error(f"Error al emitir certificado: {e}")
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

# ==========================================
# ENDPOINT: VERIFICAR CERTIFICADO
# ==========================================

@app.route('/verify/<token>', methods=['GET'])
@limiter.limit("10 per minute")
def verify_certificate(token):
    """
    Verifica un certificado y genera PDF para descarga.
    
    Valida:
    1. Existencia del token en BD
    2. Estado del certificado (active, no revocado)
    3. Fecha de expiración
    4. Integridad de datos (HMAC)
    
    Si es válido:
    - Genera PDF en memoria
    - Registra auditoría
    - Fuerza descarga con Content-Disposition: attachment
    
    Si es inválido:
    - Registra auditoría con motivo
    - Retorna 403/404 según corresponda
    """
    try:
        # Buscar certificado por token
        certificate = Certificate.query.filter_by(token=token).first()
        
        if not certificate:
            logger.warning(f"Token no encontrado: {token[:8]}...")
            log_verification(token, 0, False, 'token_not_found')
            
            # Renderizar página de error para navegador
            if request.headers.get('Accept', '').find('text/html') >= 0:
                return render_template(
                    'verify_error.html',
                    error='Certificado no encontrado',
                    message='El token proporcionado no existe en nuestro sistema.'
                ), 404
            
            return jsonify({
                'success': False,
                'error': 'Certificado no encontrado'
            }), 404
        
        # Verificar estado
        if certificate.status == 'revoked':
            logger.warning(f"Token revocado: {token[:8]}...")
            log_verification(token, certificate.id, False, 'revoked')
            
            if request.headers.get('Accept', '').find('text/html') >= 0:
                return render_template(
                    'verify_error.html',
                    error='Certificado revocado',
                    message='Este certificado ha sido revocado por la institución emisora.'
                ), 403
            
            return jsonify({
                'success': False,
                'error': 'Certificado revocado'
            }), 403
        
        # Verificar expiración
        if certificate.expiry_date and datetime.utcnow() > certificate.expiry_date:
            logger.warning(f"Token expirado: {token[:8]}...")
            log_verification(token, certificate.id, False, 'expired')
            
            # Actualizar estado
            certificate.status = 'expired'
            db.session.commit()
            
            if request.headers.get('Accept', '').find('text/html') >= 0:
                return render_template(
                    'verify_error.html',
                    error='Certificado expirado',
                    message=f'Este certificado expiró el {certificate.expiry_date.strftime("%d/%m/%Y")}.'
                ), 403
            
            return jsonify({
                'success': False,
                'error': 'Certificado expirado'
            }), 403
        
        # Verificar integridad HMAC
        hmac_data = {
            'participant_name': certificate.participant_name,
            'course_name': certificate.course_name,
            'course_hours': certificate.course_hours,
            'institution': certificate.institution,
            'issue_date': certificate.issue_date.isoformat(),
            'token': certificate.token
        }
        
        if not verify_hmac_signature(hmac_data, certificate.hmac_signature):
            logger.error(f"Firma HMAC inválida: {token[:8]}...")
            log_verification(token, certificate.id, False, 'invalid_hmac')
            
            if request.headers.get('Accept', '').find('text/html') >= 0:
                return render_template(
                    'verify_error.html',
                    error='Certificado inválido',
                    message='La firma de integridad no coincide. Este certificado puede haber sido alterado.'
                ), 403
            
            return jsonify({
                'success': False,
                'error': 'Firma de integridad inválida'
            }), 403
        
        # ==========================================
        # CERTIFICADO VÁLIDO - GENERAR PDF
        # ==========================================
        
        # Generar QR para el PDF
        base_url = os.getenv('BASE_URL', request.host_url.rstrip('/'))
        verification_url = f"{base_url}/verify/{token}"
        qr_bytes = generate_qr_bytes(verification_url)
        
        # Generar PDF en memoria
        pdf_buffer = generate_certificate_pdf(
            participant_name=certificate.participant_name,
            course_name=certificate.course_name,
            course_hours=certificate.course_hours,
            institution=certificate.institution,
            issue_date=certificate.issue_date,
            token=certificate.token,
            hmac_signature=certificate.hmac_signature,
            qr_image_data=qr_bytes,
            expiry_date=certificate.expiry_date
        )
        
        # Registrar auditoría (éxito)
        log_verification(token, certificate.id, True)
        
        # Preparar respuesta con descarga forzada
        filename = get_pdf_filename(
            certificate.participant_name,
            certificate.course_name,
            certificate.token
        )
        
        response = make_response(send_file(
            pdf_buffer,
            mimetype=get_pdf_content_type(),
            as_attachment=True,
            download_name=filename
        ))
        
        # Headers para forzar descarga y prevenir cache
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        
        logger.info(f"Certificado verificado y descargado: {token[:8]}...")
        
        return response
        
    except Exception as e:
        logger.error(f"Error en verificación: {e}")
        
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

# ==========================================
# ENDPOINT: REVOCAR CERTIFICADO
# ==========================================

@app.route('/revoke/<token>', methods=['PUT'])
@limiter.limit("5 per minute")
def revoke_certificate(token):
    """
    Revoca un certificado activo.
    
    Requiere autorización (implementar según necesidades).
    Útil para:
    - Certificados emitidos por error
    - Suspensión de validez por entidades
    - Corrección de datos
    
    Request Body (JSON):
        {
            "reason": "Emisión duplicada",
            "revoked_by": "admin@institution.com"
        }
    """
    try:
        # TODO: Implementar autenticación/autorización
        # Esto es crítico en producción
        
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type debe ser application/json'
            }), 400
        
        data = request.get_json()
        reason = sanitize_input(data.get('reason', 'Sin motivo especificado'), max_length=200)
        revoked_by = sanitize_input(data.get('revoked_by', 'system'), max_length=100)
        
        # Buscar certificado
        certificate = Certificate.query.filter_by(token=token).first()
        
        if not certificate:
            return jsonify({
                'success': False,
                'error': 'Certificado no encontrado'
            }), 404
        
        if certificate.status == 'revoked':
            return jsonify({
                'success': False,
                'error': 'Certificado ya está revocado'
            }), 400
        
        # Revocar
        certificate.status = 'revoked'
        db.session.commit()
        
        # Registrar en revoked_tokens (opcional, para historial)
        # from models import RevokedToken
        # revoked = RevokedToken(
        #     token=token,
        #     reason=reason,
        #     revoked_by=revoked_by
        # )
        # db.session.add(revoked)
        # db.session.commit()
        
        logger.warning(f"Certificado revocado: {token[:8]}... reason={reason}")
        
        return jsonify({
            'success': True,
            'message': 'Certificado revocado exitosamente',
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Error al revocar certificado: {e}")
        db.session.rollback()
        
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

# ==========================================
# ENDPOINT: PÁGINA WEB DE VERIFICACIÓN
# ==========================================

@app.route('/', methods=['GET'])
def index():
    """
    Página web para verificación manual de certificados.
    
    Permite a usuarios ingresar un token manualmente
    y ver el estado del certificado en el navegador.
    """
    return render_template('index.html')

# ==========================================
# MANEJADORES DE ERROR
# ==========================================

@app.errorhandler(429)
def ratelimit_handler(e):
    """Manejador de rate limit excedido."""
    return jsonify({
        'success': False,
        'error': 'Demasiadas solicitudes. Por favor espere antes de intentar nuevamente.'
    }), 429

@app.errorhandler(500)
def internal_error(e):
    """Manejador de error interno."""
    logger.error(f"Error interno: {e}")
    return jsonify({
        'success': False,
        'error': 'Error interno del servidor'
    }), 500

@app.errorhandler(404)
def not_found(e):
    """Manejador de recurso no encontrado."""
    return jsonify({
        'success': False,
        'error': 'Recurso no encontrado'
    }), 404

# ==========================================
# MAIN
# ==========================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Iniciando servidor en http://{host}:{port}")
    logger.info(f"Entorno: {os.getenv('FLASK_ENV', 'production')}")
    
    app.run(host=host, port=port, debug=debug)
