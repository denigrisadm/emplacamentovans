import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from collections import Counter
import os, re, unicodedata, json, hashlib, random
from io import BytesIO
import datetime
import base64
import requests

# ════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES E CONSTANTES
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Emplacamento VANS - De Nigris",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
NOMES_DENIGRIS = ["NIGRIS", "DE NIGRIS"]

# ════════════════════════════════════════════════════════════════
# FUNÇÕES DE NORMALIZAÇÃO E UTILITÁRIOS
# ════════════════════════════════════════════════════════════════

def norm_str(s):
    if not s: return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s

def norm_str_series(series):
    return series.fillna("").astype(str).apply(norm_str)

def norm_cep(val):
    if pd.isna(val): return ""
    s = str(val).replace(".", "").replace("-", "").replace(" ", "").strip()
    if "." in s: s = s.split(".")[0]
    return s.zfill(8)[:8]

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha, hash_armazenado):
    return hash_senha(senha) == hash_armazenado

def safe_str(val, default="—"):
    if pd.isna(val) or val is None: return default
    s = str(val).strip()
    return s if s and s.upper() != "NAN" else default

def format_tel(ddd, tel):
    ddd = str(safe_str(ddd, "")).replace("(", "").replace(")", "").replace("-", "").strip()
    if "." in ddd: ddd = ddd.split(".")[0]
    tel = str(safe_str(tel, "")).replace("-", "").replace(" ", "").strip()
    if "." in tel: tel = tel.split(".")[0]
    if not ddd or not tel: return None
    if len(tel) == 8: return f"({ddd}) {tel[:4]}-{tel[4:]}"
    if len(tel) == 9: return f"({ddd}) {tel[:5]}-{tel[5:]}"
    return f"({ddd}) {tel}"

def make_fone_num(ddd, tel):
    ddd = str(safe_str(ddd, "")).replace("(", "").replace(")", "").replace("-", "").strip()
    if "." in ddd: ddd = ddd.split(".")[0]
    tel = str(safe_str(tel, "")).replace("-", "").replace(" ", "").strip()
    if "." in tel: tel = tel.split(".")[0]
    if not ddd or not tel: return None
    return "55" + ddd + tel

def is_denigris(series):
    return series.astype(str).str.upper().apply(
        lambda x: any(nome in x for nome in NOMES_DENIGRIS)
    )

# ════════════════════════════════════════════════════════════════
# GESTÃO DE USUÁRIOS E PERSISTÊNCIA GITHUB
# ════════════════════════════════════════════════════════════════

def _gh_secrets():
    return (st.secrets.get("GH_TOKEN"), 
            st.secrets.get("GH_REPO"), 
            st.secrets.get("GH_BRANCH", "main"))

def _gh_get_file(url, token):
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        j = r.json()
        return base64.b64decode(j["content"]), j["sha"]
    return None, f"HTTP {r.status_code}"

def _gh_put_file(url, token, branch, content_bytes, sha):
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    data = {
        "message": f"Update users.json {datetime.datetime.now()}",
        "content": base64.b64encode(content_bytes).decode("utf-8"),
        "branch": branch
    }
    if sha: data["sha"] = sha
    r = requests.put(url, headers=headers, json=data)
    return r.status_code in (200, 201)

def load_users():
    token, repo, _ = _gh_secrets()
    if token and repo:
        try:
            url = f"https://api.github.com/repos/{repo}/contents/data/users.json"
            content, _ = _gh_get_file(url, token)
            if content: return json.loads(content.decode("utf-8"))
        except: pass
    
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    
    return {"ADMIN": {"senha_hash": hash_senha("admin2025"), "perfil": "gestor", "nome": "Administrador", "ultimo_acesso": None}}

def save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    content_str = json.dumps(users, ensure_ascii=False, indent=2)
    content_bytes = content_str.encode("utf-8")
    
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            f.write(content_str)
    except: pass
    
    token, repo, branch = _gh_secrets()
    if token and repo:
        try:
            url = f"https://api.github.com/repos/{repo}/contents/data/users.json"
            _, sha = _gh_get_file(url, token)
            _gh_put_file(url, token, branch, content_bytes, sha if not str(sha).startswith("HTTP") else None)
        except: pass
    return True

