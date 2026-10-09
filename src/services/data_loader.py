import glob
import os

import pandas as pd

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre",
]
MES_ORDEN = {m: i for i, m in enumerate(MESES, start=1)}

UNIDADES = {
    "Calzapato": "data/raw",
    "Kelder": "data/raw/KELDER",
}

COLUMNAS = [
    "Unidad Negocio", "Sucursal", "Ventas", "Meta Ventas", "% Ventas",
    "UPT", "Meta UN Cumplimiento", "Estrellas Ventas",
    "Cantidad", "% Cantidad", "Rentabilidad", "% Rentabilidad",
    "Valor", "% Valor", "Estrellas Alcanzadas",
]


def _resolver_archivo(mes: str, data_dir: str) -> str:
    """Los archivos de cada mes no siempre tienen la misma capitalización
    (ej. 'Junio.xlsx' vs 'enero.xlsx'), así que se busca sin importar mayúsculas."""
    coincidencias = glob.glob(os.path.join(data_dir, "*.xlsx"))
    for ruta in coincidencias:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        if nombre.lower() == mes.lower():
            return ruta
    raise FileNotFoundError(f"No se encontró el archivo de {mes} en {data_dir}")


def _leer_mes(mes: str, data_dir: str) -> pd.DataFrame:
    ruta = _resolver_archivo(mes, data_dir)
    df = pd.read_excel(ruta, sheet_name="Sheet1", header=1)
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

    tendencia = _tendencia_por_sucursal(df)
    metrica_debil = _metrica_debil_por_sucursal(resumen)
    resumen = resumen.merge(tendencia, on="Sucursal").merge(metrica_debil, on="Sucursal")

    return resumen.sort_values("Promedio_Estrellas")


def _tendencia_por_sucursal(df: pd.DataFrame) -> pd.DataFrame:
    """Compara el promedio de estrellas del trimestre más reciente contra el
    trimestre inmediato anterior, para saber si la sucursal mejora, empeora o
    se mantiene. Con 6 meses cargados esto es Ene-Mar vs Abr-Jun; con más
    meses (ej. 9) siempre toma los últimos 3 vs los 3 antes de esos, para que
    la tendencia refleje el momentum reciente y no se desbalancee a medida
    que se acumulan más meses.
    """
    meses_presentes = sorted(df["Mes"].unique(), key=MES_ORDEN.get)
    trimestre_anterior = meses_presentes[-6:-3]
    trimestre_reciente = meses_presentes[-3:]

    prom_inicio = df[df["Mes"].isin(trimestre_anterior)].groupby("Sucursal")["Estrellas Alcanzadas"].mean()
    prom_fin = df[df["Mes"].isin(trimestre_reciente)].groupby("Sucursal")["Estrellas Alcanzadas"].mean()
    diferencia = (prom_fin - prom_inicio).rename("Diferencia Trimestral")

    todas_sucursales = df["Sucursal"].unique()
    prom_inicio = prom_inicio.reindex(todas_sucursales)
    prom_fin = prom_fin.reindex(todas_sucursales)
    diferencia = diferencia.reindex(todas_sucursales)

    def etiqueta(sucursal: str) -> str:
        # Sin datos en el trimestre reciente: dejó de reportar (posible cierre),
        # no es lo mismo que "Estable" — nunca se debe mezclar con ese caso.
        if pd.isna(prom_fin[sucursal]):
            return "⚠️ Sin datos recientes"
        if pd.isna(prom_inicio[sucursal]):
            return "🆕 Sucursal nueva"
        d = diferencia[sucursal]
        if d >= 0.5:
            return "📈 Mejorando"
        if d <= -0.5:
            return "📉 Empeorando"
        return "➡️ Estable"

    tendencia = pd.Series(todas_sucursales, index=todas_sucursales).apply(etiqueta).rename("Tendencia")
    return pd.concat([diferencia, tendencia], axis=1).reset_index(names="Sucursal")


def _metrica_debil_por_sucursal(resumen: pd.DataFrame) -> pd.DataFrame:
    """Señala qué indicador(es) están por debajo del promedio de la cadena.

    Nota: "% Rentabilidad" y "% Cantidad" se comportan casi como banderas
    binarias (0 o 100, según si se alcanzó el bono ese mes) mientras que
    "% Ventas" es un porcentaje continuo contra la meta — tienen escalas y
    "normales" muy distintas (ej. el promedio de Rentabilidad de toda la
    cadena es ~16%, no 90%). Por eso se compara cada sucursal contra el
    promedio de SU MISMA métrica en toda la cadena, no contra un umbral fijo
    como 90%, que sería irreal para Rentabilidad/Cantidad.
    """
    metricas = {
        "Promedio_Ventas": "Ventas",
        "Promedio_Cantidad": "Inventario",
        "Promedio_Rentabilidad": "Rentabilidad",
    }
    promedio_cadena = resumen[list(metricas.keys())].mean()

    def foco(row):
        debiles = [nombre for col, nombre in metricas.items() if row[col] < promedio_cadena[col]]
        return ", ".join(debiles) if debiles else "En línea con la cadena"

    resultado = resumen[["Sucursal"] + list(metricas.keys())].copy()
    resultado["Métrica Débil"] = resultado.apply(foco, axis=1)
    return resultado[["Sucursal", "Métrica Débil"]]
