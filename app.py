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

    # Limpar a coluna cliente e telefone para considerar somente números
    for col in df_temp.columns:
        col_lower = col.strip().lower()
        if any(alvo in col_lower for alvo in ['cliente', 'telefone', 'telemóvel', 'telemovel']):
            df_temp[col] = df_temp[col].apply(lambda x: "".join(re.findall(r'\d+', x)))

    # Filtrar inactivo = "não" e ocultar a coluna
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

    # Converter coluna de cliente para conter somente números também no SAGE se existir
    for col in df_temp.columns:
        if col.strip().lower() == 'cliente':
            df_temp[col] = df_temp[col].fillna("").astype(str).apply(lambda x: "".join(re.findall(r'\d+', x)))

    return df_temp

# Carregamento dos dados
try:
    df_clientes = load_clientes(URL_CLIENTES)
    df_sage = load_sage(URL_SAGE)

    # --- PAINEL LATERAL: FILTROS DO SAGE ---
    st.sidebar.header("🎚️ Filtros SAGE")

    # 1. Filtro de Documentos (Padrão: "FT")
    col_doc_sage = next((c for c in df_sage.columns if c.strip().lower() in ['doc', 'documento', 'doc.']), None)
    docs_selecionados = []
    if col_doc_sage:
        docs_unicos = sorted(df_sage[col_doc_sage].dropna().astype(str).unique())
        default_docs = [d for d in docs_unicos if 'ft' in d.lower()]
        if not default_docs:
            default_docs = docs_unicos
        docs_selecionados = st.sidebar.multiselect("📄 Documento (SAGE)", options=docs_unicos, default=default_docs)

    # 2. Filtro de Vendedor
    col_vend_sage = next((c for c in df_sage.columns if 'vendedor' in c.strip().lower()), None)
    vendedores_selecionados = []
    if col_vend_sage:
        vendedores_unicos = sorted(df_sage[col_vend_sage].dropna().astype(str).unique())
        vendedores_selecionados = st.sidebar.multiselect("🦸 Vendedor (SAGE)", options=vendedores_unicos, default=vendedores_unicos)

    # 3. Filtro de Descrição [Zonas geográficas]
    col_zona_sage = next((c for c in df_sage.columns if 'zona' in c.strip().lower() or 'descrição' in c.strip().lower()), None)
    zonas_selecionadas = []
    if col_zona_sage:
        zonas_unicas = sorted(df_sage[col_zona_sage].dropna().astype(str).unique())
        zonas_selecionadas = st.sidebar.multiselect("🌍 Descrição [Zonas geográficas]", options=zonas_unicas, default=zonas_unicas)

    # 4. Filtro de Datas (Padrão: últimos 3 meses)
    col_data_sage = next((c for c in df_sage.columns if 'data' in c.strip().lower()), None)
    if col_data_sage:
        df_sage[col_data_sage] = pd.to_datetime(df_sage[col_data_sage], errors='coerce')
        min_date = df_sage[col_data_sage].min()
        max_date = df_sage[col_data_sage].max()
        
        if pd.isna(min_date):
            min_date = datetime.now() - timedelta(days=90)
        if pd.isna(max_date):
            max_date = datetime.now()

        default_start = max_date - timedelta(days=90)
        default_end = max_date

        data_inicio, data_fim = st.sidebar.date_input(
            "📅 Intervalo de Datas (Últimos 3 Meses por defeito)",
            value=(default_start, default_end),
            min_value=min_date,
            max_value=max_date
        )

    # --- APLICAÇÃO DOS FILTROS AO SAGE ---
    df_sage_filt = df_sage.copy()
    if col_doc_sage and docs_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_doc_sage].astype(str).isin(docs_selecionados)]
    if col_vend_sage and vendedores_selecionados:
        df_sage_filt = df_sage_filt[df_sage_filt[col_vend_sage].astype(str).isin(vendedores_selecionados)]
    if col_zona_sage and zonas_selecionadas:
        df_sage_filt = df_sage_filt[df_sage_filt[col_zona_sage].astype(str).isin(zonas_selecionadas)]
    if col_data_sage and 'data_inicio' in locals() and 'data_fim' in locals():
        df_sage_filt = df_sage_filt[
            (df_sage_filt[col_data_sage] >= pd.to_datetime(data_inicio)) & 
            (df_sage_filt[col_data_sage] <= pd.to_datetime(data_fim))
        ]

    # Seleção exata das colunas exigidas para o SAGE (Data, Doc., Valor, Vendedor, Cliente)
    colunas_desejadas = []
    for col in df_sage_filt.columns:
        c_low = col.strip().lower()
        if any(k in c_low for k in ['data', 'doc.', 'documento', 'valor', 'vendedor', 'cliente']):
            colunas_desejadas.append(col)

    if colunas_desejadas:
        df_sage_exibicao = df_sage_filt[colunas_desejadas]
    else:
        df_sage_exibicao = df_sage_filt

    # --- NOVO DATAFRAME DE CLIENTES COM "Venda no Periodo" ---
    col_valor_sage = next((c for c in df_sage_filt.columns if 'valor' in c.strip().lower()), None)
    col_cliente_sage = next((c for c in df_sage_filt.columns if c.strip().lower() == 'cliente'), None)
    col_cliente_clientes = next((c for c in df_clientes.columns if 'cliente' in c.strip().lower()), None)

    df_clientes_vendas = df_clientes.copy()
    if col_valor_sage and col_cliente_sage and col_cliente_clientes:
        # Limpar e converter a coluna de valor para número de forma segura
        df_sage_filt[col_valor_sage] = (
            df_sage_filt[col_valor_sage]
            .astype(str)
            .str.replace(',', '.', regex=False)
            .apply(lambda x: "".join(re.findall(r'[\d\.\-]', x)))
        )
        df_sage_filt[col_valor_sage] = pd.to_numeric(df_sage_filt[col_valor_sage], errors='coerce').fillna(0)
        
        # Agrega a soma do Valor [Documentos GC Lin] por Cliente no SAGE
        df_agregado = df_sage_filt.groupby(col_cliente_sage, as_index=False)[col_valor_sage].sum()
        df_agregado.rename(columns={col_valor_sage: 'Venda no Periodo'}, inplace=True)
        
        # Faz o merge com o DataFrame de Clientes usando as colunas correspondentes
        df_clientes_vendas[col_cliente_clientes] = df_clientes_vendas[col_cliente_clientes].astype(str).str.strip()
        df_agregado[col_cliente_sage] = df_agregado[col_cliente_sage].astype(str).str.strip()
        
        df_clientes_vendas = pd.merge(
            df_clientes_vendas, 
            df_agregado, 
            left_on=col_cliente_clientes, 
            right_on=col_cliente_sage, 
            how='left'
        )
        # Se a coluna duplicada do cliente do sage veio no merge, remove-la
        if col_cliente_sage in df_clientes_vendas.columns and col_cliente_sage != col_cliente_clientes:
            df_clientes_vendas = df_clientes_vendas.drop(columns=[col_cliente_sage])
            
        # Preenche com 0 os clientes que não tiveram vendas no período filtrado
        df_clientes_vendas['Venda no Periodo'] = df_clientes_vendas['Venda no Periodo'].fillna(0)

    # --- EXIBIÇÃO NA INTERFACE ---
    st.subheader("📁 Ficheiro: Clientes com Venda no Período (Ativos / Inativo Oculto)")
    st.success(f"Clientes processados e cruzados com sucesso! ({len(df_clientes_vendas)} registos)")
    st.dataframe(df_clientes_vendas, use_container_width=True)

    st.markdown("---")

    st.subheader("📁 Ficheiro: SAGE (Filtrado)")
    st.success(f"SAGE.csv carregado com sucesso! ({len(df_sage_exibicao)} linhas exibidas)")
    st.dataframe(df_sage_exibicao, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar ou processar os ficheiros CSV do GitHub: {e}")
