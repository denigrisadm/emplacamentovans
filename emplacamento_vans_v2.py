import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from collections import Counter
import os, re, unicodedata, json, hashlib
from io import BytesIO
import datetime
import base64

# ════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA (Ajustado estritamente para Vans)
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Comercial De Nigris - Vans",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# PWA — Ícone para iPhone/Android (adicionar à tela inicial)
_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAIAAADdvvtQAAABC...[MANTIDO ORIGINAL]"

def inject_pwa():
    manifest = {
        "name": "Emplacamento Vans",
        "short_name": "Emp. Vans",
        "description": "Inteligência Comercial De Nigris - Vans",
        "start_url": ".",
        "display": "standalone",
        "background_color": "#0a1628",
        "theme_color": "#0a1628",
        "icons": [
            {"src": f"data:image/png;base64,{_ICON_B64}", "sizes": "192x192", "type": "image/png"}
        ]
    }
    st.markdown(f'''
        <link rel="apple-touch-icon" href="data:image/png;base64,{_ICON_B64}">
        <link rel="icon" href="data:image/png;base64,{_ICON_B64}">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <style>
            [data-testid="stSidebarNav"]::before {{
                content: "";
                display: block;
                margin: 20px auto;
                width: 130px;
                height: 130px;
                background-image: url("data:image/png;base64,{_ICON_B64}");
                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
            }}
            /* Estilização CSS Original Mantida */
            .main .block-container {{ padding: 1.5rem 2rem; max-width: 95%; }}
            div[data-testid="stMetricValue"] > div {{ font-size: 24px !important; font-weight: bold; }}
            .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
            .stTabs [data-baseweb="tab"] {{
                padding: 8px 16px; background-color: #122239; border-radius: 4px 4px 0 0;
                color: #a3b8cc; font-weight: 500; transition: all 0.2s;
            }}
            .stTabs [data-baseweb="tab"]:hover {{ color: #ffffff; background-color: #1c3557; }}
            .stTabs [data-baseweb="tab"][aria-selected="true"] {{
                background-color: #0056b3; color: white; font-weight: bold;
            }}
            .upload-box {{
                border: 2px dashed #1e3a61; padding: 20px; border-radius: 8px;
                background-color: #0d1f38; text-align: center; margin-bottom: 15px;
            }}
            .upload-title {{ font-size: 16px; font-weight: bold; color: #4dabf7; margin-bottom: 10px; }}
        </style>
    ''', unsafe_allow_html=True)

inject_pwa()

# ════════════════════════════════════════════════════════════════
# FUNÇÕES DE TRATAMENTO DE TEXTO & PADRONIZAÇÃO (COMPLETAS)
# ════════════════════════════════════════════════════════════════
def normalizar_nome(txt):
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    txt = "".join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')
    txt = re.sub(r'[^A-Z0-9\s]', ' ', txt)
    return " ".join(txt.split())

def mapear_marca(txt):
    n = normalizar_nome(txt)
    if not n: return "OUTROS"
    if any(k in n for k in ["MERCEDES", "MB", "M.BENZ", "MERCEDES BENZ", "MERCEDES-BENZ"]): return "MERCEDES-BENZ"
    if "VOLKS" in n or "VW" in n or "MAN" in n: return "VOLKSWAGEN"
    if "SCANIA" in n: return "SCANIA"
    if "VOLVO" in n: return "VOLVO"
    if "IVECO" in n: return "IVECO"
    if "FIAT" in n: return "FIAT"
    if "FORD" in n: return "FORD"
    if "PEUGEOT" in n: return "PEUGEOT"
    if "CITROEN" in n: return "CITROEN"
    if "RENAULT" in n: return "RENAULT"
    if "FOTON" in n: return "FOTON"
    if "JAC" in n: return "JAC"
    return "OUTROS"

def limpar_cnpj(val):
    if pd.isna(val): return ""
    s = re.sub(r'\D', '', str(val))
    return s.zfill(14) if len(s) > 0 else ""

