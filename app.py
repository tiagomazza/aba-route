import streamlit as st
import pandas as pd

st.title("Análise de Ficheiro CSV do GitHub com Streamlit")

st.markdown("""
### Configuração Inicial
Para criarmos o script completo e adaptado às suas necessidades exatas, por favor forneça as informações abaixo:
""")

# Recolha de informações interativas
github_url = st.text_input(
    "1. URL do ficheiro CSV no GitHub (Link Direto / Raw):",
    placeholder="https://raw.githubusercontent.com/utilizador/repositorio/main/dados.csv"
)

sep_options = {", (Vírgula)": ",", "; (Ponto e vírgula)": ";", "\t (Tabulação)": "	"}
sep_choice = st.selectbox("2. Qual o separador do CSV?", list(sep_options.keys()))
separator = sep_options[sep_choice]

encoding_choice = st.selectbox("3. Qual a codificação (encoding) do ficheiro?", ["utf-8", "latin1", "iso-8859-1"])

st.markdown("---")
st.subheader("4. O que pretende fazer com os dados? (Funcionalidades desejadas)")
show_raw = st.checkbox("Mostrar os dados brutos (tabela)", value=True)
show_stats = st.checkbox("Mostrar estatísticas descritivas (describe)", value=True)
add_filters = st.checkbox("Adicionar filtros interativos por colunas", value=False)
add_charts = st.checkbox("Adicionar gráficos automáticos", value=False)

if github_url:
    try:
        @st.cache_data
        def load_data(url, sep, enc):
            return pd.read_csv(url, sep=sep, encoding=enc)

        df = load_data(github_url, separator, encoding_choice)
        
        st.success("Ficheiro carregado com sucesso!")
        
        if show_raw:
            st.subheader("Visualização dos Dados")
            st.dataframe(df)
            
        if show_stats:
            st.subheader("Estatísticas Descritivas")
            st.write(df.describe())
            
        if add_filters and not df.empty:
            st.subheader("Filtros Interativos")
            col_to_filter = st.selectbox("Escolha uma coluna para filtrar:", df.columns)
            unique_vals = df[col_to_filter].unique()
            selected_vals = st.multiselect(f"Selecione valores para {col_to_filter}:", unique_vals, default=list(unique_vals[:min(5, len(unique_vals))]))
            filtered_df = df[df[col_to_filter].isin(selected_vals)]
            st.dataframe(filtered_df)
            
        if add_charts and not df.empty:
            st.subheader("Gráficos Rápidos")
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) >= 2:
                x_axis = st.selectbox("Eixo X", numeric_cols)
                y_axis = st.selectbox("Eixo Y", numeric_cols, index=min(1, len(numeric_cols)-1))
                st.line_chart(df[[x_axis, y_axis]].set_index(x_axis))
            else:
                st.info("São necessárias pelo menos duas colunas numéricas para gerar gráficos.")

    except Exception as e:
        st.error(f"Erro ao carregar o ficheiro CSV. Verifique o URL ou o separador. Detalhes: {e}")
else:
    st.info("Insira o URL raw do seu CSV no GitHub para começar.")
