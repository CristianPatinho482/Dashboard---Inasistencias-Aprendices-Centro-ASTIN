# Consulta nominal en Azure Static Web Apps

Guía de despliegue de la página **05 · Consulta semanal** con nombres de aprendices, sin exponerlos en el portal público ni en archivos estáticos.

> **Antes de empezar:** el repositorio de GitHub debe ser **privado**. Si alguna vez fue público y contuvo `data/restricted/DIM_APRENDIZ_PII.csv`, trate esos datos como comprometidos, ejecute `scripts/09_limpiar_pii_git.ps1` y notifique al contacto de privacidad/seguridad del SENA. Cambiar la visibilidad no borra el historial ni los forks.

## 1. Arquitectura

```text
Navegador
   │
   ├── web/index.html                 Portal agregado (público, sin PII)
   └── web/consulta.html              Página nominal (requiere rol "nominal")
            │
            │  fetch /api/consulta
            ▼
   Azure Static Web Apps
   ├── Autenticación Entra ID (app registration propia)
   ├── /api/roles                     rolesSource: grupo → rol "nominal"
   └── /api/consulta                  agrega en el servidor y devuelve solo totales
            │
            ▼
   Azure Blob Storage privado
   └── consulta-privada/consulta_web.json   (nombres + eventos, sin acceso público)
```

Propiedades de seguridad:

- El navegador **nunca recibe registros crudos**. La API agrupa por aprendiz/ficha y devuelve únicamente los totales del intervalo.
- El archivo nominal no se versiona. Se genera en `data/private/consulta_web.json` (ignorado por Git) y se sube a un contenedor privado.
- La API vuelve a validar `x-ms-client-principal`; no confía solo en la regla de ruta.
- Si la autenticación o la consulta a grupos falla, el acceso se deniega (fail closed).
- El CSV que exporta el navegador se genera en memoria y advierte que contiene datos personales.

### Dos formas de leer el Blob

| Modo | Cuándo usarlo | Configuración | Identidad administrada |
|---|---|---|---|
| **API administrada + SAS** | Despliegue simple, un solo recurso | `BLOB_SAS_URL` con SAS de solo lectura | No disponible en funciones administradas |
| **Function App propio (recomendado)** | Producción con máxima seguridad | `STORAGE_ACCOUNT_NAME` + `DefaultAzureCredential` | Sí, sistema o usuario |

> **Limitación importante:** la identidad administrada de Azure Static Web Apps solo se usa para recuperar secretos de Key Vault. Las funciones administradas **no** tienen identidad administrada. Para leer Blob sin SAS ni claves, vincule una Function App propia (bring your own functions). Requiere plan Standard.

## 2. Requisitos

- Suscripción de Azure con permiso para crear recursos.
- Plan **Standard** de Azure Static Web Apps: la autenticación personalizada, `rolesSource` y el backend propio no están disponibles en el plan Free.
- Tenant de Microsoft Entra ID y permiso para crear un registro de aplicación y un grupo de seguridad.
- Repositorio de GitHub privado con el código de `web/` y `api/`.
- Azure CLI (`az`) y Node.js 20+ en el equipo de despliegue.
- Haber ejecutado el ETL y tener `data/private/consulta_web.json` (ver sección 4).

## 3. Crear los recursos

Ajuste los nombres y la región. El nombre de la cuenta de almacenamiento debe ser único, en minúsculas y sin guiones.

```powershell
$rg = 'rg-astin-consulta'
$location = 'eastus2'
$swa = 'astin-consulta'
$storage = 'astinconsulta2026'
$container = 'consulta-privada'

az group create --name $rg --location $location

az storage account create `
  --name $storage `
  --resource-group $rg `
  --location $location `
  --sku Standard_LRS `
  --kind StorageV2 `
  --min-tls-version TLS1_2 `
  --allow-blob-public-access false `
  --allow-shared-key-access false

az storage container create `
  --account-name $storage `
  --name $container `
  --auth-mode login `
  --public-access off

az staticwebapp create `
  --name $swa `
  --resource-group $rg `
  --location $location `
  --sku Standard
```

Notas:

