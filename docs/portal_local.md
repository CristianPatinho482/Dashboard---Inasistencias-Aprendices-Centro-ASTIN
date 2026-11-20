# Portal local completo con la página 05 nominal

Este modo reemplaza la publicación en Azure como ruta principal de entrega. Genera
un **único archivo HTML autocontenido** con las seis vistas del portal, incluida la
página **05 · Consulta semanal** con nombres de aprendices. El archivo se abre con
doble clic en el equipo del instructor o coordinador autorizado, sin servidor web y
sin conexión a Internet.

> **Regla de oro:** el HTML local contiene datos personales. No se versiona, no se
> publica, no se comparte por correo, chat, WhatsApp ni almacenamiento en la nube
> abierto. Úselo solo en el equipo autorizado y bórrelo cuando termine la revisión.

## 1. Qué incluye

| Vista | Contenido | Datos sensibles |
|---|---|---|
| 00 · Inicio | KPIs, tendencia mensual, justificación, fichas y programas | No |
| 01 · Caracterización | Riesgo por aprendiz, programas y líneas de formación | No |
| 02 · Fichas y programas en riesgo | Índice de riesgo y priorización | No |
| 03 · Análisis detallado | Programas, motivos y participación | No |
| 04 · Calidad de datos | Duplicados, revisión, cobertura y límites | No |
| 05 · Consulta semanal | Filtros por ficha, instructor, fechas y búsqueda; KPIs; semáforo; CSV | **Sí** |

Las cinco primeras vistas son las mismas del portal agregado. La página 05 se
calcula con la lógica compartida `api/src/shared/aggregate.js`, la misma que usan la
API y el navegador, para que el semáforo y los totales coincidan.

## 2. Requisitos

- Python 3.10 o superior con las dependencias del ETL (`pandas`, `xlrd`).
- El archivo de inasistencias ya descargado en la carpeta de OneDrive configurada.
- `data/processed/FACT_INASISTENCIAS.csv` y `data/restricted/DIM_APRENDIZ_PII.csv`
  generados por el ETL. Ambos están excluidos de Git.
- Chart.js local en `tools/chartjs/chart.umd.min.js` (ya incluido en el proyecto).

## 3. Generación manual

Desde PowerShell, en la carpeta del proyecto:

```powershell
python .\scripts\12_generar_portal_local.py
```

Salida:

```text
outputs\portal_local_completo.html
```

El comando informa el número de registros, aprendices, rango de fechas y tamaño.
El archivo queda excluido por `.gitignore` mediante `/outputs/portal_local*.html`.

Para abrirlo:

```powershell
Start-Process .\outputs\portal_local_completo.html
```

También puede abrirlo con doble clic desde el Explorador de Windows. No necesita
`localhost`, un servidor HTTP ni conexión a Internet: los datos, Chart.js, el logo
y la lógica de consulta están embebidos en el mismo HTML.

## 4. Generación automática

`scripts/actualizar_datos.ps1` ejecuta el ETL y, al final del pipeline, genera el
portal local completo:

```powershell
.\scripts\actualizar_datos.ps1
```

El pipeline actual es:

1. `01_etl_modelo_estrella.py`
2. `02_generar_modelo_tmdl.py`
3. `03_generar_reporte_pbir.py`
4. `04_generar_portal_html.py`
5. `05_generar_consulta_interna.py` (vista nominal de apoyo, legado)
6. `10_sincronizar_agregacion.py`
7. `12_generar_portal_local.py` (portal completo)

Si la tarea programada usa `-SoloSiFuenteNueva`, el portal solo se regenera cuando
el archivo de OneDrive cambió. Para forzar una actualización manual, ejecute el
pipeline sin ese parámetro.

## 5. Demostración sintética

Para revisar la interfaz sin datos reales:

```powershell
python .\scripts\12_generar_portal_local.py --demo
```

Salida:

```text
outputs\portal_local_demo.html
```

Usa `web/data/demo_consulta.json` (453 registros y 72 aprendices sintéticos). Este
archivo sí puede compartirse para revisión de interfaz, pero no debe presentarse
como información institucional.

## 6. Uso de la página 05

1. Abra el portal y seleccione **05 · Consulta semanal** en la barra lateral.
2. Elija ficha, instructor, fecha inicial y fecha final. La búsqueda filtra por
   nombre o parte del nombre.
3. Revise los KPIs: aprendices únicos, inasistencias, horas totales y horas no
   justificadas.
