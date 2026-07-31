import pandas as pd

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
MES_ORDEN = {m: i for i, m in enumerate(MESES, start=1)}

COLUMNAS = [
    "Unidad Negocio", "Sucursal", "Ventas", "Meta Ventas", "% Ventas",
    "UPT", "Meta UN Cumplimiento", "Estrellas Ventas",
    "Cantidad", "% Cantidad", "Rentabilidad", "% Rentabilidad",
    "Valor", "% Valor", "Estrellas Alcanzadas",
]


def _leer_mes(mes: str, data_dir: str = "data/raw") -> pd.DataFrame:
    df = pd.read_excel(f"{data_dir}/{mes}.xlsx", sheet_name="Sheet1", header=1)
    df = df.iloc[:, [1, 2, 3, 4, 5, 7, 8, 9, 11, 12, 14, 15, 17, 18, 20]]
    df.columns = COLUMNAS
    df = df.dropna(subset=["Sucursal"])
    df.insert(0, "Mes", mes)
    df.insert(1, "Mes Orden", MES_ORDEN[mes])
    return df


def cargar_todos_los_meses(data_dir: str = "data/raw") -> pd.DataFrame:
    frames = [_leer_mes(mes, data_dir) for mes in MESES]
    return pd.concat(frames, ignore_index=True).sort_values(["Mes Orden", "Sucursal"])


CATEGORIAS = ["Revisión", "Más o menos", "Cumple", "Excelente"]


def clasificar_sucursales(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio de estrellas por sucursal (6 meses) + clasificación por cuartiles.

    Los cuartiles se calculan sobre el propio conjunto de sucursales porque el
    máximo teórico (9 estrellas) casi nunca se alcanza en la práctica: usar un
    corte fijo dejaría casi todo en "Revisión". Así el grupo de menor
    desempeño queda naturalmente cerca de las ~15 sucursales a atender.
    """
    resumen = (
        df.groupby("Sucursal")
        .agg(
            Promedio_Estrellas=("Estrellas Alcanzadas", "mean"),
            Promedio_Ventas=("% Ventas", "mean"),
            Promedio_Cantidad=("% Cantidad", "mean"),
            Promedio_Rentabilidad=("% Rentabilidad", "mean"),
            Meses=("Mes", "count"),
        )
        .reset_index()
    )

    # rank(pct=True) reparte los empates (muy comunes en este dataset) de forma
    # consistente entre grupos, en vez de que todos caigan en el mismo cuartil.
    percentil = resumen["Promedio_Estrellas"].rank(pct=True, method="first")

    def categoria(p: float) -> str:
        if p <= 0.25:
            return "Revisión"
        if p <= 0.5:
            return "Más o menos"
        if p <= 0.75:
            return "Cumple"
        return "Excelente"

    resumen["Categoría"] = percentil.apply(categoria)
    return resumen.sort_values("Promedio_Estrellas")
