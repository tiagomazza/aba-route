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

# Função robusta para carregar o ficheiro Clientes
@st.cache_data
def load_clientes(url):
    df_temp = None
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

    for col in df_temp.columns:
        df_temp[col] = df_temp[col].fillna("").astype(str).str.replace('nan', '', case=False)

    for col in df_temp.columns:
        col_lower = col.strip().lower()
        if any(alvo in col_lower for alvo in ['cliente', 'telefone', 'telemóvel', 'telemovel']):
            df_temp[col] = df_temp[col].apply(lambda x: "".join(re.findall(r'\d+', x)))

    # Identificar a coluna inactivo/inativo para filtragem e remoção posterior
    col_inactivo = next((c for c in df_temp.columns if c.strip().lower() in ['inactivo', 'inativo']), None)
    if col_inactivo:
        df_temp[col_inactivo] = df_temp[col_inactivo].astype(str).str.strip().str.lower()
        mapa_inactivo = {'0': 'não', '1': 'sim', '0.0': 'não', '1.0': 'sim', 'nao': 'não'}
        df_temp[col_inactivo] = df_temp[col_inactivo].replace(mapa_inactivo)
        # Filtra somente onde o inactivo é "não"
        df_temp = df_temp[df_temp[col_inactivo] == 'não'].copy()
        # Remove a coluna inactivo para não ser exibida
        df_temp = df_temp.drop(columns=[col_inactivo])

    return df_temp

# Função para carregar o ficheiro SAGE
@st.cache_data
def load_sage(url):
    df_temp = None
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

    return df_temp

# Carregamento dos dados
try:
    df_clientes = load_clientes(URL_CLIENTES)
    df_sage = load_sage(URL_SAGE)

    # --- PAINEL LATERAL: FILTROS DO SAGE ---
    st.sidebar.header("🎚️ Filtros SAGE")

    # Mapeamento dinâmico das colunas exigidas baseadas na imagem
    col_doc_sage = next((c for c in df_sage.columns if c.strip().lower() in ['doc', 'documento', 'doc.']), None)
    col_vend_sage = next((c for c in df_sage.columns if 'vendedor' in c.strip().lower()), None)

    docs_selecionados = []
    if col_doc_sage:
        docs_unicos = sorted(df_sage[col_doc_sage].dropna().astype(str).unique())
        docs_selecionados = st.sidebar.multiselect("📄 Documento (SAGE)", options=docs_unicos, default=docs_unicos)

    vendedores_selecionados = []
    if col_vend_sage:
        vendedores_unicos = sorted(df_sage[col_vend_sage].dropna().astype(str).unique())
        vendedores_selecionados = st.sidebar.multiselect("🦸 Vendedor (SAGE)", options=vendedores_unicos, default=vendedores_unicos)

    # Aplicação dos filtros ao SAGE
    df_sage_filt = df_sage.copy()
    if col_doc_sage and docs_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_doc_sage].astype(str).isin(docs_selecionados)]
    if col_vend_sage and vendedores_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_vend_sage].astype(str).isin(vendedores_selecionados)]

    # Seleção estricta apenas das colunas exibidas na imagem anexada para o SAGE
    colunas_desejadas_sage = [
        c for c in df_sage_filt.columns 
        if any(termo in c.strip().lower() for termo in ['data', 'doc', 'valor', 'vendedor', 'cliente'])
    ]
    if colunas_desejadas_sage:
        df_sage_filt = df_sage_filt[colunas_desejadas_sage]

    # --- EXIBIÇÃO NA INTERFACE ---
    st.subheader("📁 Ficheiro: Clientes (Inativo = Não | Coluna Oculta)")
    st.success(f"clientes.csv processado com sucesso! ({len(df_clientes)} registos)")
    st.dataframe(df_clientes, use_container_width=True)

    st.markdown("---")

    st.subheader("📁 Ficheiro: SAGE (Colunas Filtradas conforme Imagem)")
    st.success(f"SAGE.csv carregado com sucesso! ({len(df_sage_filt)} linhas exibidas)")
    st.dataframe(df_sage_filt, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar ou processar os ficheiros CSV do GitHub: {e}")
