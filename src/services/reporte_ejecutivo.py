import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from src.services.data_loader import cargar_todos_los_meses, clasificar_sucursales, MESES

COLOR_SURFACE = "#fcfcfb"
COLOR_TEXT_PRIMARY = "#0b0b0b"
COLOR_TEXT_SECONDARY = "#52514e"
COLOR_MUTED = "#898781"
COLOR_GRID = "#e1e0d9"

# Paleta de estatus (fija, nunca usada para series categóricas)
COLOR_CATEGORIA = {
    "Excelente": "#0ca30c",
    "Cumple": "#8fbf3f",
    "Más o menos": "#fab219",
    "Revisión": "#d03b3b",
}
ORDEN_CATEGORIAS = ["Revisión", "Más o menos", "Cumple", "Excelente"]


def generar_reporte(
    data_dir: str = "data/raw",
    salida: str = "reports/reporte_ejecutivo.png",
    unidad: str = "Calzapato",
) -> str:
    df = cargar_todos_los_meses(data_dir)
    clasif = clasificar_sucursales(df)
    revision = clasif[clasif["Categoría"] == "Revisión"].sort_values("Promedio_Estrellas")

    fig = plt.figure(figsize=(14, 16.3), facecolor=COLOR_SURFACE)
    gs = fig.add_gridspec(
        4, 1, height_ratios=[1.3, 2.4, 3.7, 0.5], hspace=0.45, top=0.9, bottom=0.02, left=0.07, right=0.95
    )

    _seccion_titulo(fig, df, unidad)
    _seccion_kpis(fig.add_subplot(gs[0]), df, clasif)
    _seccion_evolucion(fig.add_subplot(gs[1]), df)
    _seccion_tabla_revision(fig.add_subplot(gs[2]), revision)
    _seccion_conclusion(fig.add_subplot(gs[3]), revision)

    fig.savefig(salida, dpi=170, facecolor=COLOR_SURFACE, bbox_inches="tight")
    plt.close(fig)
    return salida


def _seccion_titulo(fig, df, unidad):
    fig.text(
        0.07, 0.985,
        "Reporte Ejecutivo — Cumplimiento de Metas por Sucursal",
        fontsize=22, fontweight="bold", color=COLOR_TEXT_PRIMARY, ha="left", va="top",
    )
    fig.text(
        0.07, 0.965,
        f"Periodo: Enero – Junio 2026  ·  {df['Sucursal'].nunique()} sucursales  ·  Unidad de Negocio: {unidad}",
        fontsize=12, color=COLOR_TEXT_SECONDARY, ha="left", va="top",
    )


def _seccion_kpis(ax, df, clasif):
    ax.axis("off")
    promedio = df["Estrellas Alcanzadas"].mean()
    n_revision = (clasif["Categoría"] == "Revisión").sum()
    empeorando = (clasif.loc[clasif["Categoría"] == "Revisión", "Tendencia"] == "📉 Empeorando").sum()
    ordenado = clasif.sort_values("Promedio_Estrellas", ascending=False)
    mejor = ordenado.iloc[0]
    peor = ordenado.iloc[-1]

    def nombre_corto(sucursal: str) -> str:
        nombre = sucursal.split(" - ")[-1].title()
        for prefijo in ("Kelder ", "Calzapato "):
            if nombre.startswith(prefijo):
                nombre = nombre[len(prefijo):]
        return nombre

    tarjetas = [
        ("Promedio de estrellas\n(cadena, Ene-Jun)", f"{promedio:.1f} / 9", COLOR_TEXT_PRIMARY),
        ("Sucursales en\nRevisión", f"{n_revision}", COLOR_CATEGORIA["Revisión"]),
        ("En Revisión y\nempeorando", f"{empeorando}", COLOR_CATEGORIA["Revisión"]),
        ("Mejor sucursal", nombre_corto(mejor["Sucursal"]), COLOR_CATEGORIA["Excelente"]),
        ("Peor sucursal", nombre_corto(peor["Sucursal"]), COLOR_CATEGORIA["Revisión"]),
    ]

    import textwrap

    ancho = 1.0 / len(tarjetas)
    for i, (etiqueta, valor, color) in enumerate(tarjetas):
        x0 = i * ancho + 0.01
        box = FancyBboxPatch(
            (x0, 0.05), ancho - 0.02, 0.9,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1, edgecolor=COLOR_GRID, facecolor="white",
            transform=ax.transAxes, clip_on=False,
        )
        ax.add_patch(box)

        if len(valor) <= 6:
            tam_valor, texto_valor = 20, valor
        elif len(valor) <= 14:
            tam_valor, texto_valor = 15, valor
        else:
            tam_valor = 13
            texto_valor = "\n".join(textwrap.wrap(valor, width=14, max_lines=2))

        ax.text(x0 + (ancho - 0.02) / 2, 0.62, texto_valor, transform=ax.transAxes,
                ha="center", va="center", fontsize=tam_valor, fontweight="bold", color=color)
        ax.text(x0 + (ancho - 0.02) / 2, 0.2, etiqueta, transform=ax.transAxes,
                ha="center", va="center", fontsize=10, color=COLOR_TEXT_SECONDARY)


