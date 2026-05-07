# 📜 Sistema de Certificados QR con Verificación Criptográfica

> **Demo en vivo:** [Despliega en Render](#-despliegue-en-render-gratis) para obtener tu URL pública gratuita

Sistema profesional de emisión y verificación de certificados digitales mediante códigos QR, con generación de PDFs en memoria y firma criptográfica HMAC-SHA256.

## 🎯 Características Principales

- ✅ **Emisión de certificados** vía API REST
- ✅ **Verificación instantánea** escaneando QR
- ✅ **PDFs generados en memoria** (sin almacenamiento en disco)
- ✅ **Firma HMAC-SHA256** para integridad de datos
- ✅ **Rate limiting** para protección contra abuso
- ✅ **Auditoría completa** de todas las verificaciones
- ✅ **Revocación de certificados** cuando sea necesario
- ✅ **Diseño responsive** para verificación móvil

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Usuario       │────▶│   Flask API      │────▶│   SQLite/       │
│   (escanea QR)  │     │   (verifica)     │     │   PostgreSQL    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   PDF en         │
                        │   memoria        │
                        │   (BytesIO)      │
                        └──────────────────┘
```

**Principio clave:** Los PDFs NUNCA se almacenan. Se generan bajo demanda y se descartan inmediatamente después de la descarga.

## 📁 Estructura del Proyecto

```
certificados-qr/
├── app.py                 # Aplicación Flask principal
├── models.py              # Modelos de base de datos
├── utils.py               # Utilidades de seguridad y QR
├── generador_pdf.py       # Generación de PDFs en memoria
├── requirements.txt       # Dependencias de Python
├── .env.example           # Variables de entorno (copiar a .env)
├── .env                   # Configuración local (no commitear)
├── templates/
│   ├── index.html         # Página de verificación
│   └── verify_error.html  # Página de error
├── static/                # Archivos estáticos (CSS, JS, imágenes)
└── README.md              # Este archivo
```

## 🚀 Instalación Rápida

### 1. Clonar o descargar el proyecto

```bash
cd certificados-qr
```

### 2. Crear entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Generar claves seguras
python -c "import secrets; print('HMAC_SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

Editar `.env` y pegar las claves generadas.

### 5. Inicializar base de datos

```bash
python init_db.py
```

### 6. Iniciar servidor (desarrollo)

```bash
python app.py
```

Acceder a: http://localhost:5000

## 📡 Endpoints de la API

### POST /issue

Emite un nuevo certificado.

**Request:**
```json
{
  "participant_name": "Juan Pérez",
  "participant_id": "12345678",
  "course_name": "Python Avanzado",
  "course_hours": 40,
  "institution": "Universidad XYZ"
}
```

**Response:**
```json
{
  "success": true,
  "token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "verification_url": "https://tudominio.com/verify/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
  "certificate_id": 1,
  "hmac_signature": "abc123def456..."
}
```

### GET /verify/<token>

Verifica y descarga certificado PDF.

- **200 OK:** Certificado válido, descarga PDF
- **404 Not Found:** Token no existe
- **403 Forbidden:** Certificado revocado o expirado

### PUT /revoke/<token>

Revoca un certificado.

**Request:**
```json
{
  "reason": "Emisión duplicada",
  "revoked_by": "admin@institution.com"
}
```

### GET /health

Health check para monitoreo.

## 🔐 Seguridad

### Firma HMAC-SHA256

Cada certificado incluye una firma criptográfica calculada sobre:
- Nombre del participante
- Nombre del curso
- Horas del curso
- Institución emisora
- Fecha de emisión
- Token único

La firma se verifica en cada solicitud de verificación para detectar manipulaciones.

### Rate Limiting

| Endpoint | Límite |
|----------|--------|
| /issue | 20/min |
| /verify | 10/min |
| /revoke | 5/min |

### Headers de Seguridad

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (producción)
- `Cache-Control: no-store` (respuestas con PDF)

## 🗄️ Base de Datos

### Tablas

**certificates:**
- `id`: Primary key
- `token`: UUID único (indexed)
- `participant_name`: Nombre del participante
- `course_name`: Nombre del curso
- `course_hours`: Duración en horas
- `institution`: Institución emisora
- `issue_date`: Fecha de emisión
- `expiry_date`: Fecha de expiración (nullable)
- `hmac_signature`: Firma HMAC-SHA256
- `status`: active | revoked | expired

**audit_logs:**
- `id`: Primary key
- `certificate_id`: Foreign key
- `token`: Token verificado
- `ip_address`: IP truncada (privacidad)
- `user_agent`: Navegador del usuario
- `verified_at`: Timestamp
- `success`: Éxito del intento
- `failure_reason`: Motivo de fallo

## 🌐 Despliegue en Producción

### 🚀 Despliegue en Render (Gratis)

**¡Obtén tu URL pública en 5 minutos!**

1. **Crea cuenta en Render:**
   - Ve a https://render.com
   - Regístrate con GitHub (recomendado) o email

2. **Crea nuevo Web Service:**
   - Click en "New +" → "Blueprint"
   - Conecta tu cuenta de GitHub
   - Selecciona el repositorio `gleoleder/QR_VERIFICABLE`

3. **Configuración automática:**
   - El archivo `render.yaml` configura todo automáticamente:
     - Servicio web Python
     - Base de datos PostgreSQL
     - Variables de entorno seguras

4. **Click en "Apply"**
   - Render construirá y desplegará automáticamente
   - En ~3 minutos tendrás tu URL pública: `https://qr-verificable-xxxx.onrender.com`

5. **¡Listo!**
   - Accede a tu URL pública
   - Prueba emitir y verificar certificados
   - Comparte el link de verificación

**Ventajas:**
- ✅ Totalmente gratis (plan free)
- ✅ HTTPS automático
- ✅ Base de datos PostgreSQL incluida
- ✅ Despliegue continuo desde GitHub
- ✅ Sin configuración manual

---

1. Crear cuenta en [render.com](https://render.com)
2. Crear nuevo Web Service
3. Conectar repositorio de GitHub
4. Configurar variables de entorno:
   - `HMAC_SECRET_KEY`
   - `SECRET_KEY`
   - `DATABASE_URL` (PostgreSQL de Render)
   - `FLASK_ENV=production`
   - `BASE_URL=https://tu-app.onrender.com`
5. Deploy

**render.yaml:**
```yaml
services:
  - type: web
    name: certificados-qr
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: HMAC_SECRET_KEY
        sync: false
      - key: SECRET_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: certificados-db
          property: connectionString
    databases:
      - name: certificados-db
        databaseName: certificados
        user: certificados
```

### Railway

1. Crear cuenta en [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Añadir PostgreSQL plugin
4. Configurar variables en Railway Dashboard
5. Deploy automático

### VPS (Ubuntu/Debian)

```bash
# Instalar Python y dependencias
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx supervisor

# Clonar proyecto
git clone https://github.com/tu-usuario/certificados-qr.git
cd certificados-qr

# Configurar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con claves seguras

# Configurar Gunicorn
sudo nano /etc/supervisor/conf.d/certificados.conf
```

**/etc/supervisor/conf.d/certificados.conf:**
```ini
[program:certificados]
command=/ruta/certificados-qr/venv/bin/gunicorn app:app --workers 4 --bind 0.0.0.0:8000
directory=/ruta/certificados-qr
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/certificados/out.log
```

```bash
# Configurar Nginx
sudo nano /etc/nginx/sites-available/certificados
```

**/etc/nginx/sites-available/certificados:**
```nginx
server {
    listen 80;
    server_name tudominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Habilitar y reiniciar
sudo ln -s /etc/nginx/sites-available/certificados /etc/nginx/sites-enabled/
sudo supervisorctl reread
sudo supervisorctl update
sudo systemctl restart nginx
```

### HTTPS Obligatorio

Para producción, configurar HTTPS con Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tudominio.com
```

## 🧪 Pruebas

### Probar emisión

```bash
curl -X POST http://localhost:5000/issue \
  -H "Content-Type: application/json" \
  -d '{
    "participant_name": "Juan Pérez",
    "course_name": "Python Avanzado",
    "course_hours": 40,
    "institution": "Universidad XYZ"
  }'
```

### Probar verificación

```bash
# Descargar PDF
curl -O http://localhost:5000/verify/<token>

# Ver en navegador
http://localhost:5000/verify/<token>
```

## 📝 Migración a Firma Digital Avanzada (PAdES/X.509)

Para validez legal ante entidades oficiales (gov, universidades), considerar:

### 1. Firma PAdES (PDF Advanced Electronic Signature)

```python
# Usando endesive (pip install endesive)
from endesive.pdf import cms

# Firmar PDF con certificado X.509
signature_data = cms.sign(
    pdf_content,
    private_key,
    certificate,
    [],
    'sha256'
)
```

**Requisitos:**
- Certificado X.509 emitido por CA reconocida
- HSM o token criptográfico para guardar clave privada
- Timestamping Authority (TSA) para sello de tiempo

### 2. Validación Legal

- **España:** @firma, AutoFirma
- **UE:** eIDAS regulation
- **Latinoamérica:** Cada país tiene su normativa (ej. SAT en México, AFIP en Argentina)

### 3. Consideraciones

| Característica | HMAC-SHA256 | PAdES/X.509 |
|---------------|-------------|-------------|
| Costo | Gratis | Certificado pago (~$100-500/año) |
| Validez legal | Interna | Oficial/gubernamental |
| Complejidad | Baja | Alta |
| Verificación | Propia | Lectores PDF estándar |

## 🔧 Troubleshooting

### Error: "HMAC_SECRET_KEY no configurada"

```bash
# Generar nueva clave
python -c "import secrets; print(secrets.token_hex(32))"

# Agregar a .env
echo "HMAC_SECRET_KEY=tu_clave_generada" >> .env
```

### Error: "Database locked" (SQLite)

```bash
# En producción, migrar a PostgreSQL
# Editar .env:
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Rate limit muy bajo

Editar `.env`:
```
RATE_LIMIT_PER_MINUTE=30
```

### PDF no se descarga

Verificar headers en navegador (DevTools → Network):
- `Content-Disposition: attachment` debe estar presente
- `Content-Type: application/pdf`

## 📄 Licencia

MIT License - Ver LICENSE para detalles.

## 🤝 Contribuciones

1. Fork el repositorio
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

## 📞 Soporte

Para issues o preguntas, abrir un issue en GitHub o contactar al equipo de desarrollo.

---

**Hecho con ❤️ para certificación digital segura**