- `--allow-shared-key-access false` obliga a usar Entra ID o SAS de delegación de usuario. Si su operación depende de claves de cuenta, omítalo y documente la excepción.
- El contenedor se crea privado. Verifique en **Storage > Containers > Access level = Private**.
- Guarde el nombre de host: `az staticwebapp show -n $swa -g $rg --query defaultHostname -o tsv`.

## 4. Exportar y subir los datos

El archivo real se genera desde el ETL local. Nunca lo copie a `web/`.

```powershell
python .\scripts\07_exportar_consulta_web.py
# Salida: data\private\consulta_web.json (ignorado por Git)

.\scripts\08_subir_consulta_azure.ps1 -StorageAccount $storage
```

El script valida que el archivo no sea sintético, que tenga registros, que no esté dentro de `web/`, crea el contenedor privado y sube el blob con `--auth-mode login`.

Para la API administrada, genere un SAS de solo lectura y guárdelo como `BLOB_SAS_URL`:

```powershell
.\scripts\08_subir_consulta_azure.ps1 -StorageAccount $storage -GenerarSas -SasDias 365
```

> El SAS es un secreto. No lo pegue en Git, en `web/`, en capturas ni en el chat. Rótelo antes del vencimiento con el mismo comando y actualice `BLOB_SAS_URL`.

Para el modo con Function App propia no genere SAS: asigne el rol `Storage Blob Data Reader` a la identidad de la Function App (sección 8B).

## 5. Registrar la aplicación en Entra ID

1. **Microsoft Entra ID > App registrations > New registration**.
2. Nombre: `ASTIN Consulta Nominal`.
3. Cuentas: **Solo cuentas de este directorio organizacional**.
4. Redirect URI: **Web** → `https://<host-de-la-swa>/.auth/login/aad/callback`.
5. En **Authentication**, active **ID tokens**.
6. En **Certificates & secrets**, cree un secreto y copie el **Value** (no el Secret ID).
7. En **API permissions**, agregue **Microsoft Graph > Delegated > `User.Read.All`** y conceda consentimiento de administrador. La función `roles` lo usa para consultar `/me/memberOf`. Si su política no permite ese permiso, use la alternativa de roles de aplicación (sección 6).
8. En **Token configuration > Optional claims > ID token**, puede agregar el claim `groups` si prefiere evitar Graph. Si el usuario pertenece a muchos grupos, Entra puede emitir un claim de overage; en ese caso la función cae a Graph.

Guarde:

- `Application (client) ID` → `AZURE_CLIENT_ID`
- `Directory (tenant) ID` → reemplace `REPLACE_TENANT_ID` en `web/staticwebapp.config.json`
- Secreto → `AZURE_CLIENT_SECRET`

## 6. Crear el grupo y mapear el rol

1. **Microsoft Entra ID > Groups > New group**.
2. Tipo: **Security**. Nombre: `ASTIN-Inasistencias-Nominal`.
3. Agregue solo a las personas autorizadas por Bienestar/Coordinación Académica.
4. Copie el **Object ID** del grupo.

El rol se asigna en el inicio de sesión mediante `web/staticwebapp.config.json`:

```json
"auth": {
  "rolesSource": "/api/roles",
  "identityProviders": {
    "azureActiveDirectory": {
      "userDetailsClaim": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
      "registration": {
        "openIdIssuer": "https://login.microsoftonline.com/<TENANT_ID>",
        "clientIdSettingName": "AZURE_CLIENT_ID",
        "clientSecretSettingName": "AZURE_CLIENT_SECRET"
      },
      "login": {
        "loginParameters": ["resource=https://graph.microsoft.com"]
      }
    }
  }
}
```

`api/src/functions/roles.js` revisa, en orden:

1. `ALLOWED_EMAILS` (respaldo operativo; úselo solo de forma temporal).
2. `ENTRA_NOMINAL_APP_ROLES` (roles de aplicación presentes en los claims).
3. `ENTRA_NOMINAL_GROUPS` (claims de grupo o consulta a Graph).

Si ninguna coincide, devuelve `{ "roles": [] }` y el acceso queda denegado.

### Alternativa sin Graph: roles de aplicación

