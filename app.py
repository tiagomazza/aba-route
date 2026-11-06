import streamlit as st
import pandas as pd

st.title("ABA-Route")

# URL direto (Raw) fixo do ficheiro CSV no GitHub
GITHUB_URL = "https://raw.githubusercontent.com/tiagomazza/aba-route/main/clientes.csv"
ENCODING = "latin-1"

# Definição da função para carregar os dados com cache do Streamlit
@st.cache_data
def load_data(url, enc):
    # Tenta carregar com vírgula e, se houver apenas 1 coluna, tenta com ponto e vírgula
    df_temp = pd.read_csv(url, sep=",", encoding=enc)
    if len(df_temp.columns) == 1:
        df_temp = pd.read_csv(url, sep=";", encoding=enc)
    return df_temp

try:
    df = load_data(GITHUB_URL, ENCODING)
    st.success("Ficheiro clientes.csv carregado com sucesso!")

    st.markdown("---")

    st.subheader("Visualização dos Dados")
    st.dataframe(df)

except Exception as e:
    st.error(f"Erro ao carregar o ficheiro CSV do GitHub: {e}")