4. El semáforo usa la **peor semana del intervalo**:
   - **Verde:** menos de 12 h no justificadas.
   - **Amarillo:** de 12 a 16 h inclusive.
   - **Rojo:** más de 16 h no justificadas.
5. **Exportar CSV** descarga únicamente las filas del filtro actual. El navegador
   pide confirmación porque el archivo contiene nombres y datos personales.
6. **Restablecer** vuelve a todas las fichas, instructores y al rango completo.

La tabla muestra 100 filas por página; el botón **Mostrar más** agrega otras 100.
El conteo inferior distingue parejas aprendiz/ficha, por eso puede ser mayor que
el KPI de aprendices únicos.

## 7. Seguridad y privacidad

- El HTML local se escribe en `outputs/`, fuera de `web/`, `data/` y del sitio
  publicable.
- El generador rechaza rutas de salida dentro de `web/`, `data/`, `api/` o
  `github-pages/`.
- `data/`, `data/private/`, `data/restricted/`, `outputs/consulta_interna.html` y
  `outputs/portal_local*.html` están excluidos de Git.
- El portal agregado (`web/index.html`, `index.html`, `outputs/portal_astin.html`)
  sigue sin PII y puede publicarse.
- No envíe el HTML local por canales abiertos ni lo deje en equipos compartidos.
- Use un equipo institucional con inicio de sesión, disco cifrado y bloqueo de
  pantalla.
- Al terminar, borre las copias locales:

  ```powershell
  .\scripts\11_limpiar_consulta_local.ps1
  ```

  El script pide confirmación con la palabra `BORRAR` y también revisa que no haya
  datos reales dentro de `web/`.

## 8. Actualización de datos

Ciclo recomendado:

1. El bot o el usuario descarga el archivo de inasistencias en la carpeta de
   OneDrive.
2. Se ejecuta `scripts/actualizar_datos.ps1` (manual o por tarea programada).
3. El ETL regenera `data/processed/` y `data/restricted/`.
4. El paso 12 regenera `outputs/portal_local_completo.html` con el corte nuevo.
5. El instructor o coordinador abre el HTML local y revisa la página 05.
6. Al terminar, borra el HTML local si ya no lo necesita.

El encabezado del portal muestra la fecha de última descarga. La página 05 muestra
la fecha de corte del ETL y el intervalo consultado.

## 9. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `No existe ...FACT_INASISTENCIAS.csv` | El ETL no se ha ejecutado | Ejecute `scripts/actualizar_datos.ps1` o `01_etl_modelo_estrella.py` |
| `No existe ...DIM_APRENDIZ_PII.csv` | El ETL no generó la tabla restringida | Revise que el archivo fuente tenga nombres y vuelva a ejecutar el ETL |
| La página 05 no muestra nombres | El HTML se generó con `--demo` o sin registros | Genere el portal real con `12_generar_portal_local.py` |
| El navegador bloquea la descarga CSV | Política del equipo | Permita la descarga para el archivo local o use otro navegador institucional |
| Los filtros no devuelven filas | Combinación de ficha, instructor y fechas | Use **Restablecer** y ajuste el intervalo |
| El archivo no abre en otro equipo | Ruta o política de ejecución | Copie el HTML por un canal autorizado o genérelo en el equipo destino |

## 10. Relación con Azure

La publicación en Azure Static Web Apps queda como referencia histórica y Plan B.
El bloqueo actual es de licenciamiento institucional: la fila 245 del catálogo de
TI registra **Microsoft Azure** con vigencia 2024-05-31. Mientras no haya una
suscripción institucional autorizada para PII, el modo local es la entrega
principal.

- Arquitectura y runbook: [`azure_static_web_apps.md`](azure_static_web_apps.md) y
  [`checklist_publicacion_azure.md`](checklist_publicacion_azure.md).
- Sustento ante TI: [`solicitud_ti_azure.md`](solicitud_ti_azure.md).

## Referencias

- Generador: [`scripts/12_generar_portal_local.py`](../scripts/12_generar_portal_local.py)
- Agregación compartida: [`api/src/shared/aggregate.js`](../api/src/shared/aggregate.js)
- Portal agregado: [`scripts/04_generar_portal_html.py`](../scripts/04_generar_portal_html.py)
- Limpieza local: [`scripts/11_limpiar_consulta_local.ps1`](../scripts/11_limpiar_consulta_local.ps1)
