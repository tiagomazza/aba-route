import streamlit as st
import pandas as pd

st.title("ABA-Route")

# URL direto (Raw) fixo do ficheiro CSV no GitHub
GITHUB_URL = "https://raw.githubusercontent.com/tiagomazza/aba-route/main/clientes.csv"
ENCODING = "latin-1"

try:
    df = load_data(GITHUB_URL, ENCODING)
    st.success("Ficheiro clientes.csv carregado com sucesso!")

    st.markdown("---")

    show_raw:
        st.subheader("Visualização dos Dados")
        st.dataframe(df)

except Exception as e:
    st.error(f"Erro ao carregar o ficheiro CSV do GitHub: {e}")
