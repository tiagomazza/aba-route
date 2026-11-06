import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="ABA-Route",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("ABA-Route")

# URLs diretos (Raw) dos ficheiros CSV no GitHub
URL_CLIENTES = "https://raw.githubusercontent.com/tiagomazza/aba-route/main/clientes.csv"
URL_SAGE = "https://raw.githubusercontent.com/tiagomazza/aba-sales/main/data/SAGE.csv"
ENCODING = "latin-1"

# Função genérica para carregar e tratar qualquer CSV com a limpeza cirúrgica
@st.cache_data
def load_and_clean_csv(url):
    try:
        df_temp = pd.read_csv(url, sep=",", encoding=ENCODING, header=1)
        if len(df_temp.columns) == 1:
            df_temp = pd.read_csv(url, sep=";", encoding=ENCODING, header=1)
    except Exception:
        df_temp = pd.read_csv(url, sep=";", encoding=ENCODING, header=1)

    # Limpeza cirúrgica de células para eliminar o formato '="valor"' ou quaisquer aspas e iguais residuais
    for col in df_temp.columns:
        if df_temp[col].dtype == 'object':
            def limpar_celula(val):
                if pd.isna(val):
                    return ""
                s = str(val).strip()
                if s.startswith('="') and s.endswith('"'):
                    return s[2:-1]  # Retira os 2 primeiros e o último caractere
                if s.startswith('='):
                    s = s[1:]
                return s.replace('"', '').replace('=', '').strip()

            df_temp[col] = df_temp[col].apply(limpar_celula)

    # Tratamento opcional da coluna 'inactivo' se existir
    col_inactivo = [c for c in df_temp.columns if c.strip().lower() in ['inactivo', 'inativo']]
    if col_inactivo:
        target_col = col_inactivo[0]
        df_temp[target_col] = df_temp[target_col].astype(str).str.strip()
        mapa_inactivo = {'0': 'não', '1': 'sim', '0.0': 'não', '1.0': 'sim'}
        df_temp[target_col] = df_temp[target_col].replace(mapa_inactivo)

    return df_temp

# Carregamento dos dados
try:
    st.subheader("📁 Ficheiro: Clientes")
    df_clientes = load_and_clean_csv(URL_CLIENTES)
    st.success("clientes.csv carregado e processado com sucesso!")
    st.dataframe(df_clientes, use_container_width=True)

    st.markdown("---")

    st.subheader("📁 Ficheiro: SAGE")
    df_sage = load_and_clean_csv(URL_SAGE)
    st.success("SAGE.csv carregado e processado com sucesso!")
    st.dataframe(df_sage, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar os ficheiros CSV do GitHub: {e}")
