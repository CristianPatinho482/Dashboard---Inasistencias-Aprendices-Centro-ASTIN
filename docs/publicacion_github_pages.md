# Publicación del portal en GitHub Pages

## Publicación en el repositorio actual

El generador `scripts/04_generar_portal_html.py` escribe el portal actualizado en:

- `outputs/portal_astin.html`: copia para abrir localmente.
- `github-pages/index.html`: copia lista para publicar como sitio.
- `index.html`: página principal de la rama `main`, origen que usa la URL actual de Pages.

La carpeta `github-pages` contiene solo el HTML autocontenido. Chart.js, el logo y los datos agregados están dentro de `index.html`; no se necesitan rutas locales, Excel, CSV ni dependencias web al visitar el sitio.

## Configuración del sitio

La URL actual ya está configurada para publicar `main` desde la raíz y ya contiene `index.html`. GitHub Pages despliega la nueva versión al recibir un commit en esa rama. Si se usa otro repositorio, copie solo el contenido de `github-pages` y seleccione `main` → `/(root)` en **Settings → Pages**.

Consulte la [documentación oficial para configurar el origen de publicación](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Actualizar los datos del portal

GitHub Pages no lee el Excel ni se actualiza cuando cambia el archivo local. Para publicar manualmente una nueva versión:

1. Ejecute `scripts/actualizar_datos.ps1` en el proyecto con el archivo de inasistencias actualizado.
2. Revise el portal local y `data/processed/00_resumen_etl.json`.
3. Envíe el nuevo `index.html` de la raíz a `main`.
4. GitHub Pages publicará la versión correspondiente al nuevo commit.

Para combinar ETL y publicación en una operación, ejecute `scripts/actualizar_datos.ps1 -PublicarPortal`. Para que ocurra después de cada descarga, programe ese comando en el Programador de tareas de Windows con una cuenta que tenga OneDrive sincronizado y autenticación Git configurada. Consulte [automatización del reporte](automatizacion.md).

## Privacidad y alcance

El portal contiene datos agregados por programa, mes, motivo, ficha con muestra mínima y nivel de riesgo. Aunque excluye nombres y documentos, los resultados son información institucional y podrían ser sensibles. GitHub Pages es accesible públicamente. El repositorio actual también contiene `data/restricted`; esa carpeta no forma parte del HTML, pero está dentro de un repositorio público y requiere atención independiente. Consulte la [advertencia oficial de GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).
# Datos personales y páginas de consulta nominal

GitHub Pages de este proyecto es público. El dashboard agregado puede publicarse en ese sitio, pero `outputs/consulta_interna.html` incluye nombres y datos de inasistencia por aprendiz: se genera solo localmente, está excluido de Git y no debe copiarse al repositorio ni publicarse en GitHub Pages. Para compartir esta vista, úsese un portal institucional con autenticación y permisos; el carácter interno del enlace por sí solo no restringe su acceso.
