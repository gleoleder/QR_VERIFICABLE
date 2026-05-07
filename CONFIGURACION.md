# 🚀 Configuración del Sistema de Certificados QR

## Paso 1: Crear Google Sheet

1. Ve a https://sheets.google.com
2. Click en "+" para crear una nueva hoja
3. Nombra la hoja: `Certificados QR`
4. Copia el **ID de la hoja** de la URL:
   ```
   https://docs.google.com/spreadsheets/d/1ABC123xyz_TU_SHEET_ID_AQUI/edit
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^
   ```

## Paso 2: Crear Google Apps Script

1. En tu Google Sheet, ve a **Extensiones > Apps Script**
2. Borra el código que aparece
3. Copia y pega el contenido de `code.js`
4. **IMPORTANTE:** Cambia la línea de `HMAC_SECRET`:
   ```javascript
   const HMAC_SECRET = 'tu_clave_secreta_muy_segura_cambiar_en_produccion';
   ```
   Genera una clave segura con: https://generate-secret.vercel.app/32

5. Click en **Guardar** (ícono de diskette)
6. Nombra el proyecto: `Sistema Certificados QR`

## Paso 3: Desplegar como Web App

1. Click en **Implementar** ( Deploy) > **Nueva implementación**
2. Click en el engranaje ⚙️ junto a "Seleccionar tipo"
3. Elige **Aplicación web**
4. Configura:
   - **Descripción:** `API Certificados`
   - **Ejecutar como:** `Yo (tu email)`
   - **Quién tiene acceso:** `Cualquier usuario` ⚠️
5. Click en **Implementar**
6. **Autoriza el script:**
   - Click en "Autorizar acceso"
   - Selecciona tu cuenta de Google
   - Click en "Configuración avanzada" > "Ir a ... (no seguro)"
   - Click en "Permitir"
7. **Copia la URL de la aplicación web** (se ve así):
   ```
   https://script.google.com/macros/s/TU_SCRIPT_ID_AQUI/exec
   ```

## Paso 4: Configurar index.html

1. Abre el archivo `index.html`
2. Busca la sección `CONFIG` (línea ~170)
3. Actualiza los valores:
   ```javascript
   const CONFIG = {
       SHEET_ID: 'TU_SHEET_ID_AQUI',  // Del Paso 1
       SCRIPT_URL: 'https://script.google.com/macros/s/TU_SCRIPT_ID_AQUI/exec',  // Del Paso 3
       HMAC_SECRET: 'tu_clave_secreta_muy_segura'  // La misma que en code.js
   };
   ```
4. Guarda el archivo

## Paso 5: Subir a GitHub Pages

1. Abre GitHub Desktop o usa la terminal
2. Agrega todos los archivos: `git add .`
3. Commit: `git commit -m "Configurar sistema QR"`
4. Push: `git push origin main`
5. Ve a tu repositorio en GitHub
6. **Settings > Pages**
7. En **Source**, elige: `Deploy from a branch`
8. Branch: `main` / Folder: `/ (root)`
9. Click en **Save**
10. Espera ~2 minutos y tu página estará en:
    ```
    https://tu-usuario.github.io/QR_VERIFICABLE/
    ```

## ✅ ¡Listo!

Ahora puedes:

1. **Emitir certificados:** Abre tu página y ve a la pestaña "Emitir Certificado"
2. **Verificar certificados:** Escanea el QR o ingresa el token
3. **Ver datos en tu Google Sheet:** Los certificados se guardan automáticamente

## 📱 Hoja de cálculo

Tu Google Sheet tendrá estas columnas automáticamente:

| Columna | Descripción |
|---------|-------------|
| token | UUID único del certificado |
| participant_name | Nombre del participante |
| participant_id | DNI/Cédula (opcional) |
| course_name | Nombre del curso |
| course_hours | Duración en horas |
| institution | Institución emisora |
| issue_date | Fecha de emisión |
| hmac_signature | Firma de seguridad |
| status | active/revoked/expired |
| created_at | Timestamp de creación |

## 🔒 Seguridad

- **HMAC-SHA256:** Cada certificado tiene una firma criptográfica
- **Verificación de integridad:** Si alguien modifica los datos, la firma no coincide
- **Google Sheets:** Tus datos están seguros en tu cuenta de Google

## 🛠️ Solución de problemas

### Error: "Certificado no encontrado"
- Verifica que el Google Apps Script esté desplegado como Web App
- Asegúrate de que el SCRIPT_URL sea correcto
- Revisa que la hoja se llame "Certificados"

### Error: "Firma HMAC inválida"
- El HMAC_SECRET en index.html debe ser IGUAL al de code.js
- Copia y pega exactamente el mismo valor en ambos archivos

### Error: "Permiso denegado"
- En el Apps Script, verifica que "Quién tiene acceso" sea "Cualquier usuario"
- Vuelve a desplegar el script si es necesario

### La página no carga en GitHub Pages
- Espera 2-3 minutos después del push
- Verifica que GitHub Pages esté activado en Settings > Pages
- Revisa que el index.html esté en la raíz del repositorio