1. En el registro de la app, **App roles > Create app role**.
2. Display name: `Consulta nominal`; Value: `nominal`; Allowed member types: **Users/Groups**.
3. En **Enterprise applications > ASTIN Consulta Nominal > Users and groups**, asigne el grupo o las personas al rol.
4. Configure `ENTRA_NOMINAL_APP_ROLES=nominal` y `AUTH_MODE=roles`.
5. Puede quitar `loginParameters` y el permiso `User.Read.All` si no usará Graph.

## 7. Configurar la Static Web App

### 7.1 Reemplazar el tenant

Edite `web/staticwebapp.config.json` y cambie `REPLACE_TENANT_ID` por el ID del tenant. Confirme que el redirect URI del registro de la app coincide exactamente con el host de la SWA.

### 7.2 Variables de aplicación

```powershell
az staticwebapp appsettings set `
  --name $swa `
  --resource-group $rg `
  --setting-names `
    AZURE_CLIENT_ID='<application-client-id>' `
    AZURE_CLIENT_SECRET='<secret-value>' `
    ENTRA_NOMINAL_GROUPS='<group-object-id>' `
    NOMINAL_ROLE='nominal' `
    AUTH_MODE='roles' `
    BLOB_CONTAINER='consulta-privada' `
    BLOB_NAME='consulta_web.json' `
    CACHE_TTL_SECONDS='300' `
    BLOB_SAS_URL='<url-con-sas>'
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `AZURE_CLIENT_ID` | Sí | Client ID del registro de Entra. |
| `AZURE_CLIENT_SECRET` | Sí | Valor del secreto. Rótelo antes de vencer. |
| `ENTRA_NOMINAL_GROUPS` | Una de las tres | Object IDs de grupos separados por coma. |
| `ENTRA_NOMINAL_APP_ROLES` | Una de las tres | Valores de app roles, por ejemplo `nominal`. |
| `ALLOWED_EMAILS` | Solo respaldo | Correos separados por coma. Evítelo en producción. |
| `NOMINAL_ROLE` | Sí | Nombre del rol, por defecto `nominal`. |
| `AUTH_MODE` | Sí | `roles` en Azure. `allowlist` solo para pruebas locales. |
| `BLOB_SAS_URL` | Modo SAS | URL completa del blob con SAS de lectura. |
| `STORAGE_ACCOUNT_NAME` | Modo identidad | Cuenta de almacenamiento; usa `DefaultAzureCredential`. |
| `BLOB_CONTAINER` | No | Por defecto `consulta-privada`. |
| `BLOB_NAME` | No | Por defecto `consulta_web.json`. |
| `CACHE_TTL_SECONDS` | No | Caché en memoria de la API; mínimo 30, por defecto 300. |
| `CONSULTA_LOCAL_FILE` | **Nunca en Azure** | Solo desarrollo local. |

No configure `CONSULTA_LOCAL_FILE` en Azure: la API intentaría leer una ruta inexistente.

### 7.3 Verificar la configuración de rutas

`web/staticwebapp.config.json` ya define:

- `/consulta.html` y `/api/consulta`: solo rol `nominal`.
- `/api/roles`: invocado por la plataforma como `rolesSource`; no debe usarse desde el navegador.
- `/acceso-denegado.html`: público, para el 403.
- `/data/demo_consulta.json`: público, solo demostración sintética.
- `responseOverrides`: 401 → login; 403 → página de acceso denegado.
- Cabeceras: `no-store`, `noindex`, CSP, `X-Frame-Options: DENY`, HSTS.

## 8. Desplegar

### 8A. API administrada + SAS (simple)

1. En GitHub, **Settings > Secrets and variables > Actions**, cree `AZURE_STATIC_WEB_APPS_API_TOKEN` con el token de despliegue:

   ```powershell
   az staticwebapp secrets list --name $swa --resource-group $rg --query properties.apiKey -o tsv
   ```

2. El workflow `.github/workflows/azure-static-web-apps.yml` valida la agregación, ejecuta las pruebas y despliega `web/` + `api/` en cada push a `main`. Si `AZURE_STATIC_WEB_APPS_API_TOKEN` no existe, el workflow valida pero omite el despliegue y deja un aviso; configúrelo para publicar.
3. Para desplegar sin push, ejecute el workflow manualmente desde **Actions > Azure Static Web Apps > Run workflow**.

### 8B. Function App propia + identidad administrada (recomendado)

Requisitos: plan Standard de SWA y una Function App (Consumption, Premium o Dedicated) en la misma región o región compatible.

```powershell
$func = 'astin-consulta-api'
$funcStorage = 'astinconsultaapi2026'

