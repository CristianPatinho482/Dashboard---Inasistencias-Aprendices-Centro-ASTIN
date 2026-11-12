# Checklist de publicación en Azure

Lista de ejecución para publicar la página **05 · Consulta semanal** con datos reales.
El detalle de cada decisión está en [`azure_static_web_apps.md`](azure_static_web_apps.md).

> **Regla de oro:** los nombres de aprendices solo viajan del ETL local al Blob privado.
> Nunca se versionan, nunca se suben a `web/` y nunca se pegan en el chat ni en capturas.

> **Ruta de licenciamiento:** la solicitud a TI no es para instalar Azure CLI, sino
> para acceder al servicio **Microsoft Azure** (fila 245 del catálogo). El sustento y
> el correo sugerido están en [`solicitud_ti_azure.md`](solicitud_ti_azure.md).

## Fase 0 · Antes de tocar Azure

- [ ] Repositorio de GitHub **privado** y sin PII en el historial (ver `incidente_pii_2026-11-11.md`).
- [ ] `data/private/consulta_web.json` generado con datos reales:
      `python scripts/07_exportar_consulta_web.py`
- [ ] Pruebas de la API en verde: `node --test api/test/aggregate.test.js` (6/6).
- [ ] Confirmar que el archivo privado NO está en Git: `git check-ignore data/private/consulta_web.json`.
- [ ] Plan **Standard** de Static Web Apps aprobado (el plan Free no permite auth personalizada ni `rolesSource`).

## Fase 1 · Suscripción y licenciamiento (la gestiona TI)

La solicitud no es "instalar Azure CLI"; es acceder al **servicio Microsoft Azure**.
Azure CLI es una herramienta cliente gratuita, no un producto licenciado, y no es
necesaria si se usa el portal o Azure Cloud Shell. El sustento completo y el correo
sugerido están en [`solicitud_ti_azure.md`](solicitud_ti_azure.md).

Antes de pedir los datos:

- [ ] Confirmar la vigencia de la fila 245 del catálogo (**Microsoft Azure**, 257
      licencias, Dirección General / Oficina de Sistemas). Registra **2024-05-31**;
      si está vencida, pedir renovación o una nueva suscripción.
- [ ] Radicar la solicitud con el formato que TI indique (`GTI-F-104` Azure Dev Tools
      o `GTI-F-112` Centro de Datos) y escalarla al Gestor de Licenciamiento y al
      Grupo de Infraestructura de la Oficina de Sistemas.
- [ ] Confirmar que la suscripción es **institucional** y está autorizada para
      tratar datos personales de aprendices. No usar una cuenta gratuita, Azure for
      Students o Azure Dev Tools para PII real sin autorización expresa.

Pedir a TI y anotar:

| Dato | Ejemplo | Valor |
|---|---|---|
| Tenant ID | `00000000-0000-0000-0000-000000000000` | |
| Subscription ID | `00000000-0000-0000-0000-000000000000` | |
| Resource group | `rg-astin-consulta` | |
| Región | `eastus2` | |
| Rol asignado | `Contributor` sobre el RG | |
| Confirmación de vigencia | Fila 245 vigente o renovada | |
| Autorización de PII | Suscripción institucional apta para aprendices | |

Si en lugar de un RG entregan solo la suscripción con permiso para crearlo, usar la Fase 2.
Si la licencia de Azure está vencida y no hay renovación, no crear recursos con una
cuenta personal: evaluar el Plan B de [`solicitud_ti_azure.md`](solicitud_ti_azure.md).

## Fase 2 · Infraestructura (Azure Cloud Shell, bash)

Abrir <https://shell.azure.com> y ejecutar. Ajustar los nombres: la cuenta de
almacenamiento debe ser única, en minúsculas y sin guiones.

```bash
# --- variables ---
RG=rg-astin-consulta
LOCATION=eastus2
SWA=astin-consulta
STORAGE=astinconsulta2026
CONTAINER=consulta-privada
BLOB=consulta_web.json

az account show -o table
az group create -n "$RG" -l "$LOCATION"

# Almacenamiento privado, TLS 1.2 y sin acceso anónimo
az storage account create \
  -n "$STORAGE" -g "$RG" -l "$LOCATION" \
  --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# Rol de datos para poder crear el contenedor y generar el SAS con la sesión
ME=$(az ad signed-in-user show --query id -o tsv)
STORAGE_ID=$(az storage account show -n "$STORAGE" -g "$RG" --query id -o tsv)
az role assignment create --assignee "$ME" --role "Storage Blob Data Owner" --scope "$STORAGE_ID"

# Esperar 1-2 minutos a que propague el rol y crear el contenedor privado
az storage container create \
  --account-name "$STORAGE" -n "$CONTAINER" \
  --auth-mode login --public-access off

# Static Web App Standard
az staticwebapp create -n "$SWA" -g "$RG" -l "$LOCATION" --sku Standard

# Guardar el host: se usa en el redirect URI del registro de app
az staticwebapp show -n "$SWA" -g "$RG" --query defaultHostname -o tsv
```

Anotar el host resultante, por ejemplo `astin-consulta-xxxx.azurestaticapps.net`.

## Fase 3 · Entra ID (portal, lo hace una persona con permisos)

1. **Microsoft Entra ID > App registrations > New registration**
   - Nombre: `ASTIN Consulta Nominal`
   - Cuentas: **solo este directorio organizacional**
   - Redirect URI tipo **Web**: `https://<host>/.auth/login/aad/callback`
