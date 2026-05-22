import base64
import qrcode
import pandas as pd
from io import BytesIO
import streamlit as st
from rapidfuzz import process, fuzz

# ------------------- CONFIGURAÇÃO DA PLANILHA -------------------
url_edit = "https://docs.google.com/spreadsheets/d/1_1FzkSOXCBESZScXFXIzESkpP9HQu29y8c-huOv_Fz0/edit?usp=drivesdk"
sheet_id = url_edit.split('/d/')[1].split('/')[0]
url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

@st.cache_data(ttl=3600)  # cache para não recarregar a planilha a cada interação
def load_data():
    df = pd.read_csv(url_csv)
    df.columns = df.columns.str.strip()
    colunas = ['Marca', 'Descrição', 'Apresentação', 'Cód. EAN']
    df = df[colunas].copy()
    df['texto_busca'] = df['Marca'] + " " + df['Descrição'] + " " + df['Apresentação']
    return df

df = load_data()
produtos = df.to_dict('records')

# ------------------- FUNÇÃO DE BUSCA -------------------
def buscar_produtos(termo, limite=5):
    if not termo or len(termo) < 2:
        return []
    textos = df['texto_busca'].tolist()
    resultados = process.extract(termo, textos, scorer=fuzz.WRatio, limit=limite)
    indices = [r[2] for r in resultados if r[1] >= 40]
    return [produtos[i] for i in indices]

# ------------------- FUNÇÃO QR CODE -------------------
def gerar_qr_code(ean):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(ean)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# ------------------- INTERFACE STREAMLIT -------------------
st.set_page_config(page_title="Consulta de Produtos", page_icon="🔍", layout="centered")

st.markdown("<h2 style='text-align: center;'>🔍 Consulta avançada de produtos</h2>", unsafe_allow_html=True)

# Caixa de busca
termo = st.text_input("Digite marca, descrição ou parte do nome", placeholder="Ex: shampoo dove", key="busca")

if termo and len(termo) >= 2:
    matches = buscar_produtos(termo)
    if matches:
        # Cria uma lista de strings para exibir no selectbox
        opcoes = [f"{p['Marca']} | {p['Descrição']} ({p['Apresentação'][:30]})" for p in matches]
        indice_selecionado = st.selectbox("Produtos encontrados:", range(len(opcoes)), format_func=lambda i: opcoes[i])
        produto = matches[indice_selecionado]

        if st.button("Selecionar produto", use_container_width=True):
            # Exibe informações do produto
            st.markdown("---")
            st.markdown("<h3 style='text-align: center;'>📦 Produto selecionado</h3>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style='text-align:center; font-size:1.1rem; margin:10px 0;'>
                    <strong>{produto['Marca']} | {produto['Descrição']}</strong><br>
                    {produto['Apresentação']}
                </div>
            """, unsafe_allow_html=True)

            # Gera e exibe QR Code
            img_buffer = gerar_qr_code(produto['Cód. EAN'])
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            st.markdown(f"""
                <div style='display:flex; flex-direction:column; align-items:center; margin:15px 0;'>
                    <img src="data:image/png;base64,{img_base64}" style='max-width:200px; width:80%; height:auto;' />
                    <span style='margin-top:10px; font-family:monospace; font-size:1rem;'>{produto['Cód. EAN']}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Nenhum produto encontrado com esse termo.")
else:
    if termo:
        st.info("Digite pelo menos 2 caracteres para buscar.")