az storage account create -n $funcStorage -g $rg -l $location --sku Standard_LRS
az functionapp create `
  --name $func `
  --resource-group $rg `
  --storage-account $funcStorage `
  --consumption-plan-location $location `
  --runtime node `
  --runtime-version 20 `
  --functions-version 4 `
  --os-type Linux

az functionapp identity assign --name $func --resource-group $rg
```

Asigne el rol de lectura del Blob a la identidad:

```powershell
$principalId = az functionapp identity show -n $func -g $rg --query principalId -o tsv
$storageId = az storage account show -n $storage -g $rg --query id -o tsv

az role assignment create `
  --assignee $principalId `
  --role 'Storage Blob Data Reader' `
  --scope $storageId
```

Configure la Function App:

```powershell
az functionapp config appsettings set `
  --name $func `
  --resource-group $rg `
  --settings `
    AUTH_MODE='roles' `
    NOMINAL_ROLE='nominal' `
    ENTRA_NOMINAL_GROUPS='<group-object-id>' `
    STORAGE_ACCOUNT_NAME=$storage `
    BLOB_CONTAINER='consulta-privada' `
    BLOB_NAME='consulta_web.json' `
    CACHE_TTL_SECONDS='300' `
    FUNCTIONS_WORKER_RUNTIME='node'
```

Despliegue la API (desde `api/`):

```powershell
npm ci
func azure functionapp publish $func --javascript
```

Vincule la Function App a la SWA:

```powershell
$funcId = az functionapp show -n $func -g $rg --query id -o tsv
az staticwebapp backends link `
  --name $swa `
  --resource-group $rg `
  --backend-resource-id $funcId `
  --backend-region $location
```

Luego:

1. Cambie `api_location` a `""` en `.github/workflows/azure-static-web-apps.yml` para que la SWA no intente desplegar funciones administradas.
2. Quite `BLOB_SAS_URL` de la SWA.
3. Mantenga `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `ENTRA_NOMINAL_GROUPS`, `NOMINAL_ROLE` y `AUTH_MODE` en la SWA para la autenticación y `rolesSource`.
4. Vuelva a desplegar la SWA y verifique `/api/consulta`.

La Function App no debe ser accesible directamente: al vincularla, la SWA la deja como backend exclusivo. No configure IP restrictions ni private link en la Function App; la integración no lo admite. Si necesita acceso directo para diagnóstico, use una identidad y una ruta temporal, y retírela después.

## 9. Validación

Use una ventana de incógnito y una cuenta de prueba:

1. `https://<host>/consulta.html` sin sesión → redirección al login de Entra.
2. Cuenta **fuera** del grupo → `acceso-denegado.html` o 403; no debe ver nombres.
3. Cuenta **dentro** del grupo → tabla con nombres, filtros y KPIs.
4. `https://<host>/api/consulta` sin sesión → 401/403; con sesión no autorizada → 403.
5. `https://<storage>.blob.core.windows.net/consulta-privada/consulta_web.json` → 404/403; nunca 200.
6. **DevTools > Sources/Network**: `consulta.html`, `consulta.js`, `aggregate.js`, `config.js` y `demo_consulta.json` no contienen nombres reales.
7. Exportar CSV: debe pedir confirmación y descargar `consulta_semanal_<fecha>.csv`; en Azure no debe existir el prefijo `demo_`.
8. Probar un intervalo sin datos, una ficha inexistente y una búsqueda sin resultados.
9. Revisar los logs de Application Insights/Function App: no deben registrar nombres, documentos ni justificaciones.

## 10. Actualización periódica

El flujo recomendado es local y desatendido:

1. El bot/OneDrive actualiza `Inasistencias.xls`.
2. `scripts/actualizar_datos.ps1` ejecuta el ETL, el modelo, el PBIR, el portal y la exportación nominal.
3. El operador (o una tarea programada con credenciales de Azure) ejecuta `scripts/08_subir_consulta_azure.ps1`.
4. La API renueva su caché en `CACHE_TTL_SECONDS` (300 s por defecto); no hace falta redesplegar.

