import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from src.services.data_loader import cargar_todos_los_meses, clasificar_sucursales, UNIDADES

COLOR_SURFACE = "#fcfcfb"
COLOR_TEXT_PRIMARY = "#0b0b0b"
COLOR_TEXT_SECONDARY = "#52514e"
COLOR_MUTED = "#898781"
COLOR_GRID = "#e1e0d9"

COLOR_CATEGORIA = {
    "Excelente": "#0ca30c",
    "Cumple": "#8fbf3f",
    "Más o menos": "#fab219",
    "Revisión": "#d03b3b",
}

# Series por marca: slots categóricos fijos (azul / naranja), nunca reutilizados.
# Nombre comercial a mostrar (la clave interna "Calzapato" viene de UNIDADES en
# data_loader.py; el nombre público de la marca lleva doble "z").
NOMBRE_MOSTRAR = {
    "Calzapato": "Calzzapato",
    "Kelder": "Kelder",
}

COLOR_MARCA = {
    "Calzzapato": "#2a78d6",
    "Kelder": "#eb6834",
}


def generar_reporte_consolidado(salida: str = "reports/reporte_consolidado.png") -> str:
    datos = {}
    for marca, ruta in UNIDADES.items():
        df = cargar_todos_los_meses(ruta)
        clasif = clasificar_sucursales(df)
        datos[NOMBRE_MOSTRAR[marca]] = {"df": df, "clasif": clasif}

    fig = plt.figure(figsize=(15, 19), facecolor=COLOR_SURFACE)
    gs = fig.add_gridspec(
        5, 1, height_ratios=[1.3, 1.4, 2.5, 4.0, 0.6],
        hspace=0.4, top=0.92, bottom=0.02, left=0.06, right=0.96,
    )

    _seccion_titulo(fig, datos)
    _seccion_kpis_globales(fig.add_subplot(gs[0]), datos)
    _seccion_kpis_por_marca(fig.add_subplot(gs[1]), datos)
    _seccion_evolucion_comparada(fig.add_subplot(gs[2]), datos)
    revision_combinada = _seccion_tabla_prioridad(fig.add_subplot(gs[3]), datos)
    _seccion_conclusion(fig.add_subplot(gs[4]), revision_combinada)

    fig.savefig(salida, dpi=170, facecolor=COLOR_SURFACE, bbox_inches="tight")
    plt.close(fig)
    return salida


def _seccion_titulo(fig, datos):
    total_sucursales = sum(d["df"]["Sucursal"].nunique() for d in datos.values())
    meses_presentes = next(iter(datos.values()))["df"].sort_values("Mes Orden")["Mes"].unique()
    periodo = f"{meses_presentes[0]} – {meses_presentes[-1]} 2026"

    fig.text(
        0.06, 0.985,
        "Reporte Ejecutivo Consolidado — Cumplimiento de Metas",
        fontsize=24, fontweight="bold", color=COLOR_TEXT_PRIMARY, ha="left", va="top",
    )
    fig.text(
        0.06, 0.965,
        f"Periodo: {periodo}  ·  {total_sucursales} sucursales  ·  Calzzapato + Kelder",
        fontsize=13, color=COLOR_TEXT_SECONDARY, ha="left", va="top",
    )


def _seccion_kpis_globales(ax, datos):
    ax.axis("off")
    total_sucursales = sum(d["df"]["Sucursal"].nunique() for d in datos.values())
    promedio_global = sum(d["df"]["Estrellas Alcanzadas"].sum() for d in datos.values()) / sum(
        len(d["df"]) for d in datos.values()
    )
    total_revision = sum((d["clasif"]["Categoría"] == "Revisión").sum() for d in datos.values())
    total_empeorando = sum(
        ((d["clasif"]["Categoría"] == "Revisión") & (d["clasif"]["Tendencia"] == "📉 Empeorando")).sum()
        for d in datos.values()
    )
    total_sin_datos = sum(
        ((d["clasif"]["Categoría"] == "Revisión") & (d["clasif"]["Tendencia"] == "⚠️ Sin datos recientes")).sum()
        for d in datos.values()
    )

    tarjetas = [
        ("Sucursales\nanalizadas", f"{total_sucursales}", COLOR_TEXT_PRIMARY),
        ("Promedio de estrellas\n(cadena, periodo)", f"{promedio_global:.1f} / 9", COLOR_TEXT_PRIMARY),
        ("Total en\nRevisión", f"{total_revision}", COLOR_CATEGORIA["Revisión"]),
        ("Empeorando\nactivamente", f"{total_empeorando}", COLOR_CATEGORIA["Revisión"]),
        ("Sin datos\nrecientes", f"{total_sin_datos}", COLOR_TEXT_SECONDARY),
    ]

    ancho = 1.0 / len(tarjetas)
    for i, (etiqueta, valor, color) in enumerate(tarjetas):
        x0 = i * ancho + 0.01
        box = FancyBboxPatch(
            (x0, 0.05), ancho - 0.02, 0.9,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1.2, edgecolor=COLOR_GRID, facecolor="white",
            transform=ax.transAxes, clip_on=False,
        )
        ax.add_patch(box)
        ax.text(x0 + (ancho - 0.02) / 2, 0.62, valor, transform=ax.transAxes,
                ha="center", va="center", fontsize=22, fontweight="bold", color=color)
        ax.text(x0 + (ancho - 0.02) / 2, 0.2, etiqueta, transform=ax.transAxes,
                ha="center", va="center", fontsize=10.5, color=COLOR_TEXT_SECONDARY)