def extrair_raiz_cnpj(val):
    c = limpar_cnpj(val)
    return c[:8] if len(c) >= 8 else ""

# ════════════════════════════════════════════════════════════════
# CARREGAMENTO DOS ARQUIVOS (ETL COMPLETO ORIGINAL)
# ════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_carteira(file_bytes):
    df = pd.read_excel(file_bytes, dtype=str)
    cols = {c: c.strip().upper() for c in df.columns}
    df = df.rename(columns=cols)
    
    # Detecção dinâmica de colunas críticas da Carteira
    c_cnpj = next((c for c in df.columns if "CNPJ" in c or "CPF" in c), None)
    c_cli = next((c for c in df.columns if "CLIENTE" in c or "RAZAO" in c or "NOME" in c), None)
    c_vend = next((c for c in df.columns if "VENDEDOR" in c or "RESPONSAVEL" in c), None)
    c_Codvend = next((c for c in df.columns if "COD" in c and "VEND" in c), None)
    
    res = pd.DataFrame()
    if c_cnpj:
        res['CARTEIRA_CNPJ'] = df[c_cnpj].apply(limpar_cnpj)
        res['CARTEIRA_RAIZ'] = df[c_cnpj].apply(extrair_raiz_cnpj)
    else:
        res['CARTEIRA_CNPJ'] = ""
        res['CARTEIRA_RAIZ'] = ""
        
    res['CARTEIRA_CLIENTE'] = df[c_cli].fillna("").astype(str).str.upper().str.strip() if c_cli else "DESCONHECIDO"
    res['CARTEIRA_VENDEDOR'] = df[c_vend].fillna("").astype(str).str.upper().str.strip() if c_vend else "SEM VENDEDOR"
    
    if c_Codvend:
        res['CARTEIRA_COD_VENDEDOR'] = df[c_Codvend].fillna("").astype(str).str.strip()
    else:
        res['CARTEIRA_COD_VENDEDOR'] = ""
        
    res = res[res['CARTEIRA_RAIZ'] != ""].drop_duplicates(subset=['CARTEIRA_RAIZ'])
    return res

@st.cache_data(show_spinner=False)
def load_emplacamentos(file_bytes, label=""):
    df = pd.read_excel(file_bytes)
    df.columns = [c.strip().upper() for c in df.columns]
    
    # Mapeamento estrito baseado no leiaute padrão do arquivo de emplacamentos
    map_cols = {
        'DATA': ['DATA', 'DATA EMPLACAMENTO', 'DATA_EMPLACAMENTO', 'MES'],
        'CNPJ': ['CNPJ', 'CPF/CNPJ', 'CNPJ_COMPRADOR', 'CNPJ COMPRADOR', 'CGC'],
        'COMPRADOR': ['COMPRADOR', 'CLIENTE', 'NOME_COMPRADOR', 'RAZAO SOCIAL', 'NOME'],
        'MARCA': ['MARCA', 'FABRICANTE', 'MONTADORA'],
        'MODELO': ['MODELO', 'VEICULO', 'DESC_MODELO'],
        'CHASSI': ['CHASSI', 'NUMERO_CHASSI', 'VIN'],
        'MUNICIPIO': ['MUNICIPIO', 'CIDADE', 'CIDADE_EMPLACAMENTO'],
        'UF': ['UF', 'ESTADO']
    }
    
    final_df = pd.DataFrame()
    
    for k, candidates in map_cols.items():
        found = next((c for c in candidates if c in df.columns), None)
        if found:
            final_df[k] = df[found]
        else:
            final_df[k] = "" if k != 'DATA' else datetime.date.today()

    # Tratamento de datas flexível
    if 'DATA' in final_df.columns:
        final_df['DATA_TRATADA'] = pd.to_datetime(final_df['DATA'], errors='coerce')
        # Se falhar, tenta interpretar números sequenciais do Excel
        idx_nat = final_df['DATA_TRATADA'].isna()
        if idx_nat.any():
            for i in final_df[idx_nat].index:
                try:
                    num = float(final_df.loc[i, 'DATA'])
                    final_df.loc[i, 'DATA_TRATADA'] = pd.to_datetime(num, unit='D', origin='1899-12-30')
                except:
                    pass
    else:
        final_df['DATA_TRATADA'] = pd.Timestamp.now()
        
    final_df['DATA_TRATADA'] = final_df['DATA_TRATADA'].fillna(pd.Timestamp.now())
    final_df['ANO_MES'] = final_df['DATA_TRATADA'].dt.to_period('M')
    
    final_df['CNPJ_LIMPO'] = final_df['CNPJ'].apply(limpar_cnpj)
    final_df['RAIZ_CNPJ'] = final_df['CNPJ'].apply(extrair_raiz_cnpj)
    final_df['MARCA_MAP'] = final_df['MARCA'].apply(mapear_marca)
    final_df['COMPRADOR_NORM'] = final_df['COMPRADOR'].fillna("").astype(str).str.upper().str.strip()
    final_df['MODELO'] = final_df['MODELO'].fillna("").astype(str).str.upper().str.strip()
    final_df['UF'] = final_df['UF'].fillna("").astype(str).str.upper().str.strip()
    final_df['MUNICIPIO'] = final_df['MUNICIPIO'].fillna("").astype(str).str.upper().str.strip()
    final_df['CHASSI'] = final_df['CHASSI'].fillna("").astype(str).str.upper().str.strip()
    
    final_df['FONTE_ARQUIVO'] = label
    return final_df

