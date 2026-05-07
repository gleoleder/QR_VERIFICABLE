"""
generador_pdf.py - Generación de certificados PDF en memoria

Este módulo genera certificados PDF profesionalmente diseñados
sin almacenar archivos en disco. Todo se procesa en memoria
usando io.BytesIO.

Características:
- Diseño profesional con encabezado, cuerpo y pie de página
- QR embebido en el PDF
- Firma HMAC visible para verificación manual
- Optimizado para impresión en carta/A4

Autor: Sistema de Certificados QR
Fecha: 2026
"""

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, 
    Paragraph, 
    Spacer, 
    Image, 
    Table, 
    TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


def generate_certificate_pdf(
    participant_name: str,
    course_name: str,
    course_hours: int,
    institution: str,
    issue_date: datetime,
    token: str,
    hmac_signature: str,
    qr_image_data: io.BytesIO,
    expiry_date: Optional[datetime] = None
) -> io.BytesIO:
    """
    Genera certificado PDF en memoria.
    
    Args:
        participant_name: Nombre del participante
        course_name: Nombre del curso
        course_hours: Duración en horas
        institution: Institución emisora
        issue_date: Fecha de emisión
        token: Token único de verificación
        hmac_signature: Firma HMAC del certificado
        qr_image_data: BytesIO con imagen QR
        expiry_date: Fecha de expiración (opcional)
    
    Returns:
        io.BytesIO: Buffer con PDF generado listo para envío
    
    Note:
        El PDF se genera completamente en memoria. No se escribe
        nada al sistema de archivos.
    """
    # Crear buffer en memoria
    buffer = io.BytesIO()
    
    # Configurar documento horizontal (mejor para certificados)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"Certificado - {participant_name} - {course_name}"
    )
    
    # Contenedores de elementos
    elements = []
    styles = getSampleStyleSheet()
    
    # ==========================================
    # ESTILOS PERSONALIZADOS
    # ==========================================
    
    # Título principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Subtítulo
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#16213e'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # Texto normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # Nombre del participante (destacado)
    name_style = ParagraphStyle(
        'ParticipantName',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=25,
        spaceBefore=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Curso
    course_style = ParagraphStyle(
        'CourseName',
        parent=styles['Heading2'],
        fontSize=20,
        textColor=colors.HexColor('#e94560'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-BoldOblique'
    )
    
    # Texto pequeño (footer, hash)
    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # ==========================================
    # CONTENIDO DEL CERTIFICADO
    # ==========================================
    
    # Encabezado decorativo (línea superior)
    header_line = Table([[' ' * 100]], colWidths=[6.5 * inch])
    header_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#e94560')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#1a1a2e')),
    ]))
    elements.append(header_line)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Título
    elements.append(Paragraph("CERTIFICADO DE APROBACIÓN", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Subtítulo
    elements.append(Paragraph(institution, subtitle_style))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Texto introductorio
    elements.append(Paragraph(
        "Por medio del presente se certifica que:",
        normal_style
    ))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Nombre del participante
    elements.append(Paragraph(participant_name, name_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Texto de aprobación
    elements.append(Paragraph(
        "Ha completado satisfactoriamente el curso:",
        normal_style
    ))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Nombre del curso
    elements.append(Paragraph(course_name, course_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Horas y fecha
    details_text = f"Con una duración total de <b>{course_hours} horas</b> académicas"
    if expiry_date:
        expiry_str = expiry_date.strftime('%d de %B de %Y')
        details_text += f"<br/>Válido hasta: {expiry_str}"
    
    elements.append(Paragraph(details_text, normal_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Fecha de emisión
    issue_str = issue_date.strftime('%d de %B de %Y')
    elements.append(Paragraph(
        f"Emitido en {issue_str}",
        normal_style
    ))
    elements.append(Spacer(1, 0.5 * inch))
    
    # ==========================================
    # TABLA CON QR Y FIRMAS
    # ==========================================
    
    # Guardar QR como imagen temporal para reportlab
    qr_image_data.seek(0)
    qr_img = Image(qr_image_data, width=1.5 * inch, height=1.5 * inch)
    
    # Token corto para mostrar (primeros 8 caracteres)
    short_token = token[:8] + '...' + token[-4:]
    
    # Tabla de firmas y QR
    signature_table = Table(
        [
            [qr_img, ' ' * 30, ' ' * 30],
            [
                Paragraph("<b>Código de Verificación</b><br/>" + short_token, small_style),
                Paragraph("<b>Firma Autorizada</b><br/>" + "_" * 25, small_style),
                Paragraph("<b>Sello Institucional</b><br/>" + "_" * 25, small_style)
            ]
        ],
        colWidths=[2 * inch, 2 * inch, 2 * inch]
    )
    
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(signature_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # ==========================================
    # INFORMACIÓN DE VERIFICACIÓN
    # ==========================================
    
    elements.append(Paragraph(
        "<b>Verificación de Autenticidad:</b><br/>"
        "Escanee el código QR o visite el portal de verificación<br/>"
        "Este certificado incluye firma digital HMAC-SHA256",
        small_style
    ))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Hash truncado para referencia visual
    truncated_hmac = hmac_signature[:16] + '...' + hmac_signature[-8:]
    elements.append(Paragraph(
        f"Hash de integridad: {truncated_hmac}",
        small_style
    ))
    
    # Línea inferior decorativa
    elements.append(Spacer(1, 0.3 * inch))
    footer_line = Table([[' ' * 100]], colWidths=[6.5 * inch])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#1a1a2e')),
        ('LINEBELOW', (0, 0), (-1, 0), 3, colors.HexColor('#e94560')),
    ]))
    elements.append(footer_line)
    
    # ==========================================
    # GENERAR PDF
    # ==========================================
    
    doc.build(elements)
    
    # Resetear buffer para lectura
    buffer.seek(0)
    
    return buffer


def generate_simple_certificate(
    participant_name: str,
    course_name: str,
    course_hours: int,
    institution: str,
    issue_date: datetime,
    token: str,
    qr_image_data: io.BytesIO
) -> io.BytesIO:
    """
    Genera certificado simplificado (una sola página, diseño minimalista).
    
    Útil para certificados de participación o cursos cortos.
    
    Args:
        participant_name: Nombre del participante
        course_name: Nombre del curso
        course_hours: Duración en horas
        institution: Institución emisora
        issue_date: Fecha de emisión
        token: Token de verificación
        qr_image_data: BytesIO con imagen QR
    
    Returns:
        io.BytesIO: Buffer con PDF generado
    """
    buffer = io.BytesIO()
    
    # Crear canvas directo para más control
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # ==========================================
    # BORDE DECORATIVO
    # ==========================================
    
    c.setStrokeColor(colors.HexColor('#0f3460'))
    c.setLineWidth(3)
    c.rect(0.5 * inch, 0.5 * inch, width - 1 * inch, height - 1 * inch)
    
    c.setStrokeColor(colors.HexColor('#e94560'))
    c.setLineWidth(1)
    c.rect(0.7 * inch, 0.7 * inch, width - 1.4 * inch, height - 1.4 * inch)
    
    # ==========================================
    # TÍTULO
    # ==========================================
    
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.HexColor('#1a1a2e'))
    c.drawCentredString(width / 2, height - 1.5 * inch, "CERTIFICADO")
    
    c.setFont("Helvetica-Oblique", 14)
    c.setFillColor(colors.HexColor('#16213e'))
    c.drawCentredString(width / 2, height - 1.9 * inch, institution)
    
    # ==========================================
    # CUERPO
    # ==========================================
    
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawCentredString(
        width / 2, 
        height - 2.5 * inch, 
        "Se certifica que:"
    )
    
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor('#0f3460'))
    c.drawCentredString(width / 2, height - 3 * inch, participant_name)
    
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawCentredString(
        width / 2, 
        height - 3.5 * inch, 
        "completó el curso:"
    )
    
    c.setFont("Helvetica-BoldOblique", 18)
    c.setFillColor(colors.HexColor('#e94560'))
    c.drawCentredString(width / 2, height - 3.9 * inch, course_name)
    
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawCentredString(
        width / 2, 
        height - 4.4 * inch, 
        f"Duración: {course_hours} horas"
    )
    
    # ==========================================
    # FECHA Y QR
    # ==========================================
    
    issue_str = issue_date.strftime('%d/%m/%Y')
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor('#666666'))
    c.drawCentredString(width / 2, height - 5 * inch, f"Emitido: {issue_str}")
    
    # QR
    qr_image_data.seek(0)
    qr_img = Image(qr_image_data, width=1.2 * inch, height=1.2 * inch)
    qr_img.drawOn(
        c, 
        width / 2 - 0.6 * inch, 
        height - 6.2 * inch
    )
    
    # Token
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor('#666666'))
    short_token = token[:8] + '...' + token[-4:]
    c.drawCentredString(width / 2, height - 6.6 * inch, f"ID: {short_token}")
    
    # Guardar PDF
    c.save()
    buffer.seek(0)
    
    return buffer


def get_pdf_content_type() -> str:
    """Retorna el Content-Type correcto para PDFs."""
    return 'application/pdf'


def get_pdf_filename(
    participant_name: str, 
    course_name: str, 
    token: str
) -> str:
    """
    Genera nombre de archivo seguro para descarga.
    
    Args:
        participant_name: Nombre del participante
        course_name: Nombre del curso
        token: Token del certificado
    
    Returns:
        str: Nombre de archivo sanitizado
    
    Example:
        >>> get_pdf_filename("Juan Pérez", "Python Básico", "abc-123")
        'Certificado_Juan_Perez_Python_Basico_abc123.pdf'
    """
    # Sanitizar nombres
    safe_name = participant_name.replace(' ', '_').replace('ñ', 'n')[:30]
    safe_course = course_name.replace(' ', '_')[:30]
    safe_token = token.replace('-', '')[:8]
    
    # Codificar caracteres especiales
    safe_name = safe_name.encode('ascii', 'ignore').decode('ascii')
    safe_course = safe_course.encode('ascii', 'ignore').decode('ascii')
    
    return f"Certificado_{safe_name}_{safe_course}_{safe_token}.pdf"
