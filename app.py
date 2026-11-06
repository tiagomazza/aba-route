import streamlit as st
import pandas as pd

st.title("Análise de Ficheiro CSV do GitHub com Streamlit")

# URL direto (Raw) fixo do ficheiro CSV no GitHub
GITHUB_URL = "https://raw.githubusercontent.com/tiagomazza/aba-route/main/clientes.csv"
ENCODING = "latin-1"

@st.cache_data
def load_data(url, enc):
    # Tenta carregar com vírgula e, se falhar ou houver apenas 1 coluna, tenta com ponto e vírgula
    df_temp = pd.read_csv(url, sep=",", encoding=enc)
    if len(df_temp.columns) == 1:
        df_temp = pd.read_csv(url, sep=";", encoding=enc)
    return df_temp

try:
    df = load_data(GITHUB_URL, ENCODING)
    st.success("Ficheiro clientes.csv carregado com sucesso!")

    st.markdown("---")
    st.subheader("Funcionalidades")
    
    show_raw = st.checkbox("Mostrar dados brutos (tabela)", value=True)
    show_stats = st.checkbox("Mostrar estatísticas descritivas (describe)", value=True)
    add_filters = st.checkbox("Adicionar filtros interativos por colunas", value=False)
    add_charts = st.checkbox("Adicionar gráficos automáticos", value=False)

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
        selected_vals = st.multiselect(
            f"Selecione valores para {col_to_filter}:", 
            unique_vals, 
            default=list(unique_vals[:min(5, len(unique_vals))])
        )
        filtered_df = df[df[col_to_filter].isin(selected_vals)]
        st.dataframe(filtered_df)

    if add_charts and not df.empty:
        st.subheader("Gráficos Rápidos")
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) >= 2:
            x_axis = st.selectbox("Eixo X", numeric_cols)
            y_axis = st.selectbox("Eixo Y", numeric_cols, index=min(1, len(numeric_cols)-1))
            st.line_chart(df[[x_axis, y_axis]].set_index(x_axis))
        elif len(numeric_cols) == 1:
            st.line_chart(df[numeric_cols[0]])
        else:
            st.info("Não foram encontradas colunas numéricas para gerar gráficos automaticamente.")

except Exception as e:
    st.error(f"Erro ao carregar o ficheiro CSV do GitHub: {e}")