# ════════════════════════════════════════════════════════════════
# GERENCIAMENTO DE ESTADO (SESSION STATE ORIGINAL)
# ════════════════════════════════════════════════════════════════
if 'df_cart' not in st.session_state: st.session_state.df_cart = pd.DataFrame()
if 'df_emp_list' not in st.session_state: st.session_state.df_emp_list = []
if 'emp_fontes' not in st.session_state: st.session_state.emp_fontes = []

# ════════════════════════════════════════════════════════════════
# ÁREA DE UPLOAD (MANTIDO COMPLETO)
# ════════════════════════════════════════════════════════════════
with st.expander("📂 Gerenciador de Bases de Dados (Carteira e Emplacamentos)", expanded=not len(st.session_state.df_emp_list)):
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown('<div class="upload-box"><div class="upload-title">📋 Carteira de Clientes</div>', unsafe_allow_html=True)
        up_c = st.file_uploader("CARTEIRA.xlsx", type=["xlsx"], key="up_cart")
        if up_c:
            st.session_state.df_cart = load_carteira(BytesIO(up_c.getvalue()))
            st.success("✅ Carteira processada com sucesso!")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_u2:
        st.markdown('<div class="upload-box"><div class="upload-title">🚚 Histórico de Emplacamentos</div>', unsafe_allow_html=True)
        up_e = st.file_uploader("EMPLACAMENTOS.xlsx (Múltiplos permitidos)", type=["xlsx"], key="up_emp", accept_multiple_files=True)
        if up_e:
            novos = 0
            for f in up_e:
                if f.name not in st.session_state.emp_fontes:
                    st.session_state.df_emp_list.append(load_emplacamentos(BytesIO(f.getvalue()), label=f.name))
                    st.session_state.emp_fontes.append(f.name)
                    novos += 1
            if novos: st.success(f"✅ {novos} nova(s) base(s) adicionada(s)!")
        
        if st.session_state.emp_fontes:
            st.markdown("**Arquivos Consolidados:** " + ", ".join([f"`{f}`" for f in st.session_state.emp_fontes]))
            if st.button("🗑️ Limpar Histórico de Emplacamentos", type="secondary"):
                st.session_state.df_emp_list = []
                st.session_state.emp_fontes = []
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Consolidação dos DataFrames de Emplacamento
if st.session_state.df_emp_list:
    df_base = pd.concat(st.session_state.df_emp_list, ignore_index=True)
