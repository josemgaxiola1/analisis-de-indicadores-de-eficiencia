# Contexto del proyecto — Proyecto Metas

## 1. PROYECTO

**Nombre:** Proyecto Metas
**Repositorio:** https://github.com/josemgaxiola1/analisis-de-indicadores-de-eficiencia (público)
**App desplegada:** https://metas-indicadores-eficiencia.streamlit.app (Streamlit Community Cloud)
**Directorio local:** `c:\Users\Jose Mario Gaxiola\Proyecto Metas`

**Propósito:** Dashboard y sistema de reportes que analiza el cumplimiento mensual de metas (Ventas, Inventario, Rentabilidad) de las sucursales de dos unidades de negocio — **Calzapato** (70 sucursales) y **Kelder** (55 sucursales) — de Enero a Junio 2026. Cada sucursal recibe "estrellas" mensuales (0-9) según cumplimiento de metas. El sistema consolida los 6 meses, clasifica sucursales por desempeño, detecta tendencias y genera material (dashboard interactivo, imagen ejecutiva PNG, Excel) para solicitar apoyo a dirección sobre las sucursales con peor desempeño.

**Stack tecnológico:**
- Python 3.13, entorno virtual en `.venv/`
- **Streamlit 1.60.0** — dashboard web interactivo
- **pandas 3.0.5** — procesamiento de datos
- **openpyxl 3.1.5** — lectura/escritura de Excel
- **plotly 6.9.0** — gráficos interactivos en el dashboard
- **matplotlib 3.11.1** — generación de imagen estática del reporte ejecutivo (instalado pero **no está en `requirements.txt`** porque no lo usa `app.py`, solo scripts standalone — ver sección 6)
- Git + GitHub, desplegado en Streamlit Community Cloud (auto-deploy on push a `main`)

## 2. ESTRUCTURA

```
Proyecto Metas/
├── app.py                              # Dashboard Streamlit (entry point)
├── requirements.txt                    # Dependencias para Streamlit Cloud
├── data/
│   └── raw/
│       ├── Enero.xlsx ... Junio.xlsx    # Datos crudos Calzapato (70 sucursales)
│       └── KELDER/
│           ├── enero.xlsx ... Junio.xlsx # Datos crudos Kelder (55 sucursales)
│                                          # OJO: capitalización inconsistente en nombres
│                                          # de archivo (mezclan mayúsc/minúsc) — manejado
│                                          # con búsqueda case-insensitive en el loader
├── src/services/
│   ├── data_loader.py                  # Núcleo: carga, clasifica, calcula tendencias
│   ├── reporte_ejecutivo.py            # Genera imagen PNG tipo "one-pager" ejecutivo
│   └── reporte_excel.py                # Genera Excel de salida con 4 hojas
└── reports/                             # Salidas generadas (PNG y XLSX), trackeadas en git
    ├── reporte_ejecutivo.png            # Calzapato
    ├── reporte_ejecutivo_kelder.png     # Kelder
    ├── Analisis_Metas_Enero_Junio.xlsx
    └── Analisis_Metas_Kelder_Enero_Junio.xlsx
```

### Qué hace cada módulo

**`src/services/data_loader.py`** (el corazón del proyecto):
- `UNIDADES` (dict): mapea nombre de unidad de negocio → carpeta de datos (`{"Calzapato": "data/raw", "Kelder": "data/raw/KELDER"}`). Punto único para agregar nuevas unidades de negocio en el futuro.
- `_resolver_archivo(mes, data_dir)`: busca el archivo `.xlsx` de un mes sin importar mayúsculas/minúsculas (necesario porque Kelder trae nombres inconsistentes: `Junio.xlsx` pero `enero.xlsx`).
- `_leer_mes(mes, data_dir)`: lee un Excel, se queda solo con las columnas relevantes (por posición, `iloc`), renombra a nombres en español, agrega columnas `Mes` y `Mes Orden`.
- `cargar_todos_los_meses(data_dir)`: concatena los 6 meses en un solo DataFrame.
- `clasificar_sucursales(df)`: agrupa por sucursal, calcula promedios, clasifica en 4 categorías por **cuartiles usando rank(pct=True, method="first")** (no por umbral fijo — ver sección 4), y añade tendencia + métrica débil.
- `_tendencia_por_sucursal(df)`: compara promedio de estrellas del primer trimestre (Ene-Mar) vs segundo (Abr-Jun) → etiqueta "📈 Mejorando" / "📉 Empeorando" / "➡️ Estable" (umbral: diferencia ≥ 0.5 o ≤ -0.5).
- `_metrica_debil_por_sucursal(resumen)`: para cada sucursal, compara sus promedios de Ventas/Inventario/Rentabilidad contra el promedio de **toda la cadena en esa misma métrica** (no contra un umbral fijo — ver sección 4) y lista cuáles están por debajo.

