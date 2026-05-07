"""
utils.py - Utilidades de seguridad, criptografía y generación de QR

Este módulo contiene:
- Generación y verificación de firmas HMAC-SHA256
- Generación de códigos QR en base64
- Sanitización de inputs
- Funciones de auditoría

Autor: Sistema de Certificados QR
Fecha: 2026
"""

import hmac
import hashlib
import base64
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from io import BytesIO

import qrcode
from PIL import Image
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Clave secreta para HMAC (debe estar en .env)
HMAC_SECRET = os.getenv('HMAC_SECRET_KEY')

if not HMAC_SECRET:
    raise ValueError(
        "HMAC_SECRET_KEY no configurada en .env o variables de entorno. "
        "Ejecutar: python -c \"import secrets; print(secrets.token_hex(32))\""
    )


def generate_hmac_signature(data: dict) -> str:
    """
    Genera firma HMAC-SHA256 para los datos del certificado.
    
    La firma se calcula sobre los datos críticos del certificado
    para garantizar integridad y detectar manipulaciones.
    
    Args:
        data: Diccionario con datos del certificado:
            - participant_name: Nombre del participante
            - course_name: Nombre del curso
            - course_hours: Horas del curso
            - institution: Institución emisora
            - issue_date: Fecha de emisión (ISO format)
            - token: Token único del certificado
    
    Returns:
        str: Firma HMAC en hexadecimal (64 caracteres)
    
    Example:
        >>> data = {
        ...     'participant_name': 'Juan Pérez',
        ...     'course_name': 'Python Avanzado',
        ...     'course_hours': 40,
        ...     'institution': 'Universidad XYZ',
        ...     'issue_date': '2026-05-07',
        ...     'token': 'abc-123-def'
        ... }
        >>> signature = generate_hmac_signature(data)
        >>> len(signature)
        64
    """
    # Crear string canónico para hashing consistente
    # El orden de las claves es importante para reproducibilidad
    canonical_string = '|'.join([
        str(data.get('participant_name', '')),
        str(data.get('course_name', '')),
        str(data.get('course_hours', 0)),
        str(data.get('institution', '')),
        str(data.get('issue_date', '')),
        str(data.get('token', ''))
    ])
    
    # Generar HMAC-SHA256
    signature = hmac.new(
        HMAC_SECRET.encode('utf-8'),
        canonical_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_hmac_signature(data: dict, provided_signature: str) -> bool:
    """
    Verifica la firma HMAC de un certificado.
    
    Usa hmac.compare_digest() para comparación segura contra
    ataques de timing side-channel.
    
    Args:
        data: Datos del certificado (mismo formato que generate_hmac_signature)
        provided_signature: Firma proporcionada por el certificado
    
    Returns:
        bool: True si la firma es válida, False en caso contrario
    
    Security:
        - Constant-time comparison para prevenir timing attacks
        - No revela información sobre la firma esperada
    """
    expected_signature = generate_hmac_signature(data)
    
    # Comparación segura contra timing attacks
    return hmac.compare_digest(expected_signature, provided_signature)


def generate_qr_code(
    url: str, 
    size: int = 300, 
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white"
) -> str:
    """
    Genera código QR en formato base64 para embebido en HTML/PDF.
    
    Args:
        url: URL o datos a codificar en el QR
        size: Tamaño en píxeles (ancho/alto)
        border: Grosor del borde en módulos (mínimo 4 para estándar QR)
        fill_color: Color de los módulos (hex, nombre CSS, o RGB tuple)
        back_color: Color de fondo
    
    Returns:
        str: Imagen QR codificada en base64 (data URI para HTML)
    
    Example:
        >>> qr_base64 = generate_qr_code("https://ejemplo.com/verify/abc123")
        >>> qr_base64[:50]
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAYAAAB5...'
    """
    # Crear objeto QR con configuración optimizada
    qr = qrcode.QRCode(
        version=1,  # Auto-ajustar según tamaño de datos
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # 15% recuperación de errores
        box_size=size // 25,  # Escalar según tamaño solicitado
        border=border,
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    # Generar imagen
    img = qr.make_image(
        fill_color=fill_color,
        back_color=back_color
    )
    
    # Redimensionar a tamaño exacto
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Guardar en buffer de memoria
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    
    # Codificar a base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Retornar como data URI para uso directo en HTML
    return f"data:image/png;base64,{img_base64}"


def generate_qr_bytes(url: str, size: int = 300) -> BytesIO:
    """
    Genera código QR como BytesIO para embebido directo en PDF.
    
    Args:
        url: URL o datos a codificar
        size: Tamaño en píxeles
    
    Returns:
        BytesIO: Buffer con imagen PNG lista para usar con reportlab
    
    Note:
        Esta función evita la codificación base64 para eficiencia
        cuando se usa directamente en generación de PDF.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size // 25,
        border=4,
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)  # Resetear puntero al inicio
    
    return buffer


def sanitize_input(text: str, max_length: int = 200) -> str:
    """
    Sanitiza input de usuario para prevenir XSS e inyecciones.
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
    
    Returns:
        str: Texto sanitizado
    
    Security:
        - Elimina tags HTML
        - Escapa caracteres especiales
        - Limita longitud para prevenir DoS
        - Normaliza whitespace
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Truncar a longitud máxima
    text = text[:max_length]
    
    # Eliminar tags HTML (<, >)
    text = re.sub(r'<[^>]*>', '', text)
    
    # Escapar caracteres especiales para HTML
    text = text.replace('&', '&amp;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Normalizar whitespace múltiple
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def truncate_ip(ip_address: str) -> str:
    """
    Trunca dirección IP para privacidad (GDPR compliance).
    
    Args:
        ip_address: IP completa (IPv4 o IPv6)
    
    Returns:
        str: IP truncada (último octeto removido para IPv4)
    
    Example:
        >>> truncate_ip("192.168.1.100")
        '192.168.1.0'
        >>> truncate_ip("2001:db8::1")
        '2001:db8::0'
    """
    if not ip_address:
        return "0.0.0.0"
    
    # IPv4
    if '.' in ip_address:
        parts = ip_address.rsplit('.', 1)
        return f"{parts[0]}.0"
    
    # IPv6
    if ':' in ip_address:
        parts = ip_address.rsplit(':', 1)
        return f"{parts[0]}:0"
    
    return ip_address


def calculate_expiry_date(
    issue_date: datetime, 
    expiry_days: int
) -> Optional[datetime]:
    """
    Calcula fecha de expiración del certificado.
    
    Args:
        issue_date: Fecha de emisión
        expiry_days: Días de validez (0 = sin expiración)
    
    Returns:
        datetime: Fecha de expiración o None si no expira
    """
    if expiry_days <= 0:
        return None
    
    return issue_date + timedelta(days=expiry_days)


def get_client_ip(request) -> str:
    """
    Obtiene IP real del cliente considerando proxies/load balancers.
    
    Args:
        request: Objeto request de Flask
    
    Returns:
        str: Dirección IP del cliente
    """
    # Verificar headers de proxy (Cloudflare, Nginx, etc.)
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For puede tener múltiples IPs: cliente, proxy1, proxy2...
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    
    # Fallback a IP directa
    return request.remote_addr or "0.0.0.0"


def validate_certificate_data(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Valida datos de certificado antes de emisión.
    
    Args:
        data: Diccionario con datos del certificado
    
    Returns:
        Tuple[bool, Optional[str]]: (es_válido, mensaje_de_error)
    """
    # Campos requeridos
    required_fields = ['participant_name', 'course_name', 'course_hours', 'institution']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Campo requerido faltante: {field}"
    
    # Validar tipos
    if not isinstance(data.get('participant_name'), str):
        return False, "participant_name debe ser string"
    
    if not isinstance(data.get('course_name'), str):
        return False, "course_name debe ser string"
    
    if not isinstance(data.get('course_hours'), int) or data['course_hours'] <= 0:
        return False, "course_hours debe ser entero positivo"
    
    if not isinstance(data.get('institution'), str):
        return False, "institution debe ser string"
    
    # Validar longitudes
    if len(data['participant_name']) > 200:
        return False, "participant_name excede 200 caracteres"
    
    if len(data['course_name']) > 200:
        return False, "course_name excede 200 caracteres"
    
    if len(data['institution']) > 200:
        return False, "institution excede 200 caracteres"
    
    # Validar course_hours razonable (1-10000 horas)
    if data['course_hours'] < 1 or data['course_hours'] > 10000:
        return False, "course_hours debe estar entre 1 y 10000"
    
    return True, None
