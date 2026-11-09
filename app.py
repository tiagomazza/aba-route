import streamlit as st
import pandas as pd
import re

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

# Função robusta para carregar e tratar qualquer CSV ignorando linhas problemáticas e aplicando limpeza estricta
@st.cache_data
def load_and_clean_csv(url):
    df_temp = None
    
    # Tenta ler com diferentes separadores usando o engine python e ignorando linhas corrompidas
    for sep in [",", ";"]:
        try:
            df_temp = pd.read_csv(
                url, 
                sep=sep, 
                encoding=ENCODING, 
                header=1, 
                engine="python", 
                on_bad_lines="skip"
            )
            if len(df_temp.columns) > 1:
                break
        except Exception:
            continue

    if df_temp is None or df_temp.empty:
        df_temp = pd.read_csv(
            url, 
            sep=",", 
            encoding=ENCODING, 
            engine="python", 
            on_bad_lines="skip"
        )

    # Limpeza geral para as restantes colunas
    for col in df_temp.columns:
        if df_temp[col].dtype == 'object':
            df_temp[col] = (
                df_temp[col]
                .astype(str)
                .str.replace(r'[\"\=]', '', regex=True)
                .str.strip()
            )

    # Tratamento estricto: Mantém apenas os números nas colunas especificadas
    colunas_apenas_numeros = ['cliente', 'telefone', 'telemóvel', 'telemovel']
    for col in df_temp.columns:
        col_lower = col.strip().lower()
        if any(alvo in col_lower for alvo in colunas_apenas_numeros):
            df_temp[col] = (
                df_temp[col]
                .astype(str)
                .apply(lambda x: "".join(re.findall(r'\d+', x)))  # Extrai unicamente os dígitos numéricos
            )

    # Tratamento opcional da coluna 'inactivo' se existir
    col_inactivo = [c for c in df_temp.columns if c.strip().lower() in ['inactivo', 'inativo']]
    if col_inactivo:
        target_col = col_inactivo[0]
        df_temp[target_col] = df_temp[target_col].astype(str).str.strip()
        mapa_inactivo = {'0': 'não', '1': 'sim', '0.0': 'não', '1.0': 'sim'}
        df_temp[target_col] = df_temp[target_col].replace(mapa_inactivo)

    return df_temp

# Carregamento e exibição dos dados na aplicação
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