**`app.py`** (dashboard Streamlit):
- Selector de Unidad de Negocio (Calzapato/Kelder) vía `UNIDADES`.
- Filtros de Mes y Sucursal (multiselect).
- KPIs generales, gráfico de evolución de estrellas (plotly), gráfico de clasificación por categoría, tabla de seguimiento de sucursales en "Revisión" (con tendencia y métrica débil), tabla pivote de estrellas por mes, y tabla de detalle completo.

**`src/services/reporte_ejecutivo.py`**:
- `generar_reporte(data_dir, salida, unidad)`: genera un PNG con matplotlib — título, 5 tarjetas KPI (promedio, # en Revisión, # empeorando, mejor sucursal, peor sucursal), gráfico de línea de evolución, tabla de sucursales en Revisión coloreada por tendencia, y un recuadro de conclusión/solicitud de apoyo.
- Sigue convenciones de la skill de dataviz del proyecto: paleta de "status" (verde/amarillo/naranja/rojo) reservada solo para las 4 categorías de desempeño, nunca reutilizada como color categórico.
- Ejecutable standalone (`python -m src.services.reporte_ejecutivo`) — genera ambos reportes (Calzapato y Kelder) en un solo run.

**`src/services/reporte_excel.py`**:
- `generar_excel(data_dir, salida)`: genera un `.xlsx` con 4 hojas: Resumen Ejecutivo, Sucursales en Revisión (con evolución mensual), Clasificación Completa (70/55 sucursales coloreadas por categoría), Datos Detalle (6 meses crudo).
- Ejecutable standalone igual que el anterior, genera ambas unidades en un run.

## 3. ESTADO ACTUAL

**Terminado y funcionando:**
- Carga y consolidación de datos de 6 meses (Ene-Jun) para Calzapato y Kelder.
- Clasificación en 4 niveles (Excelente/Cumple/Más o menos/Revisión) por cuartiles.
- Detección de tendencia trimestral y métrica débil por sucursal.
- Dashboard Streamlit desplegado y funcionando en producción, con selector de unidad de negocio.
- Generación de reporte ejecutivo PNG y Excel para ambas unidades.
- Correos de solicitud de apoyo ya enviados a dirección para **Calzapato** (31 jul) y **Kelder** (en curso, texto ya redactado, pendiente de que el usuario lo mande manualmente — no tengo acceso a Gmail en esta sesión).
- Repo público en GitHub con auto-deploy a Streamlit Cloud configurado y verificado.

**A medias / pendiente de decisión:**
- **Julio**: el usuario intentó mandar datos de Julio dos veces. La primera vez pegó una tabla con formato completamente distinto (Meta Mensual, Importe 2026, % Alcance vs 2025/2024 — sin estrellas/inventario/rentabilidad) que resultó ser un error del usuario (dijo "me equivoqué, eso no es") — **no se usó ni se guardó**. La segunda vez dijo que aún no tiene toda la info de Julio lista. **No hay archivo de Julio ni para Calzapato ni para Kelder todavía.**
- `reports/Analisis_Metas_Kelder_Enero_Junio.xlsx` tiene cambios sin commitear (aparece "modified" en `git status`) — probablemente por haberse abierto/regenerado localmente después del último push. Falta decidir si se vuelve a commitear.

**Pendiente (no iniciado):**
- Integrar Julio cuando el usuario tenga el archivo completo (mismo formato que Ene-Jun).
- No hay tests automatizados en el proyecto.

## 4. DECISIONES TÉCNICAS IMPORTANTES

1. **Clasificación por cuartiles relativos, no por umbral fijo de estrellas.**
   Por qué: el máximo teórico son 9 estrellas, pero en la práctica casi ninguna sucursal lo alcanza (la media real de la cadena es ~2.5/9). Un corte fijo (ej. "Excelente = 7+") habría dejado casi todas las sucursales en "Revisión", sin poder discriminar desempeño real. Se usa `rank(pct=True)` sobre el promedio de estrellas de las propias sucursales, dividiendo en cuartiles (25% Revisión, 25% Más o menos, 25% Cumple, 25% Excelente).

2. **`rank(pct=True, method="first")` en vez de `quantile()` simple para los cuartiles.**
   Por qué: hay muchísimos empates en el promedio de estrellas (dataset discreto, pocos valores posibles). Usar `quantile()` directo metía ~26 sucursales en "Revisión" en vez de las ~17-18 esperadas, porque todos los empates en el valor límite caían del mismo lado. `rank(method="first")` reparte los empates de forma determinística y balanceada entre grupos.

3. **"Métrica débil" comparada contra el promedio de la cadena, no contra un umbral fijo (ej. 90%).**
   Por qué: se descubrió que `% Rentabilidad` y `% Cantidad` (inventario) se comportan casi como banderas binarias (0 o 100, según si se ganó el bono ese mes), con una media de cadena muy baja (~16% para Rentabilidad), mientras que `% Ventas` es un porcentaje continuo con media ~76%. Un umbral fijo de 90% habría marcado a *todas* las sucursales como fallando en Rentabilidad siempre (sesgo de escala, no señal real). Comparar cada sucursal contra el promedio real de su propia métrica en toda la cadena da una señal correcta de "por debajo de lo normal para esa métrica específica".

4. **Tendencia trimestral (Ene-Mar vs Abr-Jun), no mes-a-mes.**
   Por qué: comparar mes contra mes anterior es ruidoso con datos tan variables; comparar la mitad del periodo contra la otra mitad da una señal de tendencia más estable con umbral de ±0.5 estrellas para considerar cambio real vs ruido.

5. **Streamlit + Community Cloud (gratis) sobre otras opciones de hosting.**
   Por qué: el usuario ya tenía cuenta en Streamlit, no se requiere backend separado ni base de datos — todo el estado se deriva de los Excel en `data/raw/` en cada carga. Sencillo de mantener para un usuario no-técnico.

6. **Repo público en GitHub (decisión explícita del usuario, con datos reales de ventas incluidos).**
   Por qué: se le preguntó explícitamente dos veces (repo público vs privado, incluir Excel con datos reales o no) y confirmó ambas veces que quería todo público. **Nota de seguridad:** esto significa que los datos de ventas/metas reales de la empresa son visibles públicamente en GitHub — decisión informada del usuario, no un descuido.

7. **`UNIDADES` como dict extensible en vez de hardcodear "Calzapato" en todo el código.**
   Por qué: cuando apareció la necesidad de agregar Kelder como segunda unidad de negocio, se refactorizó `data_loader.py`, `reporte_ejecutivo.py` y `reporte_excel.py` para aceptar `data_dir`/`unidad` como parámetros en vez de rutas fijas, permitiendo agregar más unidades de negocio a futuro solo añadiendo una entrada al dict.

8. **Matplotlib solo para el reporte ejecutivo estático, plotly para el dashboard interactivo.**
   Por qué: la imagen ejecutiva se pensó explícitamente para adjuntarse en correo (algo que se pueda "recortar y pegar"), lo cual requiere un PNG estático con layout controlado a nivel de píxel — plotly/HTML no sirve para eso. El dashboard en cambio se beneficia de interactividad (zoom, hover), de ahí plotly.

## 5. PROBLEMAS RESUELTOS

1. **Bug de clasificación: 26 sucursales en "Revisión" en vez de ~17.** Causa: `quantile()` con empates masivos. Solución: cambiar a `rank(pct=True, method="first")`. Ver decisión #2 arriba.

2. **Bug de "métrica débil" siempre devolvía "Rentabilidad" para el 100% de sucursales en Revisión.** Causa: se comparaba el mínimo entre 3 columnas de escalas incompatibles (Ventas ~76% de media vs Rentabilidad ~16% de media), así que Rentabilidad "ganaba" por diseño, no por ser realmente el problema. Solución: comparar cada métrica contra su propio promedio de cadena. Ver decisión #3.

3. **Emoji 🔴 no se renderizaba en matplotlib** (glyph faltante en fuente DejaVu Sans, aparecía como cuadro vacío). Solución: usar color de texto real (rojo) en vez de emoji para títulos en las imágenes generadas con matplotlib. Los emojis sí funcionan bien en Streamlit/HTML (dashboard), el problema era específico de matplotlib con fuente por defecto.

4. **Tarjetas KPI se encaballaban en el reporte ejecutivo de Kelder** porque los nombres de sucursal son más largos ("Kelder Centro Caborca" vs "Navolato Catedral") y con 5 tarjetas en vez de 4 el ancho se redujo. Solución: función `nombre_corto()` que quita el prefijo redundante ("Kelder "/"Calzapato ") y lógica de `textwrap` que ajusta tamaño de fuente y hace wrap a 2 líneas según longitud del texto.

5. **Nombres de archivo inconsistentes en la carpeta de Kelder** (`Junio.xlsx` vs `enero.xlsx`, mezclando mayúsculas). Solución: `_resolver_archivo()` hace glob + comparación case-insensitive en vez de construir la ruta directamente con `f"{mes}.xlsx"`.

6. **Ruta con capitalización incorrecta rompía el dashboard en producción pero no en local.** Causa: el código apuntaba a `data/raw/Kelder` pero la carpeta real (y committeada a git) era `data/raw/KELDER`. Windows es case-insensitive así que funcionaba en local; Streamlit Cloud corre en Linux (case-sensitive) así que habría fallado en producción. Se corrigió la ruta en el código **antes** de hacer push, evitando el problema.

7. **`ImportError: cannot import name 'UNIDADES'` en producción después del deploy**, a pesar de que el archivo en GitHub sí tenía `UNIDADES` correctamente (verificado con `git show origin/main:...`). Causa: caché de bytecode/contenedor obsoleto en el servidor de Streamlit Cloud tras el push — no un bug de código. Solución: el usuario le dio **"Reboot app"** desde el panel de administración de Streamlit Cloud, lo cual forzó una reconstrucción limpia y resolvió el error.

8. **`.claude/settings.json` casi se commiteó al repo público por accidente** (quedó incluido en un `git add -A`). Se detectó a tiempo, se hizo `git reset` sobre ese archivo específico y se agregó `.claude/` a `.gitignore` antes de commitear.

9. **Nombre de subdominio rechazado por Streamlit** dos veces al desplegar: primero por tener tilde (`análisis-...`), luego por un falso positivo del filtro de palabrotas en `analisis-indicadores-eficiencia`. Se resolvió usando un nombre alternativo: `metas-indicadores-eficiencia`.

## 6. PROBLEMAS PENDIENTES O CONOCIDOS

1. **`matplotlib` no está en `requirements.txt`.** No rompe el dashboard en producción porque `app.py` no lo importa (solo lo usan `reporte_ejecutivo.py`, que se corre localmente/manualmente, no desde la app web). Si en algún momento se quiere generar el reporte ejecutivo *desde* el dashboard desplegado, hay que agregar `matplotlib` a `requirements.txt`.

2. **`reports/Analisis_Metas_Kelder_Enero_Junio.xlsx` tiene cambios sin commitear** al cierre de esta sesión (ver `git status`). Revisar si se quiere volver a generar y subir, o descartar el cambio local.

3. **Sin tests automatizados.** Toda la validación de la lógica de clasificación/tendencia/métrica débil se hizo manualmente con prints ad-hoc durante la sesión, no hay `pytest` ni asserts guardados en el repo.

4. **Los archivos Excel de origen (`data/raw/`) están en el repo público de GitHub con datos reales de ventas de la empresa** — ver decisión #6. Riesgo de exposición de información comercial sensible, aceptado explícitamente por el usuario.

5. **No hay manejo de errores si falta un archivo de mes.** Si se agrega una unidad de negocio nueva o un mes sin el Excel correspondiente, `_resolver_archivo()` lanza `FileNotFoundError` sin mensaje amigable en la UI de Streamlit (se vería como un traceback crudo en el dashboard).

6. **La codificación de consola de Windows (cp1252) rompe los `print()` con emoji/acentos** al debuggear desde bash local (no afecta la app en sí, solo la experiencia de depuración manual — hay que envolver stdout en UTF-8 al hacer scripts de prueba ad-hoc).

## 7. PRÓXIMOS PASOS

En el orden en que se espera continuar (según lo conversado, no confirmado como plan formal):

1. **Recibir y cargar los datos de Julio** (Calzapato y/o Kelder) cuando el usuario los tenga completos, con el mismo formato de columnas que Ene-Jun (Ventas, Meta, %, UPT, Estrellas, Cantidad, Rentabilidad, Valor, Estrellas Alcanzadas). Extender `MESES` en `data_loader.py` a 7 meses y regenerar reportes.
2. **Confirmar envío del correo de Kelder** — el texto y adjuntos ya están listos, pendiente que el usuario lo mande manualmente desde su cliente de correo (no hay integración de Gmail activa en esta sesión de Claude Code).
3. Decidir qué hacer con el cambio sin commitear en `reports/Analisis_Metas_Kelder_Enero_Junio.xlsx`.
4. (Sugerido, no confirmado) Agregar `matplotlib` a `requirements.txt` si se quiere que la generación de reportes ejecutivos sea accesible desde la propia app web en vez de solo localmente.

## 8. CONVENCIONES DEL PROYECTO

- **Idioma:** todo el código de negocio (nombres de columnas, funciones, docstrings, texto en UI) está en **español**. Nombres de variables/funciones en `snake_case` en español (ej. `cargar_todos_los_meses`, `clasificar_sucursales`, `_metrica_debil_por_sucursal`).
- **Docstrings solo cuando explican el "por qué", no el "qué".** Se ve claramente en `data_loader.py`: funciones simples no tienen docstring, pero `clasificar_sucursales` y `_metrica_debil_por_sucursal` sí, porque documentan decisiones no obvias (por qué cuartiles y no umbral fijo, por qué comparar contra promedio de cadena).
- **Sin comentarios redundantes.** Se evita explicar qué hace una línea si el nombre ya lo dice; los comentarios que existen explican decisiones/trade-offs.
- **Funciones privadas con prefijo `_`** para helpers internos de un módulo (`_leer_mes`, `_resolver_archivo`, `_seccion_kpis`, etc.), funciones públicas sin prefijo son la API del módulo.
- **Cada script de generación de reportes (`reporte_ejecutivo.py`, `reporte_excel.py`) es ejecutable standalone** vía `python -m src.services.<módulo>`, con un bloque `if __name__ == "__main__":` que genera el reporte para **ambas** unidades de negocio en una sola corrida.
- **Paleta de color reservada por rol** (siguiendo la skill de dataviz del proyecto): los colores de categoría (Excelente=verde, Cumple=verde claro, Más o menos=amarillo, Revisión=rojo) son colores de "status" fijos, nunca se reutilizan como paleta categórica genérica ni se ciclan para otra cosa.
- **Parámetros con defaults sensatos apuntando a Calzapato** (`data_dir: str = "data/raw"`) para no romper las llamadas existentes al agregar soporte multi-unidad — Kelder siempre se pasa explícitamente.
- **Git:** commits en español, mensajes descriptivos del "por qué" cuando aplica (ver mensaje del commit `a281385`). Nunca se usa `--force`, `--amend` sobre commits ya pusheados, ni se salta hooks.
