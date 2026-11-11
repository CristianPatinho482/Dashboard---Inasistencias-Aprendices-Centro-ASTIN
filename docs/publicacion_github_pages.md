# Publicación del portal en GitHub Pages

## Publicación en el repositorio actual

El generador `scripts/04_generar_portal_html.py` escribe el portal actualizado en:

- `outputs/portal_astin.html`: copia para abrir localmente.
- `github-pages/index.html`: copia lista para publicar como sitio.
- `index.html`: página principal de la rama `main`, origen que usa la URL actual de Pages.

La carpeta `github-pages` contiene solo el HTML autocontenido. Chart.js, el logo y los datos agregados están dentro de `index.html`; no se necesitan rutas locales, Excel, CSV ni dependencias web al visitar el sitio.

## Configuración del sitio

La URL actual estaba configurada para publicar `main` desde la raíz. Si el repositorio se hace privado, GitHub Pages solo funciona con un plan de GitHub que lo permita; para la versión institucional se recomienda Azure Static Web Apps. Si se usa otro repositorio, copie solo el contenido de `github-pages` y seleccione `main` → `/(root)` en **Settings → Pages**.

Consulte la [documentación oficial para configurar el origen de publicación](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Actualizar los datos del portal

GitHub Pages no lee el Excel ni se actualiza cuando cambia el archivo local. Para publicar manualmente una nueva versión:

1. Ejecute `scripts/actualizar_datos.ps1` en el proyecto con el archivo de inasistencias actualizado.
2. Revise el portal local y `data/processed/00_resumen_etl.json`.
3. Envíe el nuevo `index.html` de la raíz a `main`.
4. GitHub Pages publicará la versión correspondiente al nuevo commit.

Para combinar ETL y publicación en una operación, ejecute `scripts/actualizar_datos.ps1 -PublicarPortal`. Para que ocurra después de cada descarga, programe ese comando en el Programador de tareas de Windows con una cuenta que tenga OneDrive sincronizado y autenticación Git configurada. Consulte [automatización del reporte](automatizacion.md).

## Privacidad y alcance

El portal contiene datos agregados por programa, mes, motivo, ficha con muestra mínima y nivel de riesgo. Aunque excluye nombres y documentos, los resultados son información institucional y podrían ser sensibles. GitHub Pages es accesible públicamente; el repositorio debe ser privado y no debe contener `data/`. Si el historial ya publicó `data/restricted`, `data/raw` o salidas con nombres, trate el dato como comprometido y ejecute el procedimiento de purga descrito en [automatización](automatizacion.md#0-datos-git-y-privacidad).

## Datos personales y consulta nominal

La vista nominal con nombres de aprendices **no** se publica en GitHub Pages. `outputs/consulta_interna.html` se genera solo localmente, está excluido de Git y no debe copiarse al repositorio. La versión web autorizada es `web/consulta.html` en Azure Static Web Apps, protegida por Entra ID, el rol `nominal` y un Blob privado. Consulte [la guía de Azure](azure_static_web_apps.md).

