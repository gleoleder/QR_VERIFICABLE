/**
 * Google Apps Script para Sistema de Certificados QR
 * 
 * Instrucciones de instalación:
 * 1. Crea un nuevo Google Sheet
 * 2. Ve a Extensiones > Apps Script
 * 3. Pega este código
 * 4. Cambia HMAC_SECRET por tu clave secreta
 * 5. Guarda y despliega como Web App (cualquiera puede acceder)
 * 6. Copia la URL del Web App y pégala en index.html
 */

// ==========================================
// CONFIGURACIÓN - CAMBIAR AQUÍ
// ==========================================
const HMAC_SECRET = 'tu_clave_secreta_muy_segura_cambiar_en_produccion';

// Nombre de la hoja de cálculo (debe llamarse así)
const SHEET_NAME = 'Certificados';

// ==========================================
// FUNCIONES PRINCIPALES
// ==========================================

function doGet(e) {
  const action = e.parameter.action;
  const token = e.parameter.token;
  
  if (action === 'verify' && token) {
    return verifyCertificate(token);
  } else if (action === 'pdf' && token) {
    return generatePDF(token);
  }
  
  return jsonResponse({ success: false, message: 'Parámetros inválidos' });
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const action = data.action;
    
    if (action === 'issue') {
      return issueCertificate(data.certificate);
    }
    
    return jsonResponse({ success: false, message: 'Acción no válida' });
  } catch (error) {
    return jsonResponse({ success: false, message: 'Error: ' + error.message });
  }
}

// ==========================================
// EMITIR CERTIFICADO
// ==========================================

function issueCertificate(cert) {
  try {
    // Validar campos requeridos
    if (!cert.token || !cert.participant_name || !cert.course_name || !cert.course_hours || !cert.institution) {
      return jsonResponse({ success: false, message: 'Faltan campos requeridos' });
    }
    
    // Validar firma HMAC
    const expectedHMAC = generateHMAC(cert);
    if (cert.hmac_signature !== expectedHMAC) {
      return jsonResponse({ success: false, message: 'Firma HMAC inválida' });
    }
    
    // Abrir hoja de cálculo
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);
    
    // Crear hoja si no existe
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME);
      // Encabezados
      sheet.appendRow([
        'token',
        'participant_name',
        'participant_id',
        'course_name',
        'course_hours',
        'institution',
        'issue_date',
        'hmac_signature',
        'status',
        'created_at'
      ]);
      // Congelar encabezado
      sheet.setFrozenRows(1);
    }
    
    // Verificar que el token no exista
    const existing = findCertificateByToken(sheet, cert.token);
    if (existing) {
      return jsonResponse({ success: false, message: 'El token ya existe' });
    }
    
    // Guardar certificado
    sheet.appendRow([
      cert.token,
      cert.participant_name,
      cert.participant_id || '',
      cert.course_name,
      cert.course_hours,
      cert.institution,
      cert.issue_date,
      cert.hmac_signature,
      'active',
      new Date().toISOString()
    ]);
    
    return jsonResponse({
      success: true,
      message: 'Certificado guardado exitosamente',
      token: cert.token
    });
    
  } catch (error) {
    return jsonResponse({ success: false, message: 'Error: ' + error.message });
  }
}

// ==========================================
// VERIFICAR CERTIFICADO
// ==========================================

function verifyCertificate(token) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(SHEET_NAME);
    
    if (!sheet) {
      return jsonResponse({ success: false, message: 'No hay certificados registrados' });
    }
    
    const cert = findCertificateByToken(sheet, token);
    
    if (!cert) {
      return jsonResponse({ success: false, message: 'Certificado no encontrado' });
    }
    
    // Verificar estado
    if (cert.status !== 'active') {
      return jsonResponse({ 
        success: false, 
        message: `Certificado ${cert.status}` 
      });
    }
    
    // Verificar firma HMAC
    const expectedHMAC = generateHMAC({
      participant_name: cert.participant_name,
      course_name: cert.course_name,
      course_hours: cert.course_hours,
      institution: cert.institution,
      issue_date: cert.issue_date,
      token: cert.token
    });
    
    const isValid = cert.hmac_signature === expectedHMAC;
    
    return jsonResponse({
      success: isValid,
      message: isValid ? 'Certificado válido' : 'Certificado inválido - Firma HMAC no coincide',
      certificate: {
        token: cert.token,
        participant_name: cert.participant_name,
        participant_id: cert.participant_id,
        course_name: cert.course_name,
        course_hours: cert.course_hours,
        institution: cert.institution,
        issue_date: cert.issue_date,
        hmac_signature: cert.hmac_signature,
        status: cert.status
      }
    });
    
  } catch (error) {
    return jsonResponse({ success: false, message: 'Error: ' + error.message });
  }
}

// ==========================================
// GENERAR PDF
// ==========================================

