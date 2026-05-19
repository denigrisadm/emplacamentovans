import streamlit as st
import pandas as pd
import plotly.graph_objects go
from dateutil.relativedelta import relativedelta
from collections import Counter
import os, re, unicodedata, json, hashlib
from io import BytesIO
import datetime
import base64

st.set_page_config(
    page_title="Comercial De Nigris",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ════════════════════════════════════════════════════════════════
# PWA — Ícone para iPhone/Android (adicionar à tela inicial)
# ════════════════════════════════════════════════════════════════
_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAIAAADdvvtQAAABC...[TRUNCADO]"

def inject_pwa():
    manifest = {
        "name": "Emplacamento Vans",
        "short_name": "Emp. Vans",
        "description": "Inteligência Comercial De Nigris",
        "start_url": ".",
        "display": "standalone",
        "background_color": "#0a1628",
        "theme_color": "#0a1628",
        "icons": [
            {"src": f"data:image/png;base64,{_ICON_B64}", "sizes": "192x192", "type": "image/png"},
        ]
    }
    import json as _json
    manifest_b64 = __import__("base64").b64encode(_json.dumps(manifest).encode()).decode()
    st.markdown(f"""
    <link rel="manifest" href="data:application/manifest+json;base64,{manifest_b64}">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Emp. Vans">
    <link rel="apple-touch-icon" href="data:image/png;base64,{_ICON_B64}">
    <meta name="theme-color" content="#0a1628">
    <meta name="mobile-web-app-capable" content="yes">
    """, unsafe_allow_html=True)

inject_pwa()

# ── LOGO em base64 ──
LOGO_B64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCARlB9ADASIAAhEBAxEB/8QAHQABAAMAAwEBAQAAAAAAAAAAAAcICQQFBgMCAf/EAGcQAQABAwMCAwIHBg0NCwsDBQABAgMEBQYRBxIIITETQQkUIjJRYYE3OHF2s7QVFhgjQlJzdISRoaWxFyQzNEdWZ4WSlcTT5DVXYnKCk6KjwdHSQ1NUVWWUpLLC1OIlNnWDJkVjw//EABsBAQACAwEBAAAAAAAAAAAAAAAEBQIDBgEH/8QAMREBAAEDAQUECQUBAAAAAAAAAAECAwQRBRIhMUEyQoHBExQiUWFxkaHRFSNSseHx/9oADAMBAAIRAxEAPwCmQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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════════════════════════════════


# ── SISTEMA DE CACHE SEGURO (Prevenção de Corrupção de Estado) ──
@st.cache_data(show_spinner=False, ttl=600)
def get_file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()

@st.cache_data(show_spinner="Processando arquivo de Carteira...", ttl=600)
def load_carteira(file_bytes):
    try:
        df = pd.read_excel(file_bytes)
        df.columns = df.columns.str.strip().str.upper()
        # Normalização de strings para evitar quebras por acentos ou espaços extras
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar Carteira: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Processando arquivo de Emplacamentos...", ttl=600)
def load_emplacamentos(file_bytes, label=""):
    try:
        df = pd.read_excel(file_bytes)
        df.columns = df.columns.str.strip().str.upper()
        
        # Mapeamento e detecção automática de datas
        col_data = None
        for c in ['DATA', 'DATA_EMPLACAMENTO', 'DT_EMPLAC', 'MES']:
            if c in df.columns:
                col_data = c
                break
        
        if col_data:
            df['DATA_REF'] = pd.to_datetime(df[col_data], errors='coerce')
        else:
            df['DATA_REF'] = pd.to_datetime(datetime.date.today())
            
        df['FONTE_ARQUIVO'] = label
        
        for col in df.select_dtypes(include=['object']).columns:
            if col != 'FONTE_ARQUIVO':
                df[col] = df[col].astype(str).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.strip().str.upper()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar Emplacamentos ({label}): {e}")
        return pd.DataFrame()


# ── INICIALIZAÇÃO SEGURA DE ESTADOS (Session State) ──
if 'df_cart' not in st.session_state:
    st.session_state.df_cart = pd.DataFrame()
if 'df_emp_list' not in st.session_state:
    st.session_state.df_emp_list = []
if 'emp_fontes' not in st.session_state:
    st.session_state.emp_fontes = []


# ── ESTILIZAÇÃO COMPLETA DA INTERFACE (CSS Customizado) ──
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #060d17 !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #0f1c2e 0%, #08111f 100%);
        padding: 20px 25px;
        border-radius: 12px;
        border-left: 5px solid #0052cc;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .main-title {
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .main-subtitle {
        font-size: 13px;
        color: #718096;
        margin-top: 4px;
        margin-bottom: 0;
    }
    .upload-box {
        background-color: #0f1c2e;
        border: 1px dashed #1e293b;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    .upload-box:hover {
        border-color: #0052cc;
        background-color: #132237;
    }
    .upload-title {
        font-size: 14px;
        font-weight: 600;
        color: #38bdf8;
        margin-bottom: 10px;
    }
    .card-metric {
        background: #0f1c2e;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .metric-value {
        font-size: 30px;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-label {
        font-size: 12px;
        color: #94a3b8;
        text-transform: uppercase;
        margin-top: 5px;
    }
    /* Ocultar elementos desnecessários do Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)


# ── RENDERIZAÇÃO DO TOPO (Header com Logo) ──
logo_html = f'<img src="data:image/png;base64,{LOGO_B64}" style="height:48px; object-fit:contain;">' if LOGO_B64 else ""
st.markdown(f"""
    <div class="main-header">
        <div>
            <h1 class="main-title">Emplacamento Vans</h1>
            <p class="main-subtitle">Inteligência Comercial & Análise Corporativa — De Nigris</p>
        </div>
        <div>
            {logo_html}
        </div>
    </div>
""", unsafe_allow_html=True)


# ── SEÇÃO DE UPLOADS (Estrutura Unificada em Duas Colunas) ──
with st.expander("📂 GERENCIADOR DE BASES DE DADOS", expanded=not bool(st.session_state.emp_fontes)):
    col_u1, col_u2 = st.columns(2)
    
    with col_u1:
        st.markdown('<div class="upload-box"><div class="upload-title">📋 Carteira Interna</div>', unsafe_allow_html=True)
        up_c = st.file_uploader("Arraste ou selecione CARTEIRA.xlsx", type=["xlsx"], key="up_cart_vans")
        if up_c:
            st.session_state.df_cart = load_carteira(BytesIO(up_c.getvalue()))
            st.success("✅ Carteira interna atualizada com sucesso!")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_u2:
        st.markdown('<div class="upload-box"><div class="upload-title">🚚 Mercado (Emplacamentos)</div>', unsafe_allow_html=True)
        up_e = st.file_uploader("Arraste ou selecione EMPLACAMENTOS.xlsx (Múltiplos permitidos)", type=["xlsx"], key="up_emp_vans", accept_multiple_files=True)
        if up_e:
            novos = 0
            for f in up_e:
                if f.name not in st.session_state.emp_fontes:
                    st.session_state.df_emp_list.append(load_emplacamentos(BytesIO(f.getvalue()), label=f.name))
                    st.session_state.emp_fontes.append(f.name)
                    novos += 1
            if novos: 
                st.success(f"✅ {novos} nova(s) base(s) de emplacamento injetada(s)!")
        
        if st.session_state.emp_fontes:
            st.markdown("**Bases carregadas atualmente:** " + ", ".join([f"`{f}`" for f in st.session_state.emp_fontes]))
            if st.button("🗑️ Limpar Arquivos de Emplacamento", key="btn_clear_vans"):
                st.session_state.df_emp_list = []
                st.session_state.emp_fontes = []
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# Consolidação Dinâmica do Dataframe de Emplacamentos
df_emp = pd.concat(st.session_state.df_emp_list, ignore_index=True) if st.session_state.df_emp_list else pd.DataFrame()


# ── EXECUÇÃO DA INTELIGÊNCIA DE MERCADO (Se as bases existirem) ──
if not df_emp.empty:
    
    # Validador de colunas críticas
    colunas_necessarias = ['DATA_REF', 'MARCA', 'MODELO', 'ESTADO', 'MUNICIPIO']
    for col in colunas_necessarias:
        if col not in df_emp.columns:
            df_emp[col] = "N/D"

    # ── PAINEL DE FILTROS AVANÇADOS ──
    st.markdown("### 🔍 Filtros Estratégicos")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        anos_disponiveis = sorted(list(df_emp['DATA_REF'].dt.year.dropna().unique()), reverse=True)
        ano_sel = st.selectbox("Ano de Referência", anos_disponiveis if anos_disponiveis else [2026], key="f_ano")
        df_filtrado = df_emp[df_emp['DATA_REF'].dt.year == ano_sel] if anos_disponiveis else df_emp.copy()
        
    with col_f2:
        marcas_disponiveis = sorted(list(df_filtrado['MARCA'].dropna().unique()))
        marcas_sel = st.multiselect("Montadora / Marca", marcas_disponiveis, key="f_marca")
        if marcas_sel:
            df_filtrado = df_filtrado[df_filtrado['MARCA'].isin(marcas_sel)]
            
    with col_f3:
        estados_disponiveis = sorted(list(df_filtrado['ESTADO'].dropna().unique()))
        estados_sel = st.multiselect("Estado (UF)", estados_disponiveis, key="f_uf")
        if estados_sel:
            df_filtrado = df_filtrado[df_filtrado['ESTADO'].isin(estados_sel)]
            
    with col_f4:
        modelos_disponiveis = sorted(list(df_filtrado['MODELO'].dropna().unique()))
        modelos_sel = st.multiselect("Modelo de Van", modelos_disponiveis, key="f_mod")
        if modelos_sel:
            df_filtrado = df_filtrado[df_filtrado['MODELO'].isin(modelos_sel)]

    # Cálculo do volume total do mercado filtrado
    total_mercado = len(df_filtrado)
    # Exemplo de cálculo de Market Share interno focado em MERCEDES-BENZ
    total_mb = len(df_filtrado[df_filtrado['MARCA'].str.contains('MERCEDES', na=False)])
    share_mb = (total_mb / total_mercado * 100) if total_mercado > 0 else 0.0

    # ── CARDS DE PERFORMANCE OPERACIONAL ──
    st.markdown("---")
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.markdown(f'<div class="card-metric"><div class="metric-value">{total_mercado:,}</div><div class="metric-label">Volume de Mercado Regulado</div></div>', unsafe_allow_html=True)
    with c_m2:
        st.markdown(f'<div class="card-metric"><div class="metric-value">{total_mb:,}</div><div class="metric-label">Emplacamentos Mercedes-Benz</div></div>', unsafe_allow_html=True)
    with c_m3:
        st.markdown(f'<div class="card-metric"><div class="metric-value">{share_mb:.2f}%</div><div class="metric-label">Market Share Estimado MB</div></div>', unsafe_allow_html=True)

    # ── VISUALIZAÇÕES E GRÁFICOS ANALÍTICOS ──
    st.markdown("### 📊 Comportamento e Volumetria de Vendas")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Distribuição Mensal de Emplacamentos
        df_filtrado['MES_NOME'] = df_filtrado['DATA_REF'].dt.strftime('%m - %b')
        evolucao_mensal = df_filtrado.groupby('MES_NOME').size().reset_index(name='Volume')
        evolucao_mensal = evolucao_mensal.sort_values('MES_NOME')
        
        fig_mes = go.Figure(data=[
            go.Scatter(
                x=evolucao_mensal['MES_NOME'], 
                y=evolucao_mensal['Volume'],
                mode='lines+markers',
                line=dict(color='#0052cc', width=3),
                marker=dict(size=8, color='#38bdf8')
            )
        ])
        fig_mes.update_layout(
            title="Evolução Temporal de Emplacamentos (Mensal)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_mes, use_container_width=True)
        
    with col_g2:
        # Maiores Competidores (Top Marcas)
        top_marcas = df_filtrado['MARCA'].value_counts().head(7).reset_index(name='Volume')
        top_marcas.columns = ['Marca', 'Volume']
        top_marcas = top_marcas.sort_values('Volume', ascending=True)
        
        fig_marca = go.Figure(data=[
            go.Bar(
                y=top_marcas['Marca'],
                x=top_marcas['Volume'],
                orientation='h',
                marker_color='#38bdf8'
            )
        ])
        fig_marca.update_layout(
            title="Market Share - Top Marcas do Segmento",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_marca, use_container_width=True)

    # ── MÓDULO ADICIONAL: CRUZAMENTO DE CARTEIRA INTERNA VS MERCADO ──
    if not st.session_state.df_cart.empty:
        st.markdown("### 🔄 Penetração de Mercado vs Carteira Interna")
        # Exemplo de lógica de cruzamento (ex: comparar clientes da carteira com registros de emplacamento)
        st.info("💡 Base de Carteira carregada. Implemente chaves como CNPJ/CPF ou Chassi para gerar relatórios de Market Share Nominativo (Clientes que compraram da concorrência).")
        
        with st.expander("Visualizar Dados Brutos da Carteira"):
            st.dataframe(st.session_state.df_cart.head(100), use_container_width=True)

else:
    # Estado inicial com instruções limpas
    st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background-color: #0f1c2e; border-radius: 12px; border: 1px solid #1e293b;">
            <p style="font-size: 48px; margin-bottom: 10px;">📊</p>
            <h3 style="color: #ffffff; font-weight: 600; margin-bottom: 8px;">Nenhum arquivo de mercado carregado</h3>
            <p style="color: #94a3b8; max-width: 500px; margin: 0 auto 20px auto; font-size: 14px;">
                Para começar a analisar a performance do mercado de Vans, expanda o gerenciador acima e faça o upload dos arquivos contendo os dados de emplacamento.
            </p>
        </div>
    """, unsafe_allow_html=True)
