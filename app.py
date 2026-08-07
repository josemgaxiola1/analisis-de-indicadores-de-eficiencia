import streamlit as st
import plotly.express as px

from src.services.data_loader import cargar_todos_los_meses, clasificar_sucursales, MESES, UNIDADES

COLOR_CATEGORIA = {
    "Excelente": "#1a9850",
    "Cumple": "#91cf60",
    "Más o menos": "#fee08b",
    "Revisión": "#d73027",
}

st.set_page_config(
    page_title="Proyecto Metas",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Proyecto Metas — Estrellas Enero a Junio")

unidad = st.selectbox("Unidad de Negocio", list(UNIDADES.keys()))
df = cargar_todos_los_meses(UNIDADES[unidad])

sucursales = sorted(df["Sucursal"].unique())
col1, col2 = st.columns(2)
meses_sel = col1.multiselect("Mes", MESES, default=MESES)
sucursales_sel = col2.multiselect("Sucursal", sucursales, default=sucursales)

df_f = df[df["Mes"].isin(meses_sel) & df["Sucursal"].isin(sucursales_sel)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Promedio estrellas", f"{df_f['Estrellas Alcanzadas'].mean():.1f}")
c2.metric("% cumplimiento ventas", f"{df_f['% Ventas'].mean():.1f}%")
c3.metric("% cumplimiento inventario", f"{df_f['% Cantidad'].mean():.1f}%")
c4.metric("Sucursales", df_f["Sucursal"].nunique())

st.subheader("Evolución de estrellas por sucursal")
evolucion = df_f.groupby(["Mes Orden", "Mes"])["Estrellas Alcanzadas"].mean().reset_index().sort_values("Mes Orden")
fig = px.line(evolucion, x="Mes", y="Estrellas Alcanzadas", markers=True)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Clasificación de sucursales (promedio Ene-Jun)")
clasif = clasificar_sucursales(df_f)

conteo_cols = st.columns(4)
for col, cat in zip(conteo_cols, ["Revisión", "Más o menos", "Cumple", "Excelente"]):
    n = (clasif["Categoría"] == cat).sum()
    col.metric(cat, n)

fig_clasif = px.bar(
    clasif,
    x="Sucursal",
    y="Promedio_Estrellas",
    color="Categoría",
    color_discrete_map=COLOR_CATEGORIA,
    category_orders={"Categoría": ["Revisión", "Más o menos", "Cumple", "Excelente"]},
)
fig_clasif.update_layout(xaxis_tickangle=-90, height=500)
st.plotly_chart(fig_clasif, use_container_width=True)

st.subheader("🔴 Seguimiento específico — sucursales en Revisión")
revision = clasif[clasif["Categoría"] == "Revisión"].reset_index(drop=True)
st.caption(f"{len(revision)} sucursales por debajo del primer cuartil de estrellas promedio.")
st.dataframe(
    revision[[
        "Sucursal", "Promedio_Estrellas", "Tendencia", "Métrica Débil",
        "Promedio_Ventas", "Promedio_Cantidad", "Promedio_Rentabilidad",
    ]],
    use_container_width=True,
)
st.caption(
    f"Empeorando: {(revision['Tendencia'] == '📉 Empeorando').sum()} · "
    f"Estable: {(revision['Tendencia'] == '➡️ Estable').sum()} · "
    f"Mejorando: {(revision['Tendencia'] == '📈 Mejorando').sum()}"
)

st.markdown("**Evolución mensual de las sucursales en Revisión**")
tabla_revision = df_f[df_f["Sucursal"].isin(revision["Sucursal"])].pivot_table(
    index="Sucursal", columns="Mes", values="Estrellas Alcanzadas"
)
tabla_revision = tabla_revision[[m for m in MESES if m in tabla_revision.columns]]
st.dataframe(tabla_revision, use_container_width=True)

st.subheader("Estrellas por sucursal y mes")
tabla_estrellas = df_f.pivot_table(index="Sucursal", columns="Mes", values="Estrellas Alcanzadas")
tabla_estrellas = tabla_estrellas[[m for m in MESES if m in tabla_estrellas.columns]]
st.dataframe(tabla_estrellas, use_container_width=True)

st.subheader("Detalle completo")
st.dataframe(df_f, use_container_width=True)