2. **Authentication**: activar **ID tokens**.
3. **Certificates & secrets > New client secret**: copiar el **Value** (no el Secret ID).
4. **App roles > Create app role** (opción sin Graph):
   - Display name: `Consulta nominal`
   - Value: `nominal`
   - Allowed member types: **Users/Groups**
5. **Microsoft Entra ID > Groups > New group**
   - Tipo **Security**, nombre `ASTIN-Inasistencias-Nominal`
   - Agregar solo a las personas autorizadas por Bienestar/Coordinación Académica
6. **Enterprise applications > ASTIN Consulta Nominal > Users and groups**: asignar el grupo al rol `nominal`.

Anotar:

| Dato | Valor |
|---|---|
| Application (client) ID | |
| Directory (tenant) ID | |
| Client secret **Value** | |
| Object ID del grupo | |

> Alternativa con grupos y Graph: conceder `User.Read.All` (delegado) con consentimiento
> de administrador y configurar `ENTRA_NOMINAL_GROUPS` en lugar de `ENTRA_NOMINAL_APP_ROLES`.
> Si el tenant bloquea ese consentimiento, quedarse con app roles.

## Fase 4 · Datos y configuración de la SWA

### 4.1 Subir el archivo nominal

Opción portal: **Storage account > Containers > consulta-privada > Upload** y seleccionar
`data/private/consulta_web.json`. Verificar que el nivel de acceso del contenedor siga en
**Private**.

Opción Cloud Shell (si se subió el archivo a la sesión):

```bash
az storage blob upload \
  --account-name "$STORAGE" -c "$CONTAINER" -n "$BLOB" \
  --file consulta_web.json --auth-mode login --overwrite
```

### 4.2 SAS de solo lectura y variables de la SWA

En Cloud Shell, sin pegar el SAS en ningún lado:

```bash
EXP=$(date -u -d "+180 days" '+%Y-%m-%dT%H:%MZ')
SAS=$(az storage blob generate-sas \
  --account-name "$STORAGE" -c "$CONTAINER" -n "$BLOB" \
  --permissions r --expiry "$EXP" --auth-mode login --as-user -o tsv)
BLOB_URL="https://$STORAGE.blob.core.windows.net/$CONTAINER/$BLOB?$SAS"

read -rp "Client ID: " CLIENT_ID
read -rsp "Client secret: " CLIENT_SECRET; echo
read -rp "Object ID del grupo: " GROUP_ID

az staticwebapp appsettings set \
  -n "$SWA" -g "$RG" \
  --setting-names \
    AZURE_CLIENT_ID="$CLIENT_ID" \
    AZURE_CLIENT_SECRET="$CLIENT_SECRET" \
    ENTRA_NOMINAL_APP_ROLES="nominal" \
    NOMINAL_ROLE="nominal" \
    AUTH_MODE="roles" \
    BLOB_CONTAINER="$CONTAINER" \
    BLOB_NAME="$BLOB" \
    CACHE_TTL_SECONDS="300" \
    BLOB_SAS_URL="$BLOB_URL"
```

> El SAS vence en 180 días. Anotar la fecha y rotarlo con el mismo comando.

## Fase 5 · Tenant y despliegue

1. Reemplazar `REPLACE_TENANT_ID` en `web/staticwebapp.config.json` por el Directory (tenant) ID.
2. Commit y push a `main`.
3. En GitHub: **Settings > Secrets and variables > Actions > New repository secret**
   - Nombre: `AZURE_STATIC_WEB_APPS_API_TOKEN`
   - Valor: `az staticwebapp secrets list -n "$SWA" -g "$RG" --query properties.apiKey -o tsv`
4. Ejecutar **Actions > Azure Static Web Apps > Run workflow** (o push a `main`).
5. Confirmar que el job `deploy` ya no dice "configure AZURE_STATIC_WEB_APPS_API_TOKEN".

## Fase 6 · Validación

- [ ] `https://<host>/consulta.html` sin sesión → redirige al login de Entra.
- [ ] Cuenta fuera del grupo → `acceso-denegado.html`, sin nombres.
- [ ] Cuenta dentro del grupo → tabla con nombres y filtros.
- [ ] `https://<host>/api/consulta` sin sesión → 401/403.
- [ ] Blob directo `https://<storage>.blob.core.windows.net/consulta-privada/consulta_web.json` → 403/404, nunca 200.
- [ ] DevTools > Network: `consulta.js`, `config.js`, `aggregate.js` y `demo_consulta.json` no contienen nombres reales.
- [ ] Exportar CSV pide confirmación y descarga `consulta_semanal_<fecha>.csv`.
- [ ] Logs de la API sin nombres, documentos ni justificaciones.
- [ ] Probar intervalo sin datos, ficha inexistente y búsqueda sin resultados.

## Fase 7 · Rollback

| Qué | Cómo |
|---|---|
| Front/API | Redesplegar un commit anterior desde Actions |
| Datos | Subir la versión previa del Blob o reexportar con el ETL |
| Auth | Corregir el registro de app; no desactivar `rolesSource` sin otro control |
| Backend propio | `az staticwebapp backends unlink -n "$SWA" -g "$RG"` |

## Costos de referencia

- **Static Web Apps Standard**: aproximadamente USD 9/mes (verificar calculadora).
- **Storage**: centavos; el archivo real pesa ~2,8 MB.
- **Entra ID**: sin costo para el registro y el grupo (asignación a grupos puede requerir P1/P2 según el tenant).