else:
    df_base = pd.DataFrame()

# Bloqueio amigável caso não existam dados carregados
if df_base.empty:
    st.info("💡 Por favor, insira arquivos de Emplacamento acima para inicializar os Dashboards de Inteligência Comercial.")
    st.stop()

# Cruzamento de dados com a Carteira (Left Join via Raiz do CNPJ)
if not st.session_state.df_cart.empty:
    df_m = pd.merge(df_base, st.session_state.df_cart, left_on='RAIZ_CNPJ', right_on='CARTEIRA_RAIZ', how='left')
    df_m['CARTEIRA_VENDEDOR'] = df_m['CARTEIRA_VENDEDOR'].fillna("FORA DA CARTEIRA")
    df_m['STATUS_CARTEIRA'] = df_m['CARTEIRA_RAIZ'].apply(lambda x: "DENTRO" if pd.notna(x) else "FORA")
else:
    df_m = df_base.copy()
    df_m['CARTEIRA_VENDEDOR'] = "CARTEIRA NÃO ENVIADA"
    df_m['STATUS_CARTEIRA'] = "N/A"

# ════════════════════════════════════════════════════════════════
# FILTROS GLOBAIS DA SIDEBAR (ORIGINAL COMPLETO)
# ════════════════════════════════════════════════════════════════
st.sidebar.title("🎯 Filtros Estratégicos")

anos_disponiveis = sorted(df_m['DATA_TRATADA'].dt.year.unique(), reverse=True)
ano_sel = st.sidebar.selectbox("Ano de Análise", anos_disponiveis)

df_ano = df_m[df_m['DATA_TRATADA'].dt.year == ano_sel]

meses_disponiveis = sorted(df_ano['DATA_TRATADA'].dt.month.unique())
mes_nomes = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
opcoes_mes = [(m, mes_nomes[m]) for m in meses_disponiveis]

mes_sel = st.sidebar.select_slider(
    "Mês de Referência",
    options=[m[0] for m in opcoes_mes],
    format_func=lambda x: mes_nomes[x],
    value=max([m[0] for m in opcoes_mes])
)

# Definição estrita das janelas temporais de cálculo (Mês Atual, Mês Anterior e Acumulado YTD)
dt_ref_fim = datetime.date(ano_sel, mes_sel, 1) + relativedelta(months=1) - datetime.timedelta(days=1)
dt_ref_ini = datetime.date(ano_sel, mes_sel, 1)

dt_ant_ini = dt_ref_ini - relativedelta(months=1)
dt_ant_fim = dt_ref_ini - datetime.timedelta(days=1)

dt_ytd_ini = datetime.date(ano_sel, 1, 1)
dt_ytd_fim = dt_ref_fim

# Filtros Geográficos e Setoriais dinâmicos
ufs_disp = sorted(df_ano['UF'].unique())
uf_sel = st.sidebar.multiselect("Filtrar por UF", ufs_disp, default=ufs_disp)

df_filtrado_global = df_ano[df_ano['UF'].isin(uf_sel)]

muns_disp = sorted(df_filtrado_global['MUNICIPIO'].unique())
mun_sel = st.sidebar.multiselect("Filtrar por Município", muns_disp)

if mun_sel:
    df_filtrado_global = df_filtrado_global[df_filtrado_global['MUNICIPIO'].isin(mun_sel)]

vends_disp = sorted(df_filtrado_global['CARTEIRA_VENDEDOR'].unique())
vend_sel = st.sidebar.multiselect("Filtrar por Vendedor", vends_disp)

if vend_sel:
    df_filtrado_global = df_filtrado_global[df_filtrado_global['CARTEIRA_VENDEDOR'].isin(vend_sel)]