def registrar_acesso(login):
    users = st.session_state.get("users_db", load_users())
    if login in users:
        agora_brt = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
        users[login]["ultimo_acesso"] = agora_brt.strftime("%Y-%m-%dT%H:%M:%S")
        save_users(users)
        st.session_state.users_db = users

# ════════════════════════════════════════════════════════════════
# CARREGAMENTO DE DADOS
# ════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_carteira(src):
    if isinstance(src, BytesIO): src.seek(0)
    df = pd.read_excel(src)
    df.columns = [c.strip() for c in df.columns]
    col_map = {}
    for c in df.columns:
        cu = str(c).upper()
        if any(k in cu for k in ["CPF","CNPJ"]): col_map[c] = "CNPJ_RAW"
        elif "VENDEDOR" in cu: col_map[c] = "VENDEDOR"
    df = df.rename(columns=col_map)
    df["CNPJ_NORM"] = df["CNPJ_RAW"].astype(str).str.replace(r"\D", "", regex=True)
    df["VENDEDOR"] = df["VENDEDOR"].astype(str).str.strip()
    return df

@st.cache_data(show_spinner=False)
def load_emplacamentos(src, label=""):
    if isinstance(src, BytesIO): src.seek(0)
    raw = pd.read_excel(src, header=None, nrows=15)
    header_row = 0
    for i in range(len(raw)):
        if any("Chassi" in str(v) for v in raw.iloc[i].tolist()):
            header_row = i; break
    if isinstance(src, BytesIO): src.seek(0)
    df = pd.read_excel(src, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    
    df["CNPJ_NORM"] = df["NU_CPF_CNPJ"].astype(str).str.replace(r"\D", "", regex=True)
    df["Data emplacamento"] = pd.to_datetime(df["DT_EMPLACAMENTO"], dayfirst=True, errors="coerce")
    df["Ano"] = df["Data emplacamento"].dt.year
    df["Mes"] = df["Data emplacamento"].dt.month
    df["NO_CIDADE_NORM"] = norm_str_series(df["NO_CIDADE"])
    df["_fonte"] = label
    
    df.dropna(subset=["Ano"], inplace=True)
    df["Ano"] = df["Ano"].astype(int)
    
    return df

def distribuir_clientes(df_emp, df_cart, vendedores):
    cnpjs_cart = set(df_cart["CNPJ_NORM"].unique())
    nao_cad = df_emp[~df_emp["CNPJ_NORM"].isin(cnpjs_cart)].drop_duplicates(subset=["CNPJ_NORM"])
    lista_cnpjs = nao_cad["CNPJ_NORM"].tolist()
    random.seed(42)
    random.shuffle(lista_cnpjs)
    dist = {v: [] for v in vendedores}
    for i, cnpj in enumerate(lista_cnpjs):
        v = vendedores[i % len(vendedores)]
        dist[v].append(cnpj)
    return dist

# ════════════════════════════════════════════════════════════════
# INTERFACE STREAMLIT (VERSÃO ESTÁVEL)
# ════════════════════════════════════════════════════════════════

def show_login():
    st.markdown("<h1 style='text-align: center;'>🚐 Emplacamento VANS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                users = load_users()
                if u in users and verificar_senha(p, users[u]["senha_hash"]):
                    st.session_state.auth = True
                    st.session_state.user = u
                    st.session_state.perfil = users[u]["perfil"]
                    registrar_acesso(u)
                    st.rerun()
                else: st.error("Usuário ou senha inválidos")

def show_main():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user}")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
        st.markdown("---")
        if st.session_state.perfil == "gestor":
            menu = st.radio("Menu", ["📊 Dashboard", "🎯 Distribuição", "👥 Usuários"])
        else:
            menu = st.radio("Menu", ["📋 Meus Clientes", "📈 Histórico"])

    if menu == "📊 Dashboard": show_dashboard()
    elif menu == "🎯 Distribuição": show_dist_page()
    elif menu == "📋 Meus Clientes": show_vendedor_clientes()
    elif menu == "📈 Histórico": show_historico_geral()
    elif menu == "👥 Usuários": show_users_page()

def show_dashboard():
    st.title("📊 Dashboard")
    f1, f2 = st.columns(2)
    with f1: f_cart = st.file_uploader("Carteira", type=["xlsx"])
    with f2: f_emp = st.file_uploader("Emplacamentos", type=["xlsx"])
    
    if f_cart and f_emp:
        if st.button("Processar Dados", use_container_width=True):
            st.session_state.df_cart = load_carteira(f_cart)
            st.session_state.df_emp = load_emplacamentos(f_emp, "Upload")
            st.rerun()
    
    if "df_emp" in st.session_state:
        df = st.session_state.df_emp
        st.metric("Total Emplacamentos", len(df))
        st.dataframe(df.head(100), use_container_width=True)

def show_dist_page():
    st.title("🎯 Distribuição")
    if "df_cart" not in st.session_state:
        st.warning("Carregue os dados no Dashboard.")
        return
    vendedores = sorted([v for v in st.session_state.df_cart["VENDEDOR"].unique() if v and v != "nan"])
    if st.button("Realizar Distribuição", type="primary"):
        st.session_state.dist = distribuir_clientes(st.session_state.df_emp, st.session_state.df_cart, vendedores)
        st.success("Concluído!")
    if "dist" in st.session_state:
        st.write(pd.DataFrame([{"Vendedor": k, "Qtd": len(v)} for k, v in st.session_state.dist.items()]))

def show_vendedor_clientes():
    st.title("📋 Meus Clientes")
    if "dist" not in st.session_state:
        st.info("Aguardando distribuição.")
        return
    user = st.session_state.user
    vendedor_sel = st.selectbox("Vendedor:", list(st.session_state.dist.keys())) if st.session_state.perfil == "gestor" else user
    cnpjs = st.session_state.dist.get(vendedor_sel, [])
    
    if not cnpjs:
        st.info("Nenhum cliente.")
        return

    df_meus = st.session_state.df_emp[st.session_state.df_emp["CNPJ_NORM"].isin(cnpjs)].copy()
    clientes_unicos = df_meus.drop_duplicates(subset=["CNPJ_NORM"]).sort_values("DT_EMPLACAMENTO", ascending=False)
    
    for _, row in clientes_unicos.iterrows():
        with st.expander(f"🏢 {row['NO_PROPRIETARIO']}"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**CNPJ:** {row['CNPJ_NORM']}")
                st.write(f"**Cidade:** {row['NO_CIDADE']}")
                addr = f"{row['NO_LOGR_CONTATO1']}, {row['NU_LOGR_CONTATO1']}, {row['NO_CIDADE']}".replace(" ","+")
                st.markdown(f"[🗺️ Google Maps](https://www.google.com/maps/search/?api=1&query={addr})")
                st.markdown(f"[🚗 Waze](https://waze.com/ul?q={addr})")
            with c2:
                st.write("**Contatos:**")
                for i in range(1, 4):
                    tel = format_tel(row.get(f'DDD{i}_CEL_SOCIO1'), row.get(f'TEL{i}_CEL_SOCIO1'))
                    num = make_fone_num(row.get(f'DDD{i}_CEL_SOCIO1'), row.get(f'TEL{i}_CEL_SOCIO1'))
                    if tel: st.markdown(f"📱 {tel} [WhatsApp](https://wa.me/{num})")

def show_historico_geral():
    st.title("📈 Histórico")
    if "df_emp" in st.session_state: st.dataframe(st.session_state.df_emp)

def show_users_page():
    st.title("👥 Usuários")
    users = load_users()
    with st.form("new"):
        nu, nn, np, ns = st.text_input("Usuário"), st.text_input("Nome"), st.selectbox("Perfil", ["vendedor", "gestor"]), st.text_input("Senha", type="password")
        if st.form_submit_button("Criar"):
            users[nu] = {"senha_hash": hash_senha(ns), "perfil": np, "nome": nn, "ultimo_acesso": None}
            save_users(users)
            st.rerun()

def main():
    if "auth" not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth: show_login()
    else: show_main()

if __name__ == "__main__":
    main()
