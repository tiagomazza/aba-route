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

# Função robusta para carregar e tratar qualquer CSV ignorando linhas problemáticas
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

    # 1. Converte tudo para texto de forma segura
    for col in df_temp.columns:
        df_temp[col] = df_temp[col].fillna("").astype(str).str.replace('nan', '', case=False)

    # 2. Limpa colunas de cliente e telefone mantendo apenas números
    for col in df_temp.columns:
        col_lower = col.strip().lower()
        if any(alvo in col_lower for alvo in ['cliente', 'telefone', 'telemóvel', 'telemovel']):
            df_temp[col] = df_temp[col].apply(lambda x: "".join(re.findall(r'\d+', x)))

    # Tratamento da coluna 'inactivo' se existir
    col_inactivo = [c for c in df_temp.columns if c.strip().lower() in ['inactivo', 'inativo']]
    if col_inactivo:
        target_col = col_inactivo[0]
        df_temp[target_col] = df_temp[target_col].astype(str).str.strip()
        mapa_inactivo = {'0': 'não', '1': 'sim', '0.0': 'não', '1.0': 'sim'}
        df_temp[target_col] = df_temp[target_col].replace(mapa_inactivo)

    return df_temp

# Carregamento dos dados
try:
    df_clientes = load_and_clean_csv(URL_CLIENTES)
    df_sage = load_and_clean_csv(URL_SAGE)

    # --- PAINEL LATERAL: FILTROS DO SAGE ---
    st.sidebar.header("🎚️ Filtros SAGE")

    # Filtro para Documento (coluna Doc. ou equivalente)
    col_doc_sage = next((c for c in df_sage.columns if c.strip().lower() in ['doc', 'documento', 'doc.']), None)
    docs_selecionados = []
    if col_doc_sage:
        docs_unicos = sorted(df_sage[col_doc_sage].dropna().unique())
        docs_selecionados = st.sidebar.multiselect("📄 Documento (SAGE)", options=docs_unicos, default=docs_unicos)

    # Filtro para Vendedor (coluna Vendedor [Documentos GC Linha] ou equivalente)
    col_vend_sage = next((c for c in df_sage.columns if 'vendedor' in c.strip().lower()), None)
    vendedores_selecionados = []
    if col_vend_sage:
        vendedores_unicos = sorted(df_sage[col_vend_sage].dropna().unique())
        vendedores_selecionados = st.sidebar.multiselect("🦸 Vendedor (SAGE)", options=vendedores_unicos, default=vendedores_unicos)

    # Aplicação dos filtros ao DataFrame do SAGE
    df_sage_filt = df_sage.copy()
    if col_doc_sage and docs_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_doc_sage].isin(docs_selecionados)]
    if col_vend_sage and vendedores_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_vend_sage].isin(vendedores_selecionados)]

    # --- EXIBIÇÃO NA INTERFACE ---
    st.subheader("📁 Ficheiro: Clientes")
    st.success("clientes.csv carregado e processado com sucesso!")
    st.dataframe(df_clientes, use_container_width=True)

    st.markdown("---")

    st.subheader("📁 Ficheiro: SAGE (Filtrado)")
    st.success(f"SAGE.csv carregado com sucesso! ({len(df_sage_filt)} linhas exibidas)")
    st.dataframe(df_sage_filt, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar ou processar os ficheiros CSV do GitHub: {e}")
