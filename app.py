import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta

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

# Função para carregar o ficheiro Clientes
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

    col_inactivo = next((c for c in df_temp.columns if c.strip().lower() in ['inactivo', 'inativo']), None)
    if col_inactivo:
        df_temp[col_inactivo] = df_temp[col_inactivo].astype(str).str.strip().str.lower()
        mapa_inactivo = {'0': 'não', '1': 'sim', '0.0': 'não', '1.0': 'sim', 'nao': 'não'}
        df_temp[col_inactivo] = df_temp[col_inactivo].replace(mapa_inactivo)
        df_temp = df_temp[df_temp[col_inactivo] == 'não'].copy()
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

    for col in df_temp.columns:
        if col.strip().lower() == 'cliente':
            df_temp[col] = df_temp[col].fillna("").astype(str).apply(lambda x: "".join(re.findall(r'\d+', x)))

    return df_temp

try:
    df_clientes = load_clientes(URL_CLIENTES)
    df_sage = load_sage(URL_SAGE)

    col_zona_cli = next((c for c in df_clientes.columns if 'descrição' in c.strip().lower() and 'zona' in c.strip().lower()), None)
    if not col_zona_cli:
        col_zona_cli = next((c for c in df_clientes.columns if 'zona' in c.strip().lower() or 'descrição' in c.strip().lower()), None)

    col_doc_sage = next((c for c in df_sage.columns if c.strip().lower() in ['doc', 'documento', 'doc.']), None)
    col_vend_sage = next((c for c in df_sage.columns if 'vendedor' in c.strip().lower()), None)
    col_zona_sage = next((c for c in df_sage.columns if 'descrição' in c.strip().lower() and 'zona' in c.strip().lower()), None)
    if not col_zona_sage:
        col_zona_sage = next((c for c in df_sage.columns if 'zona' in c.strip().lower() or 'descrição' in c.strip().lower()), None)
    col_data_sage = next((c for c in df_sage.columns if 'data' in c.strip().lower()), None)

    df_sage_filt = df_sage.copy()
    if col_data_sage:
        df_sage_filt[col_data_sage] = pd.to_datetime(df_sage_filt[col_data_sage], errors='coerce')
        min_date = df_sage_filt[col_data_sage].min()
        max_date = df_sage_filt[col_data_sage].max()
        if pd.isna(min_date):
            min_date = datetime.now() - timedelta(days=90)
        if pd.isna(max_date):
            max_date = datetime.now()
    else:
        min_date = datetime.now() - timedelta(days=90)
        max_date = datetime.now()

    # --- PAINEL LATERAL ---
    st.sidebar.header("🎚️ Filtros")
    
    vendedores_selecionados = []
    if col_vend_sage:
        vendedores_unicos = sorted(df_sage_filt[col_vend_sage].dropna().astype(str).unique())
        vendedores_selecionados = st.sidebar.multiselect("🦸 Vendedor", options=vendedores_unicos, default=vendedores_unicos)

    zonas_cli_selecionadas = []
    if col_zona_cli:
        zonas_cli_unicas = sorted(df_clientes[col_zona_cli].dropna().astype(str).unique())
        zonas_cli_selecionadas = st.sidebar.multiselect("🌍 Zonas Geográficas", options=zonas_cli_unicas, default=zonas_cli_unicas)

    st.sidebar.header("📊 Quantidade de Clientes")
    qtd_com_mov = st.sidebar.number_input("Com Movimentação", min_value=0, value=3, step=1)
    qtd_sem_mov = st.sidebar.number_input("Sem Movimentação", min_value=0, value=3, step=1)
    
    st.sidebar.markdown("---")

    default_start = max_date - timedelta(days=90)
    default_end = max_date
    data_inicio, data_fim = st.sidebar.date_input(
        "📅 Intervalo de Datas",
        value=(default_start, default_end),
        min_value=min_date,
        max_value=max_date
    )

    docs_selecionados = []
    if col_doc_sage:
        docs_unicos = sorted(df_sage_filt[col_doc_sage].dropna().astype(str).unique())
        default_docs = [d for d in docs_unicos if 'ft' in d.lower()]
        if not default_docs:
            default_docs = docs_unicos
        docs_selecionados = st.sidebar.multiselect("📄 Documento (SAGE)", options=docs_unicos, default=default_docs)

    # --- APLICAÇÃO DOS FILTROS NO SAGE ---
    if col_doc_sage and docs_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_doc_sage].astype(str).isin(docs_selecionados)]
    if col_vend_sage and vendedores_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_vend_sage].astype(str).isin(vendedores_selecionados)]
    if col_zona_sage and zonas_sage_selecionadas:
        df_sage_filt = df_sage_filt[df_sage_filt[col_zona_sage].astype(str).isin(zonas_sage_selecionadas)]
    if col_data_sage and data_inicio and data_fim:
        df_sage_filt = df_sage_filt[
            (df_sage_filt[col_data_sage] >= pd.to_datetime(data_inicio)) & 
            (df_sage_filt[col_data_sage] <= pd.to_datetime(data_fim))
        ]

    # --- APLICAÇÃO DOS FILTROS EM CLIENTES ---
    df_clientes_filt = df_clientes.copy()
    if col_zona_cli and zonas_cli_selecionadas:
        df_clientes_filt = df_clientes_filt[df_clientes_filt[col_zona_cli].astype(str).isin(zonas_cli_selecionadas)]

    # --- CRUZAÇÃO E DATAFRAME FINAL ---
    col_valor_sage = next((c for c in df_sage_filt.columns if 'valor' in c.strip().lower()), None)
    col_cliente_sage = next((c for c in df_sage_filt.columns if c.strip().lower() == 'cliente'), None)
    col_cliente_clientes = next((c for c in df_clientes_filt.columns if 'cliente' in c.strip().lower()), None)

    df_clientes_vendas = df_clientes_filt.copy()
    if col_valor_sage and col_cliente_sage and col_cliente_clientes:
        df_sage_filt[col_valor_sage] = (
            df_sage_filt[col_valor_sage]
            .astype(str)
            .str.replace(',', '.', regex=False)
            .apply(lambda x: "".join(re.findall(r'[\d\.\-]', x)))
        )
        df_sage_filt[col_valor_sage] = pd.to_numeric(df_sage_filt[col_valor_sage], errors='coerce').fillna(0)
        
        df_agregado = df_sage_filt.groupby(col_cliente_sage, as_index=False)[col_valor_sage].sum()
        df_agregado.rename(columns={col_valor_sage: 'Venda no Periodo'}, inplace=True)
        
        df_clientes_vendas[col_cliente_clientes] = df_clientes_vendas[col_cliente_clientes].astype(str).str.strip()
        df_agregado[col_cliente_sage] = df_agregado[col_cliente_sage].astype(str).str.strip()
        
        df_clientes_vendas = pd.merge(
            df_clientes_vendas, 
            df_agregado, 
            left_on=col_cliente_clientes, 
            right_on=col_cliente_sage, 
            how='left'
        )
        if col_cliente_sage in df_clientes_vendas.columns and col_cliente_sage != col_cliente_clientes:
            df_clientes_vendas = df_clientes_vendas.drop(columns=[col_cliente_sage])
            
        df_clientes_vendas['Venda no Periodo'] = df_clientes_vendas['Venda no Periodo'].fillna(0)

        df_com_mov = df_clientes_vendas[df_clientes_vendas['Venda no Periodo'] > 0].head(qtd_com_mov)
        df_sem_mov = df_clientes_vendas[df_clientes_vendas['Venda no Periodo'] == 0].head(qtd_sem_mov)
        
        df_clientes_vendas_final = pd.concat([df_com_mov, df_sem_mov]).reset_index(drop=True)
    else:
        df_clientes_vendas_final = df_clientes_vendas

    # --- EXIBIÇÃO ---
    st.subheader("📁 Clientes")
    st.success(f"Dados processados e filtrados com sucesso! ({len(df_clientes_vendas_final)} registos exibidos)")
    st.dataframe(df_clientes_vendas_final, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar ou processar os ficheiros CSV do GitHub: {e}")