def _seccion_evolucion(ax, df):
    evolucion = (
        df.groupby(["Mes Orden", "Mes"])["Estrellas Alcanzadas"]
        .mean()
        .reset_index()
        .sort_values("Mes Orden")
    )
    ax.plot(evolucion["Mes"], evolucion["Estrellas Alcanzadas"], color="#2a78d6", linewidth=2.5,
            marker="o", markersize=8, markerfacecolor="white", markeredgewidth=2, markeredgecolor="#2a78d6")
    for _, row in evolucion.iterrows():
        ax.annotate(f"{row['Estrellas Alcanzadas']:.1f}", (row["Mes"], row["Estrellas Alcanzadas"]),
                    textcoords="offset points", xytext=(0, 12), ha="center", fontsize=10, color=COLOR_TEXT_PRIMARY)

    ax.set_title("Evolución del promedio de estrellas — toda la cadena", fontsize=14, fontweight="bold",
                 color=COLOR_TEXT_PRIMARY, loc="left", pad=14)
    ax.set_ylim(0, max(evolucion["Estrellas Alcanzadas"].max() + 1, 4))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_MUTED)
    ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=11)
    ax.yaxis.grid(True, color=COLOR_GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.set_ylabel("")


def _seccion_tabla_revision(ax, revision):
    ax.axis("off")
    ax.set_title(
        f"Sucursales en Revisión — seguimiento específico ({len(revision)})",
        fontsize=14, fontweight="bold", color=COLOR_CATEGORIA["Revisión"], loc="left", pad=14,
    )

    columnas = ["Sucursal", "Prom. Estrellas", "Tendencia", "Métrica débil"]
    filas = [
        [
            row["Sucursal"],
            f"{row['Promedio_Estrellas']:.1f}",
            row["Tendencia"].replace("📉 ", "").replace("📈 ", "").replace("➡️ ", ""),
            row["Métrica Débil"],
        ]
        for _, row in revision.iterrows()
    ]

    tabla = ax.table(cellText=filas, colLabels=columnas, cellLoc="left", loc="upper left",
                      colWidths=[0.42, 0.16, 0.18, 0.24], bbox=[0, 0, 1, 0.94])
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(10)
    tabla.scale(1, 1.55)

    tendencia_colores = {"Empeorando": "#fdecec", "Estable": "#fff6e0", "Mejorando": "#eaf7ea"}
    for (r, c), cell in tabla.get_celld().items():
        cell.set_edgecolor(COLOR_GRID)
        if r == 0:
            cell.set_facecolor("#f0efec")
            cell.set_text_props(fontweight="bold", color=COLOR_TEXT_PRIMARY)
        else:
            cell.set_facecolor("white")
            cell.set_text_props(color=COLOR_TEXT_PRIMARY)
            if c == 2:
                texto = filas[r - 1][2]
                cell.set_facecolor(tendencia_colores.get(texto, "white"))


def _seccion_conclusion(ax, revision):
    ax.axis("off")
    empeorando = (revision["Tendencia"] == "📉 Empeorando").sum()
    inventario = revision["Métrica Débil"].str.contains("Inventario").sum()

    box = FancyBboxPatch(
        (0, 0.05), 1, 0.85,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=1, edgecolor=COLOR_CATEGORIA["Revisión"], facecolor="#fdecec",
        transform=ax.transAxes, clip_on=False,
    )
    ax.add_patch(box)
    ax.text(
        0.02, 0.47,
        f"⚠ Solicitud de apoyo: {len(revision)} sucursales requieren seguimiento prioritario — "
        f"{empeorando} van empeorando y {inventario} fallan en Inventario, la causa más común. "
        "Se pide apoyo del área correspondiente para intervenir estos puntos.",
        transform=ax.transAxes, ha="left", va="center", fontsize=11.5,
        color=COLOR_TEXT_PRIMARY, wrap=True,
    )


if __name__ == "__main__":
    ruta = generar_reporte()
    print(f"Reporte generado en: {ruta}")
    ruta_kelder = generar_reporte(
        data_dir="data/raw/KELDER",
        salida="reports/reporte_ejecutivo_kelder.png",
        unidad="Kelder",
    )
    print(f"Reporte generado en: {ruta_kelder}")