# Segmentações temporais aplicadas ao DataFrame filtrado
df_mes_atual = df_filtrado_global[(df_filtrado_global['DATA_TRATADA'].dt.date >= dt_ref_ini) & (df_filtrado_global['DATA_TRATADA'].dt.date <= dt_ref_fim)]
df_mes_ant = df_filtrado_global[(df_filtrado_global['DATA_TRATADA'].dt.date >= dt_ant_ini) & (df_filtrado_global['DATA_TRATADA'].dt.date <= dt_ant_fim)]
df_ytd = df_filtrado_global[(df_filtrado_global['DATA_TRATADA'].dt.date >= dt_ytd_ini) & (df_filtrado_global['DATA_TRATADA'].dt.date <= dt_ytd_fim)]

# ════════════════════════════════════════════════════════════════
# MÉTRICAS DE DESEMPENHO (KPIs ORIGINAIS)
# ════════════════════════════════════════════════════════════════
def calcular_metricas_card(df_segmento, marca_alvo="MERCEDES-BENZ"):
    total = len(df_segmento)
    mb = len(df_segmento[df_segmento['MARCA_MAP'] == marca_alvo])
    mkt_share = (mb / total * 100) if total > 0 else 0.0
    return total, mb, mkt_share

tot_atual, mb_atual, share_atual = calcular_metricas_card(df_mes_atual)
tot_ant, mb_ant, share_ant = calcular_metricas_card(df_mes_ant)
tot_ytd, mb_ytd, share_ytd = calcular_metricas_card(df_ytd)

# Renderização do Bloco de KPIs em Cards Visuais modernos
st.markdown("### 📊 Visão Geral do Mercado")
c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)

with c_kpi1:
    diff_v = mb_atual - mb_ant
    st.metric(
        label=f"Emplacamentos MB ({mes_nomes[mes_sel]})",
        value=f"{mb_atual} u.",
        delta=f"{diff_v} u. vs mês ant."
    )
with c_kpi2:
    diff_s = share_atual - share_ant
    st.metric(
        label=f"Market Share MB ({mes_nomes[mes_sel]})",
        value=f"{share_atual:.1f}%",
        delta=f"{diff_s:.1f}% vs mês ant."
    )
with c_kpi3:
    st.metric(
        label="Volume Acumulado MB (YTD)",
        value=f"{mb_ytd} u.",
        help="Volume total de emplacamentos Mercedes-Benz no ano corrente até o mês selecionado."
    )
with c_kpi4:
    st.metric(
        label="Market Share Médio (YTD)",
        value=f"{share_ytd:.1f}%"
    )

# ════════════════════════════════════════════════════════════════
# ESTRUTURA DE ABAS PRINCIPAIS DO SISTEMA
# ════════════════════════════════════════════════════════════════
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📈 Análise Macroscópica & Share", 
    "🏢 Visão de Concorrência", 
    "👤 Compradores & Carteira", 
    "🗺️ Distribuição Geográfica",
    "🔍 Detalhamento Analítico"
])

