# Automatización del reporte

## Flujo común de datos

El bot sobrescribe el archivo fijo `Inasistencias.xls` en la carpeta OneDrive configurada en `scripts/actualizar_datos.ps1`. La automatización local ejecuta ETL, regenera dimensiones y hechos, reconstruye el PBIR, el portal agregado y la vista nominal local `outputs/consulta_interna.html`. La salida nominal está excluida de Git y no se publica. La fecha `ultima_descarga` del resumen toma la última modificación del archivo sincronizado; `corte` conserva la máxima `Fecha Fin` dentro de los datos. Así se distinguen descarga y periodo analizado.

La carpeta OneDrive debe estar sincronizada localmente en el equipo que ejecuta el ETL. La página nominal de Power BI combina el nombre desde `data/restricted/DIM_APRENDIZ_PII.csv`; esa consulta se mantiene local y el HTML público no la incluye.

## 1. Portal GitHub Pages

El portal es estático: GitHub Pages no lee OneDrive ni ejecuta el ETL. El proceso local debe crear el nuevo `index.html` y enviarlo al repositorio.

Para una actualización manual, ejecute desde PowerShell en la carpeta del proyecto:

```powershell
.\scripts\actualizar_datos.ps1 -PublicarPortal
```

El parámetro `-PublicarPortal` crea un commit únicamente para `index.html` y hace `git push origin main` si el archivo cambió. Requiere que Git esté configurado y que `git push origin main` funcione sin solicitar entrada interactiva.

Para programarlo, cree una tarea en **Programador de tareas de Windows** que se ejecute después de la descarga del bot. Use `powershell.exe` como programa, la carpeta del proyecto como **Iniciar en** y estos argumentos:

```text
-NoProfile -ExecutionPolicy Bypass -File "C:\Users\capatino\Documents\Inasistencias Sofía Plus\scripts\actualizar_datos.ps1" -PublicarPortal
```

Configure la tarea con la cuenta que tiene acceso a OneDrive y GitHub, y mantenga el equipo encendido, conectado a Internet y con OneDrive sincronizado. GitHub Pages publicará el commit que contenga el nuevo `index.html`.

## 2. Power BI Desktop local

El pipeline regenera los CSV que consume el modelo y reconstruye las definiciones PBIR/TMDL. La barra inferior del informe ahora obtiene la fecha de corte y los registros válidos de medidas DAX globales, de modo que cambian al actualizar el modelo. Después de que el pipeline regenere el PBIR/TMDL, cierre y vuelva a abrir el PBIP una vez para cargar la nueva estructura; luego use **Inicio > Actualizar**. En las siguientes actualizaciones, las dos tarjetas cambian con el refresco de datos.

Para un flujo desatendido, no se recomienda automatizar clics de la interfaz de Desktop. Use el servicio de Power BI como destino de actualización programada, conectado a los CSV generados mediante gateway o a una ubicación cloud compatible.

## 3. Power BI Service

El modelo actual lee CSV locales mediante `File.Contents` y los parámetros `RutaDatos` y `RutaDatosRestringidos`. El servicio no ejecuta el script Python que transforma el Excel. La nueva página nominal debe publicarse solo en un espacio institucional con autenticación y permisos adecuados; GitHub Pages de este repositorio es público y no sirve para mostrar nombres de aprendices. Hay dos arquitecturas para datos internos:

### Mantener ETL local y usar gateway

1. El Programador de tareas ejecuta el ETL desde el archivo OneDrive sincronizado.
2. Instale y mantenga activo un gateway en ese equipo o servidor.
3. Configure el origen de archivos/carpeta que usa `RutaDatos` (`data/processed`) en el gateway con la misma ruta y credenciales.
4. Publique el modelo y asocie el origen del modelo al gateway.
5. Programe el refresco del modelo en Power BI Service para después de la tarea ETL.

El equipo que aloja el gateway debe estar encendido y el gateway en línea cuando ocurra el refresco.

### Migrar las salidas ETL a SharePoint/OneDrive cloud

La conexión SharePoint quedó implementada en el generador del modelo. Sitio informado por el equipo: `https://sena4.sharepoint.com/teams/EquipoASTIN-DESAROLLOSPOWER-BI`. La carpeta todavía debe crearse en la biblioteca de documentos del equipo; se propone `PowerBI_Salidas` como carpeta plana para los CSV y el resumen ETL.

1. En SharePoint, cree `PowerBI_Salidas` dentro de la biblioteca del equipo y agréguela/sincronícela con OneDrive en el equipo que ejecuta el ETL.
2. Copie `config/sharepoint.example.json` como `config/sharepoint.json` y complete:
   - `mode`: `SharePoint`.
   - `site_url`: la URL del sitio indicada arriba.
   - `processed_folder_url`: la ruta de carpeta canónica que reporta el conector `SharePoint.Files` (debe terminar en `/`); el enlace de compartir con tokens no sirve.
   - `local_sync_folder`: ruta local de la carpeta `PowerBI_Salidas` sincronizada en el equipo.
3. Ejecute `.scripts\actualizar_datos.ps1 -CopiarSalidasSharePoint`. El proceso regenera las salidas y copia solo los seis archivos permitidos. No copia `DIM_APRENDIZ_PII.csv` y deja vacíos nombre, iniciales y documento enmascarado en la dimensión publicada. Espere el icono de sincronización completada de OneDrive.
4. Ejecute `python .\scripts\02_generar_modelo_tmdl.py` (el pipeline ya lo ejecuta) para generar las consultas `SharePoint.Files`; abra el PBIP, inicie sesión con **Cuenta organizativa**, actualice y valide todas las páginas.
5. Publique en el espacio de trabajo institucional. En Power BI Service configure la conexión OAuth organizacional de SharePoint y la actualización programada; no configure gateway para esta fuente cloud.

El PBIP en modo SharePoint no carga nombres ni documentos, por decisión de no copiar la salida restringida. La página `05 Consulta semanal` cambia a un código seudónimo de aprendiz, conserva ficha/instructor/fechas y el semáforo, y evita mostrar nombre, iniciales o documento. El código sigue siendo información sensible seudonimizada: publique solo en el espacio institucional autorizado. El portal GitHub Pages conserva datos agregados y no consulta SharePoint.

Para volver al modelo local, cambie `mode` a `Local` en la configuración privada y regenere el modelo. Nunca agregue `config/sharepoint.json` al repositorio: puede contener rutas internas, aunque no contraseñas.

Esta alternativa elimina la dependencia de que Service lea una ruta local, pero requiere cambiar y validar las consultas M del modelo. El refresco de OneDrive de un archivo PBIX sincroniza el archivo/modelo; por sí solo no ejecuta este ETL Python.

## Alcance y operación

- La ejecución local puede automatizar ETL y generación de artefactos, pero la carpeta de OneDrive debe estar disponible y terminar de sincronizar antes de la tarea.
- `-PublicarPortal` publica los agregados de `index.html` en el repositorio GitHub configurado. Compruebe la autorización institucional antes de exponer datos públicamente.
- El equipo genera la fecha de última descarga a partir de la fecha de modificación local del Excel. Si el bot/OneDrive conserva una fecha de modificación anterior, el bot deberá actualizar esa marca o proporcionar un archivo de control con la hora real de descarga.
- La programación del Service depende del tipo de origen, gateway y capacidad/licencia del espacio de trabajo.
- El repositorio público actual incluye una carpeta `data/restricted`; no use la visibilidad del repositorio como mecanismo de protección para esos archivos.
