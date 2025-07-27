# Postman Collection - Example Plugin API

Este directorio contiene la colección de Postman y el archivo de environment para probar la API del Example Plugin.

## Archivos

- `ExamplePlugin.postman_collection.json` - Colección con todos los endpoints de la API
- `ExamplePlugin.postman_environment.json` - Variables de entorno para desarrollo

## Cómo usar

1. **Importar en Postman:**
   - Abre Postman
   - Click en "Import" 
   - Selecciona ambos archivos JSON
   - La colección y el environment se importarán automáticamente

2. **Configurar autenticación:**
   - En el environment, actualiza el valor de `bearer_token` con un token JWT válido de Azure AD
   - Si necesitas generar un token, puedes usar:
     ```bash
     curl -X POST https://login.microsoftonline.com/5b973f99-77df-4beb-b27d-aa0c70b8482c/oauth2/v2.0/token \
       -H "Content-Type: application/x-www-form-urlencoded" \
       -d "client_id=your-client-id" \
       -d "client_secret=your-client-secret" \
       -d "scope=api://example-plugin/.default" \
       -d "grant_type=client_credentials"
     ```

3. **Variables de entorno:**
   - `base_url`: URL base de la API (por defecto apunta a localhost:8000)
   - `bearer_token`: Token JWT para autenticación
   - `chat_id`: ID de sesión de chat
   - `agent_id`: ID del agente
   - `agent_version`: Versión del agente
   - `tenant_id`: ID del tenant de Azure AD (fijo)
   - `client_id`: ID del cliente para autenticación
   - `client_secret`: Secreto del cliente

## Endpoints disponibles

### Sample
- **GET /sample** - Procesa una entrada de muestra

### AI
- **POST /ai-sample** - Procesa una solicitud usando IA (OpenAI)

### Blob Storage
- **POST /blob-sample** - Sube un archivo a Azure Blob Storage

### Data Visualization
- **POST /create-plot** - Crea un gráfico desde datos de Excel

### System
- **GET /health** - Verifica el estado del servicio (no requiere auth)

## Notas

- Todos los endpoints (excepto `/health`) requieren autenticación con JWT
- Los headers `x-chat-id`, `x-agent-id` y `x-agent-version` son opcionales pero recomendados para tracking
- Para producción, cambia el `base_url` a `https://api.example.com/api/plugin/ExamplePlugin/v1`