# ────────────────────────────────────────────────────────────────
# ABA 1: ANÁLISE MACROSCÓPICA & SHARE
# ────────────────────────────────────────────────────────────────
with aba1:
    st.markdown("#### Evolução Temporal de Volumes e Market Share")
    
    # Agrupamento temporal contínuo por mês/ano para os gráficos de linha
    df_evolucao = df_filtrado_global.groupby(['ANO_MES', 'MARCA_MAP']).size().reset_index(name='VOL')
    df_evolucao_pivot = df_evolucao.pivot(index='ANO_MES', columns='MARCA_MAP', values='VOL').fillna(0)
    df_evolucao_pivot['TOTAL'] = df_evolucao_pivot.sum(axis=1)
    
    for c in df_evolucao_pivot.columns:
        if c != 'TOTAL':
            df_evolucao_pivot[f'SHARE_{c}'] = (df_evolucao_pivot[c] / df_evolucao_pivot['TOTAL']) * 100
            
    df_evolucao_pivot.index = df_evolucao_pivot.index.astype(str)
    
    fig_macro = go.Figure()
    # Linha de Volume Total do Mercado
    fig_macro.add_trace(go.Scatter(
        x=df_evolucao_pivot.index, y=df_evolucao_pivot['TOTAL'],
        mode='lines+markers+text', name='Mercado Total',
        text=df_evolucao_pivot['TOTAL'].astype(int), textposition="top center",
        line=dict(color='#a3b8cc', width=2, dash='dot')
    ))
    # Linha de Desempenho Mercedes-Benz
    if 'MERCEDES-BENZ' in df_evolucao_pivot.columns:
        fig_macro.add_trace(go.Scatter(
            x=df_evolucao_pivot.index, y=df_evolucao_pivot['MERCEDES-BENZ'],
            mode='lines+markers+text', name='Mercedes-Benz (Vol)',
            text=df_evolucao_pivot['MERCEDES-BENZ'].astype(int), textposition="bottom center",
            line=dict(color='#007bff', width=4)
        ))
    
    fig_macro.update_layout(
        title="Volume Mensal de Emplacamentos",
        template="plotly_dark",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_macro, use_container_width=True)
    
    # Gráfico de Evolução do Market Share (%)
    fig_share = go.Figure()
    for c in df_evolucao_pivot.columns:
        if str(c).startswith('SHARE_'):
            marca_nome = str(c).replace('SHARE_', '')
            cor = '#0056b3' if marca_nome == 'MERCEDES-BENZ' else None
            fig_share.add_trace(go.Scatter(
                x=df_evolucao_pivot.index, y=df_evolucao_pivot[c],
                mode='lines+markers', name=f"Share {marca_nome}",
                line=dict(width=3 if marca_nome == 'MERCEDES-BENZ' else 1, color=cor)
            ))
    fig_share.update_layout(
        title="Evolução do Market Share por Competidor (%)",
        template="plotly_dark", 
        height=350,
        yaxis=dict(ticksuffix="%")
    )
    st.plotly_chart(fig_share, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# ABA 2: VISÃO DE CONCORRÊNCIA
# ────────────────────────────────────────────────────────────────
with aba2:
    st.markdown("#### Distribuição de Market Share por Fabricante")
    
    c_aba2_1, c_aba2_2 = st.columns(2)
    
    with c_aba2_1:
        st.markdown(f"##### Fotografia do Mês ({mes_nomes[mes_sel]})")
        share_m_atual = df_mes_atual['MARCA_MAP'].value_counts().reset_index()
        share_m_atual.columns = ['Fabricante', 'Volume']
        
        fig_pizza_m = go.Figure(data=[go.Pie(
            labels=share_m_atual['Fabricante'], values=share_m_atual['Volume'],
            hole=.4, textinfo='percent+label'
        )])
        fig_pizza_m.update_layout(template="plotly_dark", height=380, showlegend=False)
        st.plotly_chart(fig_pizza_m, use_container_width=True)
        
    with c_aba2_2:
        st.markdown("##### Acumulado Anual (YTD)")
        share_ytd_df = df_ytd['MARCA_MAP'].value_counts().reset_index()
        share_ytd_df.columns = ['Fabricante', 'Volume']
        
        fig_pizza_y = go.Figure(data=[go.Pie(
            labels=share_ytd_df['Fabricante'], values=share_ytd_df['Volume'],
            hole=.4, textinfo='percent+label'
        )])
        fig_pizza_y.update_layout(template="plotly_dark", height=380, showlegend=False)
        st.plotly_chart(fig_pizza_y, use_container_width=True)

    # Análise de Modelos Mais Emplacados da Concorrência
    st.markdown("##### Ranking de Modelos Concorrentes por Volume (YTD)")
    concorrencia_modelos = df_ytd[df_ytd['MARCA_MAP'] != 'MERCEDES-BENZ']
    if not concorrencia_modelos.empty:
        top_modelos_concorrentes = concorrencia_modelos.groupby(['MARCA_MAP', 'MODELO']).size().reset_index(name='Volume')
        top_modelos_concorrentes = top_modelos_concorrentes.sort_values(by='Volume', ascending=False).head(15)
        
        fig_modelos = go.Figure(go.Bar(
            x=top_modelos_concorrentes['Volume'],
            y=top_modelos_concorrentes['MARCA_MAP'] + " " + top_modelos_concorrentes['MODELO'],
            orientation='h',
            marker=dict(color='#c92a2a')
        ))
        fig_modelos.update_layout(template="plotly_dark", height=400, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_modelos, use_container_width=True)
    else:
        st.write("Nenhum registro de concorrente localizado no período selecionado.")

# ────────────────────────────────────────────────────────────────
# ABA 3: COMPRADORES & CARTEIRA
# ────────────────────────────────────────────────────────────────
with aba3:
    st.markdown("#### Monitoramento de Grandes Compradores e Penetração de Carteira")
    
    # Agrupamento por CNPJ Raiz para identificar os maiores players do mercado
    grandes_compradores = df_ytd.groupby(['RAIZ_CNPJ', 'COMPRADOR_NORM', 'CARTEIRA_VENDEDOR']).agg(
        VOLUME_TOTAL=('CHASSI', 'count'),
        VOLUME_MB=('MARCA_MAP', lambda x: (x == 'MERCEDES-BENZ').sum())
    ).reset_index()
    
    grandes_compradores['VOLUME_CONCORRENCIA'] = grandes_compradores['VOLUME_TOTAL'] - grandes_compradores['VOLUME_MB']
    grandes_compradores['SHARE_MB_CLIENTE'] = (grandes_compradores['VOLUME_MB'] / grandes_compradores['VOLUME_TOTAL']) * 100
    grandes_compradores = grandes_compradores.sort_values(by='VOLUME_TOTAL', ascending=False).head(30)
    
    # Gráfico de Barras Empilhadas mostrando share interno no cliente
    fig_compradores = go.Figure()
    fig_compradores.add_trace(go.Bar(
        y=grandes_compradores['COMPRADOR_NORM'], x=grandes_compradores['VOLUME_MB'],
        name='Mercedes-Benz', orientation='h', marker=dict(color='#0056b3')
    ))
    fig_compradores.add_trace(go.Bar(
        y=grandes_compradores['COMPRADOR_NORM'], x=grandes_compradores['VOLUME_CONCORRENCIA'],
        name='Outras Marcas (Concorrência)', orientation='h', marker=dict(color='#495057')
    ))
    
    fig_compradores.update_layout(
        barmode='stack', title="Top 30 Maiores Compradores do Ano (Empilhado)",
        template="plotly_dark", height=600, yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig_compradores, use_container_width=True)
    
    # Tabela detalhada de oportunidades de mercado (Vulnerabilidades da concorrência)
    st.markdown("##### Janela de Oportunidades: Clientes Comprando da Concorrência (YTD)")
    oportunidades = grandes_compradores[grandes_compradores['VOLUME_CONCORRENCIA'] > 0].copy()
    oportunidades = oportunidades.rename(columns={
        'COMPRADOR_NORM': 'Razão Social',
        'CARTEIRA_VENDEDOR': 'Vendedor Alocado',
        'VOLUME_TOTAL': 'Total Comprado',
        'VOLUME_MB': 'Comprado MB',
        'VOLUME_CONCORRENCIA': 'Comprado Concorrência',
        'SHARE_MB_CLIENTE': 'Share MB %'
    })
    st.dataframe(
        oportunidades[['Razão Social', 'Vendedor Alocado', 'Total Comprado', 'Comprado MB', 'Comprado Concorrência', 'Share MB %']],
        use_container_width=True, hide_index=True
    )

# ────────────────────────────────────────────────────────────────
# ABA 4: DISTRIBUIÇÃO GEOGRÁFICA
# ────────────────────────────────────────────────────────────────
with aba4:
    st.markdown("#### Performance Geográfica de Emplacamentos")
    
    c_aba4_1, c_aba4_2 = st.columns(2)
    
    with c_aba4_1:
        st.markdown("##### Desempenho por Estado (UF)")
        geo_uf = df_ytd.groupby(['UF', 'MARCA_MAP']).size().reset_index(name='QTD')
        geo_uf_pivot = geo_uf.pivot(index='UF', columns='MARCA_MAP', values='QTD').fillna(0)
        geo_uf_pivot['Total'] = geo_uf_pivot.sum(axis=1)
        if 'MERCEDES-BENZ' in geo_uf_pivot.columns:
            geo_uf_pivot['Share MB %'] = (geo_uf_pivot['MERCEDES-BENZ'] / geo_uf_pivot['Total']) * 100
        else:
            geo_uf_pivot['Share MB %'] = 0.0
        
        st.dataframe(geo_uf_pivot.sort_values(by='Total', ascending=False), use_container_width=True)
        
    with c_aba4_2:
        st.markdown("##### Top 20 Municípios mais Relevantes em Volume")
        geo_mun = df_ytd.groupby(['MUNICIPIO', 'UF', 'MARCA_MAP']).size().reset_index(name='QTD')
        geo_mun_pivot = geo_mun.pivot(index=['MUNICIPIO', 'UF'], columns='MARCA_MAP', values='QTD').fillna(0)
        geo_mun_pivot['Total_Geral'] = geo_mun_pivot.sum(axis=1)
        geo_mun_top = geo_mun_pivot.sort_values(by='Total_Geral', ascending=False).head(20).reset_index()
        
        fig_mun = go.Figure(go.Bar(
            x=geo_mun_top['Total_Geral'],
            y=geo_mun_top['MUNICIPIO'] + " (" + geo_mun_top['UF'] + ")",
            orientation='h', marker=dict(color='#0b7285')
        ))
        fig_mun.update_layout(template="plotly_dark", height=450, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_mun, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# ABA 5: DETALHAMENTO ANALÍTICO (DATA MINING COMPLETO)
# ────────────────────────────────────────────────────────────────
with aba5:
    st.markdown("#### Base de Dados Consolidada e Filtros de Mineração")
    
    # Converte coluna de data para visualização simplificada
    df_export = df_filtrado_global.copy()
    df_export['DATA_EMPLACAMENTO'] = df_export['DATA_TRATADA'].dt.strftime('%d/%m/%Y')
    
    # Lista de colunas estratégicas estruturada para exportação comercial
    colunas_finais = [
        'DATA_EMPLACAMENTO', 'CNPJ_LIMPO', 'COMPRADOR_NORM', 
        'MARCA_MAP', 'MODELO', 'CHASSI', 'MUNICIPIO', 'UF', 
        'CARTEIRA_VENDEDOR', 'STATUS_CARTEIRA'
    ]
    
    # Filtro em tempo real de busca textual
    busca_termo = st.text_input("🔍 Busca rápida por Razão Social, Chassi ou Modelo:")
    if busca_termo:
        termo_upper = busca_termo.upper().strip()
        df_export = df_export[
            df_export['COMPRADOR_NORM'].str.contains(termo_upper, na=False) |
            df_export['CHASSI'].str.contains(termo_upper, na=False) |
            df_export['MODELO'].str.contains(termo_upper, na=False)
        ]
        
    st.markdown(f"Registros encontrados nesta exibição: **{len(df_export)}**")
    st.dataframe(df_export[colunas_finais], use_container_width=True, hide_index=True)
    
    # Geração dinâmica do arquivo Excel binário em memória para download do usuário
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export[colunas_finais].to_excel(writer, index=False, sheet_name='Emplacamentos_Filtrados')
    processed_data = output.getvalue()
    
    st.download_button(
        label="📥 Baixar Dados Filtrados em Excel (.xlsx)",
        data=processed_data,
        file_name=f"Emplacamentos_Vans_{ano_sel}_{mes_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