No incluya la exportación nominal en el commit ni en el portal. El Blob conserva la versión anterior hasta que la carga termine; la API puede servir datos por hasta 5 minutos después de la carga.

## 11. Seguridad y privacidad

- El repositorio debe ser privado; GitHub Pages está deshabilitado en este proyecto y no sirve para nombres.
- El contenedor Blob es privado; no habilite acceso anónimo ni `$web`.
- El SAS, el secreto de Entra y las cadenas de conexión son secretos. Use Key Vault cuando sea posible y rote antes del vencimiento.
- El rol `nominal` debe tener el mínimo de personas. Revise el grupo trimestralmente.
- No agregue nombres, documentos, justificaciones ni correos a logs, mensajes de error, analytics ni URLs.
- El CSV descargado queda en el equipo del usuario: exija disco cifrado, retención mínima y borrado seguro.
- Trate cualquier exposición previa como incidente: purgue el historial, notifique y documente.
- Considere RLS/permisos del espacio de Power BI para la página 05 publicada; el PBIP no es un control de acceso por sí mismo.

## 12. Costos y límites

- **Static Web Apps Standard**: cobro por hora; consulte la calculadora. El plan Free no permite autenticación personalizada ni backend propio.
- **Storage**: unos pocos MB; el costo es mínimo. La salida de datos es baja porque la API devuelve agregados.
- **Function App propia** (si aplica): consumo o plan dedicado; la identidad administrada no tiene costo adicional.
- **Entra ID**: el grupo y el registro de app no tienen costo; algunas funciones de asignación a grupos pueden requerir licencia P1/P2 según su tenant.
- Límite de la API: 250 000 registros por archivo; el ETL actual produce ~16 000, muy por debajo.

## 13. Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| Bucle de login o 401 en el callback | Redirect URI distinto, ID tokens desactivados o tenant incorrecto | Corrija el registro de app y `openIdIssuer`. |
| `roles` vacío | Grupo mal configurado, Graph sin consentimiento o `ENTRA_NOMINAL_GROUPS` vacío | Revise el Object ID, el consentimiento `User.Read.All` y los logs de `roles`. |
| 403 con cuenta correcta | El rol se asigna en el login; la sesión anterior conserva roles viejos | Cierre sesión y vuelva a entrar. |
| `/api/consulta` devuelve 503 | Blob inaccesible, SAS vencido o identidad sin rol | Verifique `BLOB_SAS_URL`/`STORAGE_ACCOUNT_NAME` y el rol `Storage Blob Data Reader`. |
| La tabla no muestra nombres | Se está usando `demo_consulta.json` o el modo demo | En Azure, `demoMode` debe ser falso; revise `config.js`. |
| El deploy falla en `npm ci` | Falta `api/package-lock.json` o Node incorrecto | Ejecute `npm install --package-lock-only` y confirme Node 20. |
| Error de CSP en la consola | Se agregó un script/estilo inline a `consulta.html` | Use archivos externos o ajuste la CSP con revisión de seguridad. |

## 14. Rollback

- **SWA**: vuelva a desplegar un commit anterior desde GitHub Actions o `az staticwebapp` con el token de despliegue.
- **Datos**: suba la versión anterior del Blob (mantenga copias con fecha en el contenedor privado) o vuelva a exportar desde el ETL.
- **Auth**: desactive `rolesSource` solo si tiene otro control de acceso; sin él, la página nominal queda sin autorización.
- **Function App propia**: desvincule con `az staticwebapp backends unlink -n $swa -g $rg` y vuelva a la API administrada si es necesario.

## 15. Referencias

- [Custom authentication in Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/authentication-custom)
- [Assign roles with Microsoft Graph](https://learn.microsoft.com/azure/static-web-apps/assign-roles-microsoft-graph)
- [Bring your own functions](https://learn.microsoft.com/azure/static-web-apps/functions-bring-your-own)
- [API support in Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/apis-functions)
- [Access user information](https://learn.microsoft.com/azure/static-web-apps/user-information)
- [Configure Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/configuration)
