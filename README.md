# 📜 QR Verificable - Sistema de Certificados con Validación QR

> **Demo en vivo:** https://gleoleder.github.io/QR_VERIFICABLE/

Sistema de emisión y verificación de certificados digitales mediante códigos QR, que funciona **100% en el navegador** sin necesidad de servidor backend.

## ✨ Características

- ✅ **Sin backend:** Funciona con Google Sheets como base de datos
- ✅ **GitHub Pages:** Despliegue gratuito y automático
- ✅ **QR dinámico:** Cada certificado tiene un código QR único
- ✅ **Firma criptográfica:** HMAC-SHA256 para garantizar integridad
- ✅ **PDF descargable:** Generación de certificados en PDF
- ✅ **Verificación instantánea:** Escanea QR y valida autenticidad
- ✅ **Responsive:** Funciona en celular, tablet y desktop

## 🎯 ¿Cómo funciona?

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Usuario       │────▶│   GitHub Pages   │────▶│   Google Apps   │
│   (escanea QR)  │     │   (HTML + JS)    │     │   Script        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                     │
                                                     ▼
                                              ┌──────────────────┐
                                              │   Google Sheets  │
                                              │   (Base de datos)│
                                              └──────────────────┘
```

## 🚀 Despliegue Rápido (10 minutos)

### 1. Clona o descarga este repositorio

```bash
git clone https://github.com/gleoleder/QR_VERIFICABLE.git
cd QR_VERIFICABLE
```

### 2. Configura Google Sheets

Sigue las instrucciones en **[CONFIGURACION.md](CONFIGURACION.md)** para:
- Crear Google Sheet
- Configurar Google Apps Script
- Obtener URLs y claves

### 3. Actualiza index.html

Edita la sección `CONFIG` en `index.html`:

```javascript
const CONFIG = {
    SHEET_ID: 'TU_SHEET_ID_AQUI',
    SCRIPT_URL: 'https://script.google.com/macros/s/TU_SCRIPT_ID/exec',
    HMAC_SECRET: 'tu_clave_secreta'
};
```

### 4. Sube a GitHub

```bash
git add .
git commit -m "Configurar sistema de certificados"
git push origin main
```

### 5. Activa GitHub Pages

1. Ve a **Settings > Pages** en tu repositorio
2. Source: **Deploy from a branch**
3. Branch: **main** / Folder: **/(root)**
4. Click **Save**

### 6. ¡Listo!

Tu página estará disponible en:
```
https://tu-usuario.github.io/QR_VERIFICABLE/
```

## 📱 Uso

### Emitir un certificado

1. Abre tu página web
2. Click en "Emitir Certificado"
3. Completa los datos:
   - Nombre del participante
   - Identificación (opcional)
   - Nombre del curso
   - Duración en horas
   - Institución emisora
4. Click en "Generar Certificado"
5. ¡Listo! Obtendrás:
   - Token único
   - Código QR
   - Enlace de verificación
   - Botón para descargar PDF

### Verificar un certificado

**Opción A - Escanear QR:**
1. Abre la cámara de tu celular
2. Escanea el QR del certificado
3. Se abrirá la página de verificación
4. Verás si es auténtico o falso

**Opción B - Manual:**
1. Abre tu página web
2. Click en "Verificar Certificado"
3. Ingresa el token
4. Click en "Verificar Ahora"

## 🔐 Seguridad

### Firma HMAC-SHA256

Cada certificado incluye una firma criptográfica calculada sobre:
- Nombre del participante
- Nombre del curso
- Horas del curso
- Institución emisora
- Fecha de emisión
- Token único

**¿Por qué es importante?**
- Si alguien modifica los datos en el Google Sheet, la firma no coincide
- La verificación falla y se muestra "CERTIFICADO FALSO"
- Garantiza que los datos no han sido alterados

### Generación de claves seguras

Para generar tu HMAC_SECRET:
```
https://generate-secret.vercel.app/32
```

## 📁 Estructura del Proyecto

```
QR_VERIFICABLE/
├── index.html          # Aplicación principal (HTML + CSS + JS)
├── code.js             # Google Apps Script (backend en Google)
├── CONFIGURACION.md    # Instrucciones detalladas
└── README.md           # Este archivo
```

## 🗄️ Base de Datos (Google Sheets)

Tu hoja de cálculo tendrá estas columnas:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| token | Texto | UUID único (clave primaria) |
| participant_name | Texto | Nombre del participante |
| participant_id | Texto | DNI/Cédula (opcional) |
| course_name | Texto | Nombre del curso |
| course_hours | Número | Duración en horas |
| institution | Texto | Institución emisora |
| issue_date | Texto | Fecha ISO 8601 |
| hmac_signature | Texto | Firma HMAC-SHA256 |
| status | Texto | active \| revoked \| expired |
| created_at | Texto | Timestamp de creación |

## 🌐 URLs del Sistema

| URL | Función |
|-----|---------|
| `/` | Página principal |
| `/?verify={token}` | Verificación automática desde QR |

## 🛠️ Tecnologías

| Componente | Tecnología |
|------------|------------|
| Frontend | HTML5, CSS3, JavaScript Vanilla |
| QR | QRCode.js |
| PDF | jsPDF (o Google Docs API) |
| Backend | Google Apps Script |
| Base de datos | Google Sheets |
| Hosting | GitHub Pages (gratis) |

## 📊 Casos de Uso

- **Instituciones educativas:** Certificados de cursos
- **Empresas:** Constancias de capacitación
- **Eventos:** Certificados de asistencia
- **Talleres:** Diplomas de participación
- **Organizaciones:** Credenciales verificables

## 🔧 Personalización

### Cambiar colores

Edita el CSS en `index.html`:

```css
/* Color principal (rosado/rojo) */
background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);

/* Color secundario (azul oscuro) */
background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
```

### Cambiar logo/título

```html
<div class="header">
    <h1>📜 Tu Institución</h1>
    <p>Sistema de Certificados</p>
</div>
```

### Agregar más campos

1. Agrega el input en `index.html`
2. Agrega la columna en `code.js`
3. Incluye el campo en la firma HMAC

## ⚠️ Importante

- **Nunca compartas tu HMAC_SECRET** (es como una contraseña)
- **Mantén una copia de seguridad** de tu Google Sheet
- **Prueba con certificados de prueba** antes de usar en producción
- **El Google Sheet debe estar en tu cuenta** para tener control total

## 📝 Licencia

MIT License - Libre uso para proyectos personales y comerciales.

## 🤝 Soporte

1. Revisa **[CONFIGURACION.md](CONFIGURACION.md)**
2. Verifica los errores comunes en la sección de troubleshooting
3. Si el problema persiste, crea un issue en GitHub

## 🎯 Próximas Mejoras (Opcional)

- [ ] Agregar logo de la institución en el PDF
- [ ] Firmas digitales en el certificado
- [ ] Múltiples idiomas
- [ ] Estadísticas de verificaciones
- [ ] Exportar certificados a Excel
- [ ] Notificaciones por email

---

**Hecho con ❤️ para certificación digital accesible y verificable**