def _seccion_kpis_por_marca(ax, datos):
    ax.axis("off")
    ancho = 1.0 / len(datos)
    for i, (marca, d) in enumerate(datos.items()):
        df, clasif = d["df"], d["clasif"]
        n_sucursales = df["Sucursal"].nunique()
        n_revision = (clasif["Categoría"] == "Revisión").sum()
        promedio = df["Estrellas Alcanzadas"].mean()

        x0 = i * ancho + 0.01
        box = FancyBboxPatch(
            (x0, 0.08), ancho - 0.02, 0.84,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1.5, edgecolor=COLOR_MARCA[marca], facecolor="white",
            transform=ax.transAxes, clip_on=False,
        )
        ax.add_patch(box)
        ax.text(x0 + 0.015, 0.72, marca, transform=ax.transAxes,
                ha="left", va="center", fontsize=15, fontweight="bold", color=COLOR_MARCA[marca])
        ax.text(
            x0 + 0.015, 0.32,
            f"{n_sucursales} sucursales   ·   {n_revision} en Revisión   ·   promedio {promedio:.1f}/9",
            transform=ax.transAxes, ha="left", va="center", fontsize=11.5, color=COLOR_TEXT_PRIMARY,
        )


def _seccion_evolucion_comparada(ax, datos):
    for marca, d in datos.items():
        evolucion = (
            d["df"].groupby(["Mes Orden", "Mes"])["Estrellas Alcanzadas"]
            .mean().reset_index().sort_values("Mes Orden")
        )
        ax.plot(
            evolucion["Mes"], evolucion["Estrellas Alcanzadas"],
            color=COLOR_MARCA[marca], linewidth=2.5, marker="o", markersize=7,
            markerfacecolor="white", markeredgewidth=2, markeredgecolor=COLOR_MARCA[marca],
            label=marca,
        )

    ax.set_title("Evolución del promedio de estrellas por marca", fontsize=15, fontweight="bold",
                 color=COLOR_TEXT_PRIMARY, loc="left", pad=14)
    ax.set_ylim(0, 4.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_MUTED)
    ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=11)
    ax.yaxis.grid(True, color=COLOR_GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, fontsize=11)


def _seccion_tabla_prioridad(ax, datos):
    ax.axis("off")

    frames = []
    for marca, d in datos.items():
        rev = d["clasif"][d["clasif"]["Categoría"] == "Revisión"].copy()
        rev.insert(0, "Marca", marca)
        frames.append(rev)
    import pandas as pd
    combinado = pd.concat(frames, ignore_index=True).sort_values("Promedio_Estrellas")

    ax.set_title(
        f"Sucursales prioritarias — seguimiento específico ({len(combinado)})",
        fontsize=15, fontweight="bold", color=COLOR_CATEGORIA["Revisión"], loc="left", pad=14,
    )

    columnas = ["Marca", "Sucursal", "Prom.", "Tendencia", "Métrica débil"]
    filas = [
        [
            row["Marca"],
            row["Sucursal"],
            f"{row['Promedio_Estrellas']:.1f}",
            row["Tendencia"].replace("📉 ", "").replace("📈 ", "").replace("➡️ ", "")
            .replace("⚠️ ", "").replace("🆕 ", ""),
            row["Métrica Débil"],
        ]
        for _, row in combinado.iterrows()
    ]

    tabla = ax.table(cellText=filas, colLabels=columnas, cellLoc="left", loc="upper left",
                      colWidths=[0.12, 0.33, 0.1, 0.18, 0.27], bbox=[0, 0, 1, 0.95])
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(9.5)
    tabla.scale(1, 1.4)

    tendencia_colores = {
        "Empeorando": "#fdecec", "Estable": "#fff6e0", "Mejorando": "#eaf7ea",
        "Sin datos recientes": "#ececec", "Sucursal nueva": "#e8f0fd",
    }
    for (r, c), cell in tabla.get_celld().items():
        cell.set_edgecolor(COLOR_GRID)
        if r == 0:
            cell.set_facecolor("#f0efec")
            cell.set_text_props(fontweight="bold", color=COLOR_TEXT_PRIMARY)
        else:
            cell.set_facecolor("white")
            cell.set_text_props(color=COLOR_TEXT_PRIMARY)
            if c == 0:
                cell.set_text_props(color=COLOR_MARCA.get(filas[r - 1][0], COLOR_TEXT_PRIMARY), fontweight="bold")
            if c == 3:
                texto = filas[r - 1][3]
                cell.set_facecolor(tendencia_colores.get(texto, "white"))

    return combinado


def _seccion_conclusion(ax, revision_combinada):
    ax.axis("off")
    empeorando = (revision_combinada["Tendencia"] == "📉 Empeorando").sum()
    sin_datos = (revision_combinada["Tendencia"] == "⚠️ Sin datos recientes").sum()
    inventario = revision_combinada["Métrica Débil"].str.contains("Inventario").sum()

    texto = (
        f"⚠ Solicitud de apoyo: {len(revision_combinada)} sucursales (ambas marcas) requieren seguimiento "
        f"prioritario — {empeorando} van empeorando y {inventario} fallan en Inventario, la causa más común. "
    )
    if sin_datos:
        texto += f"{sin_datos} dejaron de reportar en el trimestre más reciente y deben validarse. "
    texto += "Se pide apoyo del área correspondiente para intervenir estos puntos."

    box = FancyBboxPatch(
        (0, 0.05), 1, 0.85,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=1, edgecolor=COLOR_CATEGORIA["Revisión"], facecolor="#fdecec",
        transform=ax.transAxes, clip_on=False,
    )
    ax.add_patch(box)
    ax.text(
        0.015, 0.47, texto,
        transform=ax.transAxes, ha="left", va="center", fontsize=11,
        color=COLOR_TEXT_PRIMARY, wrap=True,
    )


if __name__ == "__main__":
    ruta = generar_reporte_consolidado()
    print(f"Reporte consolidado generado en: {ruta}")
