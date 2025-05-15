import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Painel de Produtividade - BRF1", layout="wide")
st.title("📦 Painel de Produtividade - Logística de Medicamentos e Cosméticos")

uploaded_file = st.file_uploader("📁 Faça upload da planilha de produtividade", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df["EFICIENCIA"] = df["QUANT_UND"] / df["QT_APANHA"].replace(0, 1)

    filiais = sorted(df["CODFILIAL"].unique())
    metricas = ["QT_APANHA", "QUANT_OS", "OS_CX_FECHADA", "O_S_FLOW_RACK",
                "QUANT_UND", "VOLUME", "PESOBRUTO", "TOT_SKU", "EFICIENCIA"]
    horas = sorted(df["HORA"].unique())
    tipos = df["TIPO"].unique()

    st.sidebar.header("🎛️ Filtros")
    filial = st.sidebar.selectbox("Filial", filiais)
    metrica = st.sidebar.selectbox("Métrica de Produtividade", metricas)
    hora_selecionada = st.sidebar.multiselect("Hora (opcional)", horas, default=horas)
    tipo_selecionado = st.sidebar.multiselect("Tipo de Colaborador", tipos, default=tipos)
    top_n = st.sidebar.selectbox("Ranking", [3, 5, 10, 20, 50, "Todos"], index=2)

    df_filtrado = df[(df["CODFILIAL"] == filial) &
                     (df["HORA"].isin(hora_selecionada)) &
                     (df["TIPO"].isin(tipo_selecionado))]

    if filial in [1, 3]:
        agrupador = "TIPO"
        st.warning("⚠️ Esta filial usa coletores compartilhados. A análise será por setor (TIPO), não por funcionário.")
    else:
        agrupador = "FUNCIONARIO"

    abas = ["📊 Resumo Geral", "⏰ Gráficos por Hora", "📐 Regra de Pareto",
            "💰 Bonificação Top 3", "📆 Eficiência por Turno",
            "📊 Projeção para Outras Filiais", "📄 Dados Filtrados"]

    if filial == 2:
        abas.append("🏆 Benchmark de Funcionários")

    aba = st.radio("🧭 Escolha a seção que deseja visualizar:", abas)

    if aba == "📊 Resumo Geral":
        st.header("📊 Resumo Geral")
        st.markdown("---")
        st.subheader(f"📈 Métrica Selecionada: {metrica} | Filial: {filial}")

        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Média", f"{df_filtrado[metrica].mean():.2f}")
        col2.metric("🔺 Máximo", f"{df_filtrado[metrica].max()}")
        col3.metric("🔻 Mínimo", f"{df_filtrado[metrica].min()}")

        st.markdown("### 👷 Produtividade por Funcionário ou Setor")
        grafico_agrupado = df_filtrado.groupby(agrupador)[metrica].sum().sort_values(ascending=False)
        if top_n != "Todos":
            grafico_agrupado = grafico_agrupado.head(top_n)
        st.bar_chart(grafico_agrupado)

    elif aba == "⏰ Gráficos por Hora":
        st.header("⏰ Produtividade por Hora")
        st.markdown("---")
        grafico_hora = df_filtrado.groupby("HORA")[metrica].sum().sort_index()
        st.line_chart(grafico_hora)

    elif aba == "📐 Regra de Pareto":
        st.header("📐 Análise 80/20 (Regra de Pareto)")
        st.markdown("---")
        grafico_agrupado = df_filtrado.groupby(agrupador)[metrica].sum().sort_values(ascending=False)
        total_prod = grafico_agrupado.sum()
        grafico_pct = grafico_agrupado.cumsum() / total_prod
        nps = grafico_pct[grafico_pct <= 0.8]
        perc_nps = (len(nps) / len(grafico_agrupado)) * 100

        st.markdown(f"- {len(nps)} {agrupador.lower()}(s) ({perc_nps:.1f}%) foram responsáveis por 80% da produtividade.")
        if perc_nps <= 20:
            st.success("✅ A regra de Pareto se aplica!")
        else:
            st.warning("⚠️ A regra de Pareto não se aplica.")

        st.line_chart(grafico_pct)

    elif aba == "💰 Bonificação Top 3":
        st.header("💰 Bonificação para Top 3 Funcionários")
        st.markdown("---")
        grafico_agrupado = df_filtrado.groupby(agrupador)[metrica].sum().sort_values(ascending=False)
        top3 = grafico_agrupado.head(3)

        bonus_1 = 1500 * 0.15
        bonus_2 = 1500 * 0.10
        bonus_3 = 1500 * 0.07

        st.write(f"🥇 {top3.index[0]} → R$ {bonus_1:.2f}")
        st.write(f"🥈 {top3.index[1]} → R$ {bonus_2:.2f}")
        st.write(f"🥉 {top3.index[2]} → R$ {bonus_3:.2f}")
        st.success(f"💸 Total de Bonificação: R$ {bonus_1 + bonus_2 + bonus_3:.2f}")

    elif aba == "📆 Eficiência por Turno":
        st.header("📆 Eficiência por Turno (Hora do Dia)")
        st.markdown("---")
        df_filtrado["EFICIENCIA"] = df_filtrado["QUANT_UND"] / df_filtrado["QT_APANHA"].replace(0, 1)

        ef_por_hora = df_filtrado.groupby("HORA")["EFICIENCIA"].mean().reset_index()
        pico_hora = ef_por_hora.loc[ef_por_hora['EFICIENCIA'].idxmax()]
        try:
            ef_antes_almoco = ef_por_hora[ef_por_hora["HORA"] == 12]["EFICIENCIA"].values[0]
            ef_depois_almoco = ef_por_hora[ef_por_hora["HORA"] == 13]["EFICIENCIA"].values[0]
            percent_queda = ((ef_antes_almoco - ef_depois_almoco) / ef_antes_almoco) * 100
        except:
            percent_queda = 0
        media_13_15 = ef_por_hora[(ef_por_hora["HORA"] >= 13) & (ef_por_hora["HORA"] <= 15)]["EFICIENCIA"].mean()

        st.line_chart(data=ef_por_hora.set_index("HORA"))
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"📈 Pico: {int(pico_hora['HORA'])}h → {pico_hora['EFICIENCIA']:.2f} und/apanha")
        col2.markdown(f"📉 Pós-almoço: Queda {percent_queda:.1f}%")
        col3.markdown(f"🕑 13h–15h: Média {media_13_15:.2f}")

    elif aba == "📊 Projeção para Outras Filiais":
        st.header("📊 Projeção de Produtividade para Filiais 1 e 3")
        st.markdown("---")
        ef_ref = df[df["CODFILIAL"] == 2]["QUANT_UND"].sum() / df[df["CODFILIAL"] == 2]["QT_APANHA"].replace(0, 1).sum()
        st.markdown(f"🔎 Eficiência média da Filial 2 como referência: {ef_ref:.2f} und/apanha")
        df_proj = df[df["CODFILIAL"].isin([1, 3])].copy()
        df_proj["ESTIMADA"] = df_proj["QT_APANHA"] * ef_ref
        real_proj = df_proj.groupby("CODFILIAL")[["QUANT_UND", "ESTIMADA"]].sum().rename(columns={"QUANT_UND": "REAL", "ESTIMADA": "ESTIMADA"})
        st.bar_chart(real_proj)
        st.markdown("### 🧠 Por que calcular isso?")
        st.markdown("""
        - Esta projeção mostra o potencial de crescimento das filiais 1 e 3 com base na eficiência da filial 2.
        - Justifica investimentos em coletores, treinamento ou metas de bonificação.
        - Apoia decisões operacionais com dados reais.
        """)
        st.markdown(f"📍 Estimativa: Filial 1 → {int(real_proj.loc[1, 'ESTIMADA'])} unidades, Filial 3 → {int(real_proj.loc[3, 'ESTIMADA'])}.")

    elif aba == "📄 Dados Filtrados":
        st.header("📄 Dados Filtrados")
        with st.expander("Clique para visualizar a tabela"):
            st.dataframe(df_filtrado)

    elif aba == "🏆 Benchmark de Funcionários":
        st.header("🏆 Benchmark de Funcionários")
        st.markdown("---")
        funcionarios = sorted(df_filtrado["FUNCIONARIO"].unique())
        funcionarios_selecionados = st.multiselect("Escolha até 5 funcionários:", funcionarios, max_selections=5)

        if funcionarios_selecionados:
            df_benchmark = df_filtrado[df_filtrado["FUNCIONARIO"].isin(funcionarios_selecionados)]
            df_benchmark_grouped = df_benchmark.groupby("FUNCIONARIO")[metricas].sum()

            fig = go.Figure()
            for func in funcionarios_selecionados:
                fig.add_trace(go.Scatterpolar(
                    r=df_benchmark_grouped.loc[func],
                    theta=metricas,
                    fill='toself',
                    name=f"{func}"
                ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                showlegend=True,
                height=600,
                title="🔎 Comparativo no Radar Chart - Funcionários Selecionados"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📊 Comparação por Métrica")
            for metrica_comp in metricas:
                melhores = df_benchmark_grouped[metrica_comp].idxmax()
                cores = ["blue" if func == melhores else "lightgray" for func in df_benchmark_grouped.index]

                fig_bar = go.Figure(data=[go.Bar(
                    x=df_benchmark_grouped.index.astype(str),
                    y=df_benchmark_grouped[metrica_comp],
                    marker_color=cores,
                    text=df_benchmark_grouped[metrica_comp].round(2),
                    textposition='auto',
                    textfont=dict(size=16, color="red")
                )])
                fig_bar.update_layout(
                    title=f"Métrica: {metrica_comp}",
                    height=400,
                    xaxis_title="Funcionário",
                    yaxis_title=metrica_comp,
                    uniformtext_minsize=8,
                    uniformtext_mode='hide'
                )
                st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("📥 Envie um arquivo Excel com os dados de produtividade para iniciar.")