# Incidente de exposición de datos personales · 11 de noviembre de 2026

Registro de respuesta al haber estado público el repositorio
`CristianPatinho482/Dashboard---Inasistencias-Aprendices-Centro-ASTIN` con
datos personales en su historial. Este documento no contiene nombres,
documentos, identificadores de aprendices ni textos de justificación.

## 1. Situación

- El repositorio estuvo público y su historial incluía `data/restricted/DIM_APRENDIZ_PII.csv`, `data/raw/Inasistencias.xls` y los CSV procesados del ETL.
- El historial también versionaba `CaracterizacionAprendicesASTIN.SemanticModel/.pbi/cache.abf`, una copia local del modelo que puede contener los datos cargados, y los `localSettings.json` de Power BI.
- El 11 de noviembre de 2026 se cambió la visibilidad a privada antes de reescribir el historial.
- Se ejecutó dos veces `scripts/09_limpiar_pii_git.ps1` con `git-filter-repo`: la primera eliminó las rutas `data/`; la segunda eliminó además `cache.abf` y los `localSettings.json`. Se hizo push forzado de todas las ramas y etiquetas.
- Se eliminó el artefacto `github-pages` (54 MB) generado antes de la purga, que podía contener `data/`.
- GitHub Pages quedó deshabilitado; la URL anterior devuelve 404.
- El 11 de noviembre de 2026, después de la segunda purga, `main` quedó en `f1e9d24`.

## 2. Verificación realizada

- Clon espejo nuevo del remoto: 0 rutas `data/`, 0 rutas `**/.pbi/cache.abf` o `**/.pbi/localSettings.json` y 0 objetos `DIM_APRENDIZ_PII.csv`, `Inasistencias.xls`, `cache.abf` o `localSettings.json` en todas las ramas.
- Acceso anónimo al repositorio, al contenido raw y a GitHub Pages: 404.
- Repositorio privado, 0 forks, 1 colaborador (el propietario), 0 invitaciones, 0 deploy keys, 0 hooks y 0 releases.
- Artefactos de Actions: 0.
- Auditoría de los 1143 archivos versionados: sin nombres, documentos, IDs de aprendices ni instructores reales.
- Escaneo de secretos en el árbol actual: sin patrones de claves, tokens de GitHub, cadenas de conexión ni SAS.

## 3. Pendiente

1. **GitHub Support:** solicitar la purga de vistas en caché, objetos inaccesibles y artefactos/cachés asociados a los commits antiguos, incluidos `3ea43110379f01d89eb2d234b91dadb8e01f23fb` y el commit donde se introdujo `cache.abf` (`21d2e99`). Mientras no se complete, una persona con acceso al repositorio todavía puede consultar esos commits por su SHA.
2. **Privacidad/seguridad SENA:** notificar el incidente y activar el protocolo institucional. Tratar el dato como comprometido: la visibilidad privada y la reescritura no recuperan copias ya descargadas.
3. **Secretos:** revisar y rotar cualquier credencial que haya estado en el repositorio o en su historial. No se identificaron secretos en el árbol actual; verifique el historial antiguo y los respaldos.
4. **Respaldos locales:** conservarlos en almacenamiento cifrado con acceso restringido, fuera del repositorio, o destruirlos cuando ya no sean necesarios. Los respaldos de `%TEMP%` contienen `data/`, `cache.abf` y los `localSettings.json`; no los restaure en Git. El respaldo de la segunda purga es `astin_repo_backup_20261111_145013`.
5. **Clones y copias:** revisar equipos y unidades sincronizadas; no es posible borrar copias ya descargadas por terceros.

## 4. Plantilla para GitHub Support

Canal: <https://support.github.com/contact> (requiere la cuenta propietaria).

Asunto:

```text
Request to purge cached views and unreachable objects after PII removal
```

Cuerpo:

```text
Repository: CristianPatinho482/Dashboard---Inasistencias-Aprendices-Centro-ASTIN

The repository was public and its Git history contained personal data
(data/restricted/DIM_APRENDIZ_PII.csv and data/raw/Inasistencias.xls). It
also contained CaracterizacionAprendicesASTIN.SemanticModel/.pbi/cache.abf,
a Power BI model cache that may contain the loaded data, and Power BI
localSettings.json files.

The repository was made private on 2026-11-11. I rewrote all branches and
tags twice with git-filter-repo: first to remove every data/ path, then to
remove cache.abf and localSettings.json, and force-pushed all references.
A fresh mirror clone of the remote (current main f1e9d24) contains no data/
paths, no cache.abf or localSettings.json, and no objects named
DIM_APRENDIZ_PII.csv, Inasistencias.xls, cache.abf or localSettings.json.
The old GitHub Pages artifact was deleted and Pages is disabled.

Please purge cached views and unreachable objects associated with the old
history, including the original commit
3ea43110379f01d89eb2d234b91dadb8e01f23fb and the commit that introduced
cache.abf (21d2e99), and any retained build artifacts or caches for this
repository.

I understand that this does not affect copies already cloned or downloaded
by third parties. Please confirm when the purge is complete and whether any
additional action is required.
```

## 5. Plantilla de notificación interna

Para el contacto de privacidad/seguridad o la oficina de protección de datos
del SENA. Ajuste los datos del remitente y del comité.

```text
Asunto: Notificación de incidente de exposición de datos personales · Centro ASTIN

Se informa que el repositorio institucional de analítica del Centro ASTIN
estuvo público con archivos de datos personales en su historial de Git
(nombres y documentos de aprendices, además del archivo fuente de
inasistencias). El historial también incluía una cache local del modelo de
Power BI y archivos de configuración local. El repositorio se hizo privado el
11 de noviembre de 2026, se reescribió el historial para eliminar las rutas
data/ y esos archivos locales de todas las ramas y etiquetas, se hizo push
forzado y se eliminó el artefacto de GitHub Pages que podía contener esos
archivos. Un clon espejo del remoto ya no contiene las rutas ni los objetos
restringidos, el acceso anónimo devuelve 404 y no hay forks.

Queda pendiente la purga de cachés y objetos inaccesibles por parte de
GitHub Support y la revisión de copias locales o descargadas. Se solicita
activar el protocolo de privacidad, indicar el canal para conservar las
evidencias y confirmar si se requiere rotación de credenciales o una
notificación adicional a los titulares. El detalle técnico y las plantillas
están en docs/incidente_pii_2026-11-11.md.
```

## 6. Evidencia y reproducción

- `scripts/09_limpiar_pii_git.ps1`: reescritura, verificación y push forzado.
- `scripts/08_subir_consulta_azure.ps1`: carga del archivo nominal al Blob privado.
- `docs/automatizacion.md`: flujo de datos, Git y privacidad.
- `docs/azure_static_web_apps.md`: arquitectura y controles de la consulta nominal.

Comandos de verificación usados sobre un clon espejo:

```powershell
git clone --mirror <url-del-repositorio> repo_mirror.git
git -C repo_mirror.git log --all --name-only --pretty=format: |
  Where-Object { $_ -match '^data/|(^|/)\.pbi/(cache\.abf|localSettings\.json)$' }
git -C repo_mirror.git rev-list --objects --all |
  Select-String 'DIM_APRENDIZ_PII|Inasistencias\.xls|\.pbi/(cache\.abf|localSettings\.json)'
```

Ambos comandos deben devolver cero resultados. No imprima el contenido de los
archivos restringidos durante la verificación.
