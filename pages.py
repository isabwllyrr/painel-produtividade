import streamlit as st
import pandas as pd

st.title("📈 Análises Estratégicas de Produtividade")

uploaded_file = st.file_uploader("📁 Faça upload da planilha de produtividade", type=["xlsx"], key="estrategicas")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    df["EFICIENCIA"] = df["QUANT_UND"] / df["QT_APANHA"].replace(0, 1)

    tipos = df["TIPO"].unique()
    metricas = ["QT_APANHA", "QUANT_UND", "VOLUME", "PESOBRUTO", "EFICIENCIA"]
    metrica = st.selectbox("📊 Selecione uma métrica para comparação", metricas)

    st.markdown("### 🔍 Comparativo de Setores (por TIPO)")
    comparativo_setor = df.groupby("TIPO")[metrica].mean().sort_values(ascending=False)
    st.bar_chart(comparativo_setor)

    st.markdown("### ⏱️ Produtividade por Turno (Hora)")
    produtividade_turno = df.groupby("HORA")[metrica].mean().sort_index()
    st.line_chart(produtividade_turno)

    with st.expander("📄 Ver dados agrupados"):
        st.dataframe(df[["TIPO", "HORA", metrica]])

else:
    st.info("📥 Faça upload da planilha para iniciar a análise estratégica.")
