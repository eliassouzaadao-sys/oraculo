"""
Oraculo - Assistente de Conhecimento
Interface identica ao ChatGPT.
"""
import os
import tempfile
import streamlit as st

# Configura o caminho para imports
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.database import get_knowledge_base
from core.rag import get_oracle_rag
from loaders.documents import carrega_documento, LOADERS_DOCUMENTOS
from loaders.web import carrega_url, detecta_tipo_url
from loaders.images import carrega_imagem, verificar_tesseract, eh_imagem

# Configuracao da pagina
st.set_page_config(
    page_title="Oraculo",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS identico ao ChatGPT
st.markdown("""
<style>
    /* Reset e base */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Fundo principal #212121 */
    .stApp {
        background-color: #212121;
    }

    .main .block-container {
        background-color: #212121;
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Sidebar escura */
    [data-testid="stSidebar"] {
        background-color: #171717;
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    [data-testid="stSidebar"] > div:first-child {
        background-color: #171717;
        padding-top: 1rem;
    }

    /* Textos na sidebar */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #ececec !important;
    }

    /* Botoes na sidebar */
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #ececec !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        font-size: 0.875rem !important;
        transition: background-color 0.2s !important;
    }

    [data-testid="stSidebar"] button:hover {
        background-color: rgba(255,255,255,0.1) !important;
    }

    /* Expander na sidebar */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background-color: transparent !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        color: #ececec !important;
    }

    [data-testid="stSidebar"] .streamlit-expanderContent {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* File uploader na sidebar */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px dashed rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] label {
        color: #b4b4b4 !important;
    }

    /* Input de texto na sidebar */
    [data-testid="stSidebar"] input[type="text"] {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #ececec !important;
        border-radius: 8px !important;
    }

    /* Area principal do chat */
    .main-chat-area {
        display: flex;
        flex-direction: column;
        height: calc(100vh - 100px);
        max-width: 768px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }

    /* Mensagens */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 1.5rem 0 !important;
        max-width: 768px;
        margin: 0 auto;
    }

    /* Mensagem do usuario */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background-color: transparent !important;
    }

    /* Avatar */
    [data-testid="stChatMessage"] [data-testid="stImage"],
    [data-testid="stChatMessage"] img {
        border-radius: 9999px !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
    }

    /* Texto das mensagens */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {
        color: #ececec !important;
    }

    /* Input do chat - estilo pill */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
        border: none !important;
        max-width: 768px;
        margin: 0 auto;
        padding: 0 1rem;
    }

    [data-testid="stChatInput"] > div {
        background-color: #2f2f2f !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 26px !important;
        padding: 0.25rem 0.5rem !important;
    }

    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #ececec !important;
        border: none !important;
        font-size: 1rem !important;
        padding: 0.75rem 1rem !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: rgba(255,255,255,0.5) !important;
    }

    /* Botao de enviar */
    [data-testid="stChatInput"] button {
        background-color: white !important;
        border-radius: 9999px !important;
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        padding: 0 !important;
        margin: 0.25rem !important;
    }

    [data-testid="stChatInput"] button svg {
        color: black !important;
        fill: black !important;
    }

    [data-testid="stChatInput"] button:disabled {
        opacity: 0.3 !important;
        background-color: rgba(255,255,255,0.3) !important;
    }

    /* Titulo central */
    .chat-title {
        text-align: center;
        color: #ececec;
        font-size: 1.75rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .chat-subtitle {
        text-align: center;
        color: #8e8ea0;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Sugestoes de perguntas */
    .suggestion-btn {
        background-color: #2f2f2f !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #ececec !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        text-align: left !important;
        font-size: 0.9rem !important;
        transition: all 0.2s !important;
    }

    .suggestion-btn:hover {
        background-color: #3f3f3f !important;
        border-color: rgba(255,255,255,0.2) !important;
    }

    /* Disclaimer no rodape */
    .disclaimer {
        text-align: center;
        color: #8e8ea0;
        font-size: 0.75rem;
        padding: 1rem;
        position: fixed;
        bottom: 60px;
        left: 50%;
        transform: translateX(-50%);
    }

    /* Esconde elementos desnecessarios */
    #MainMenu, footer, header {
        visibility: hidden;
    }

    /* Divider na sidebar */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1) !important;
        margin: 1rem 0 !important;
    }

    /* Warning/Info boxes */
    .stAlert {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #ececec !important;
    }

    /* Success message */
    [data-testid="stSidebar"] .stSuccess {
        background-color: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-color: rgba(255,255,255,0.3) !important;
        border-top-color: white !important;
    }

    /* Scrollbar estilizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.2);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.3);
    }
</style>
""", unsafe_allow_html=True)


def verificar_configuracao():
    """Verifica se a API key esta configurada."""
    if not Config.is_configured():
        st.error("API Key nao configurada!")
        st.info(
            "Configure sua API Key da OpenAI no arquivo `.env`:\n\n"
            "`OPENAI_API_KEY=sua-chave-aqui`"
        )
        st.stop()


def processar_arquivo(arquivo_upload):
    """Processa um arquivo enviado pelo usuario."""
    if arquivo_upload is None:
        return None, None

    nome = arquivo_upload.name
    extensao = os.path.splitext(nome)[1].lower()

    with tempfile.NamedTemporaryFile(suffix=extensao, delete=False) as temp:
        temp.write(arquivo_upload.read())
        caminho_temp = temp.name

    try:
        if eh_imagem(caminho_temp):
            if not verificar_tesseract():
                return None, None
            texto = carrega_imagem(caminho_temp)
            tipo = 'imagem'
        else:
            texto = carrega_documento(caminho_temp, extensao)
            tipo = extensao.replace('.', '')

        return texto, tipo
    finally:
        try:
            os.unlink(caminho_temp)
        except:
            pass


def processar_url(url):
    """Processa uma URL (site ou YouTube)."""
    if not url or not url.strip():
        return None, None

    url = url.strip()
    tipo = detecta_tipo_url(url)

    if tipo is None:
        return None, None

    try:
        texto, tipo = carrega_url(url)
        return texto, tipo
    except Exception:
        return None, None


def adicionar_a_base(texto, fonte, tipo):
    """Adiciona documento a base de conhecimento."""
    if not texto:
        return False

    try:
        kb = get_knowledge_base()
        num_chunks = kb.adicionar_documento(texto, fonte, tipo)
        return num_chunks > 0
    except Exception:
        return False


def sidebar():
    """Sidebar com opcoes."""
    kb = get_knowledge_base()
    stats = kb.get_estatisticas()

    # Logo/Titulo
    st.markdown("### 🔮 Oraculo")

    # Botao nova conversa
    if st.button("+ Nova conversa", use_container_width=True):
        st.session_state['mensagens'] = []
        oracle = get_oracle_rag()
        oracle.limpar_memoria()
        st.rerun()

    st.markdown("---")

    # Info da base
    st.caption(f"📚 {stats['total_documentos']} documento(s) na base")

    # Adicionar documento
    with st.expander("➕ Adicionar documento"):
        extensoes = list(LOADERS_DOCUMENTOS.keys()) + ['.png', '.jpg', '.jpeg']
        arquivo = st.file_uploader(
            "Arraste ou clique",
            type=[e.replace('.', '') for e in extensoes],
            help="PDF, Word, Excel, PowerPoint, TXT, CSV, JSON, Imagens",
            label_visibility="collapsed"
        )

        if arquivo:
            with st.spinner("Processando..."):
                texto, tipo = processar_arquivo(arquivo)
                if texto:
                    if adicionar_a_base(texto, arquivo.name, tipo):
                        st.success(f"Adicionado!")
                        st.rerun()

        st.caption("Ou adicione por link:")
        url = st.text_input("URL", placeholder="https://...", label_visibility="collapsed")

        if st.button("Adicionar", use_container_width=True, key="btn_url"):
            if url:
                with st.spinner("Carregando..."):
                    texto, tipo = processar_url(url)
                    if texto:
                        if adicionar_a_base(texto, url, tipo):
                            st.success("Adicionado!")
                            st.rerun()

    # Ver documentos
    if stats['fontes']:
        with st.expander("📄 Ver documentos"):
            for fonte in stats['fontes']:
                nome = fonte[:30] + "..." if len(fonte) > 30 else fonte
                st.caption(f"• {nome}")

    st.markdown("---")

    # Opcoes
    with st.expander("⚙️ Opcoes"):
        if st.button("🗑️ Limpar tudo", use_container_width=True):
            if kb.limpar_base():
                st.session_state['mensagens'] = []
                st.rerun()


def chat_interface():
    """Interface principal do chat."""
    oracle = get_oracle_rag()
    kb = get_knowledge_base()
    stats = kb.get_estatisticas()

    # Inicializa historico
    if 'mensagens' not in st.session_state:
        st.session_state['mensagens'] = []

    # Tela inicial quando nao tem mensagens
    if not st.session_state['mensagens']:
        st.markdown("")
        st.markdown("")
        st.markdown("<h1 class='chat-title'>🔮 Oraculo</h1>", unsafe_allow_html=True)

        if stats['total_documentos'] > 0:
            st.markdown(f"<p class='chat-subtitle'>Base com {stats['total_documentos']} documento(s) - Pergunte qualquer coisa</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='chat-subtitle'>Adicione documentos no menu lateral para comecar</p>", unsafe_allow_html=True)

        # Sugestoes
        if stats['total_documentos'] > 0:
            st.markdown("")
            col1, col2 = st.columns(2)

            sugestoes = [
                ("💡", "O que voce sabe?", "Resuma o conteudo dos documentos"),
                ("📋", "Faca um resumo", "Liste os pontos principais"),
                ("🔍", "Detalhes importantes", "Quais informacoes relevantes tem?"),
                ("❓", "Posso perguntar sobre...", "Quais topicos voce conhece?")
            ]

            for i, (icon, titulo, desc) in enumerate(sugestoes):
                with [col1, col2][i % 2]:
                    if st.button(f"{icon} **{titulo}**\n\n{desc}", key=f"sug_{i}", use_container_width=True):
                        st.session_state['mensagens'].append({
                            'role': 'user',
                            'content': titulo
                        })
                        st.rerun()

    # Exibe mensagens
    for msg in st.session_state['mensagens']:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # Input
    if pergunta := st.chat_input("Envie uma mensagem"):
        if stats['total_documentos'] == 0:
            st.warning("Adicione documentos primeiro")
            st.stop()

        st.session_state['mensagens'].append({
            'role': 'user',
            'content': pergunta
        })

        with st.chat_message('user'):
            st.markdown(pergunta)

        with st.chat_message('assistant'):
            placeholder = st.empty()
            resposta = ""

            try:
                for token in oracle.responder(pergunta):
                    resposta += token
                    placeholder.markdown(resposta + "▌")
                placeholder.markdown(resposta)
            except Exception:
                resposta = "Desculpe, ocorreu um erro. Tente novamente."
                placeholder.markdown(resposta)

        st.session_state['mensagens'].append({
            'role': 'assistant',
            'content': resposta
        })


def main():
    """Funcao principal."""
    verificar_configuracao()

    with st.sidebar:
        sidebar()

    chat_interface()


if __name__ == '__main__':
    main()