function generatePDF(token) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(SHEET_NAME);
    
    if (!sheet) {
      throw new Error('No hay certificados registrados');
    }
    
    const cert = findCertificateByToken(sheet, token);
    
    if (!cert || cert.status !== 'active') {
      throw new Error('Certificado no encontrado o inválido');
    }
    
    // Verificar firma
    const expectedHMAC = generateHMAC({
      participant_name: cert.participant_name,
      course_name: cert.course_name,
      course_hours: cert.course_hours,
      institution: cert.institution,
      issue_date: cert.issue_date,
      token: cert.token
    });
    
    if (cert.hmac_signature !== expectedHMAC) {
      throw new Error('Firma HMAC inválida');
    }
    
    // Crear PDF
    const blob = createCertificatePDF(cert);
    
    return ContentService
      .createBinaryOutput(blob.getBytes())
      .setMimeType(ContentService.MimeType.PDF);
    
  } catch (error) {
    return jsonResponse({ success: false, message: error.message });
  }
}

// ==========================================
// CREAR PDF DEL CERTIFICADO
// ==========================================

function createCertificatePDF(cert) {
  // Crear documento temporal
  const doc = DocumentApp.create('Certificado Temporal');
  const body = doc.getBody();
  
  // Configurar página horizontal
  doc.setPageHeight(612);
  doc.setPageWidth(792);
  
  // Margins
  body.setMarginTop(50);
  body.setMarginBottom(50);
  body.setMarginLeft(50);
  body.setMarginRight(50);
  
  // Borde decorativo
  const borderStyle = {};
  borderStyle[DocumentApp.Attribute.BORDER_WIDTH] = 3;
  borderStyle[DocumentApp.Attribute.BORDER_COLOR] = '#0f3460';
  
  // Título
  const title = body.appendParagraph('CERTIFICADO DE APROBACIÓN');
  title.setHeading(DocumentApp.ParagraphHeading.HEADING1);
  title.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  title.setBold(true);
  title.setFontSize(28);
  title.setForegroundColor('#1a1a2e');
  
  // Espacio
  body.appendParagraph('');
  
  // Institución
  const institution = body.appendParagraph(cert.institution);
  institution.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  institution.setFontSize(16);
  institution.setForegroundColor('#16213e');
  institution.setItalic(true);
  
  // Espacio
  body.appendParagraph('');
  body.appendParagraph('');
  
  // Texto introductorio
  const intro = body.appendParagraph('Por medio del presente se certifica que:');
  intro.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  intro.setFontSize(12);
  
  // Espacio
  body.appendParagraph('');
  
  // Nombre del participante
  const name = body.appendParagraph(cert.participant_name);
  name.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  name.setBold(true);
  name.setFontSize(24);
  name.setForegroundColor('#0f3460');
  
  // Espacio
  body.appendParagraph('');
  
  // Texto de aprobación
  const approval = body.appendParagraph('Ha completado satisfactoriamente el curso:');
  approval.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  approval.setFontSize(12);
  
  // Espacio
  body.appendParagraph('');
  
  // Nombre del curso
  const course = body.appendParagraph(cert.course_name);
  course.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  course.setBold(true);
  course.setItalic(true);
  course.setFontSize(18);
  course.setForegroundColor('#e94560');
  
  // Espacio
  body.appendParagraph('');
  
  // Horas
  const hours = body.appendParagraph(`Con una duración total de ${cert.course_hours} horas académicas`);
  hours.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  hours.setFontSize(12);
  
  // Espacio
  body.appendParagraph('');
  body.appendParagraph('');
  
  // Fecha
  const issueDate = new Date(cert.issue_date);
  const dateStr = Utilities.formatDate(issueDate, Session.getScriptTimeZone(), 'dd "de" MMMM "de" yyyy');
  const datePara = body.appendParagraph(`Emitido en ${dateStr}`);
  datePara.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  datePara.setFontSize(12);
  
  // Espacio
  body.appendParagraph('');
  body.appendParagraph('');
  
  // Token y verificación
  const verifyInfo = body.appendParagraph(`ID Certificado: ${cert.token}`);
  verifyInfo.setAlignment(DocumentApp.HorizontalAlignment.CENTER);
  verifyInfo.setFontSize(10);
  verifyInfo.setForegroundColor('#666666');
  
  // Guardar y convertir a PDF
  doc.saveAndClose();
  
  const blob = DriveApp.getFileById(doc.getId()).getAs('application/pdf');
  
  // Eliminar documento temporal
  DriveApp.getFileById(doc.getId()).setTrashed(true);
  
  return blob;
}

// ==========================================
// FUNCIONES AUXILIARES
// ==========================================

function findCertificateByToken(sheet, token) {
  const data = sheet.getDataRange().getValues();
  
  // Saltar encabezado
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === token) {
      return {
        token: data[i][0],
        participant_name: data[i][1],
        participant_id: data[i][2],
        course_name: data[i][3],
        course_hours: data[i][4],
        institution: data[i][5],
        issue_date: data[i][6],
        hmac_signature: data[i][7],
        status: data[i][8]
      };
    }
  }
  
  return null;
}

function generateHMAC(cert) {
  const canonical = [
    cert.participant_name,
    cert.course_name,
    cert.course_hours,
    cert.institution,
    cert.issue_date,
    cert.token
  ].join('|');
  
  return Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    canonical + HMAC_SECRET,
    Utilities.Charset.UTF_8
  ).map(b => {
    return ((b < 0) ? b + 256 : b).toString(16).padStart(2, '0');
  }).join('');
}

function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
