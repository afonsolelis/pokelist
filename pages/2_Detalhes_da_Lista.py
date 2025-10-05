import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# --- Configuração e Funções de DB ---
load_dotenv()
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    @media (max-width: 900px) {
        div[data-testid=\"column\"] { width: 100% !important; flex: 1 0 100% !important; min-width: 0 !important; }
        div[data-testid=\"stHorizontalBlock\"] { gap: 0.5rem !important; }
        .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

LANGUAGES = [
    "Português", "Inglês", "Japonês", "Italiano", "Espanhol", 
    "Alemão", "Francês", "Chinês Simplificado", "Chinês Tradicional", "Coreano"
]

# --- Verificação de Estado ---
if 'current_list_id' not in st.session_state:
    st.error("Nenhuma lista selecionada!")
    # Em deploy com app.py como entrypoint, a página inicial é app.py
    st.page_link("app.py", label="Voltar para a Visualização", icon="🏠")
    st.stop()

list_id = st.session_state['current_list_id']
list_name = st.session_state['current_list_name']

# --- Funções da Página ---
def get_cards_for_list(list_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, photo_url, card_number, collection_total, language, card_order, grading_note, condition, owned FROM cards WHERE list_id = %s ORDER BY card_order ASC", (list_id,))
    cards = cur.fetchall()
    cur.close()
    conn.close()
    return cards

def swap_card_order(card1_id, card1_order, card2_id, card2_order):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Troca a ordem em uma única transação
        cur.execute("UPDATE cards SET card_order = %s WHERE id = %s", (card2_order, card1_id))
        cur.execute("UPDATE cards SET card_order = %s WHERE id = %s", (card1_order, card2_id))
        conn.commit()
        cur.close()
        conn.close()
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao reordenar: {e}")

def toggle_owned_status(card_id, current_status):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE cards SET owned = %s WHERE id = %s", (not current_status, card_id))
        conn.commit()
        cur.close()
        conn.close()
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")

def update_card(card_id, name, card_number, collection_total, language, condition, grading_note, owned):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE cards SET name = %s, card_number = %s, collection_total = %s, language = %s, condition = %s, grading_note = %s, owned = %s WHERE id = %s",
            (name, card_number, collection_total, language, condition, grading_note, owned, card_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        st.success("Card atualizado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")

# --- Título da Página ---
st.title(f"Cards da Lista: {list_name}")
# Voltar para a página principal de gerenciamento (app.py)
st.page_link("app.py", label="Voltar para todas as listas", icon="⬅️")
st.divider()

# --- Exibição dos Cards ---
cards = get_cards_for_list(list_id)

@st.dialog("Imagem do Card")
def show_card_image(image_url, card_name):
    st.image(image_url, caption=card_name, width="stretch")

@st.dialog("Editar Card")
def edit_card_dialog(card_data):
    card_id, name, _, number, total, lang, _, grading_note, condition, owned = card_data
    
    with st.form(key=f"edit_form_{card_id}"):
        st.write("Atenção: a imagem do card não pode ser alterada.")
        
        new_name = st.text_input("Nome do Card", value=name)
        
        c1, c2 = st.columns(2)
        new_card_number = c1.text_input("Número do Card", value=number)
        new_collection_total = c2.text_input("Total da Coleção (Opcional)", value=total)
        
        c3, c4 = st.columns(2)
        new_language = c3.selectbox("Linguagem", options=LANGUAGES, index=LANGUAGES.index(lang) if lang in LANGUAGES else 0)
        new_condition = c4.selectbox(
            "Condição",
            options=['GM', 'M', 'NM', 'SP', 'MP', 'HP', 'D'],
            index=['GM', 'M', 'NM', 'SP', 'MP', 'HP', 'D'].index(condition)
        )
        
        new_grading_note = st.number_input("Nota da Graduação (Opcional)", min_value=1, max_value=10, step=1, value=grading_note)
        
        new_owned = st.checkbox("Tenho este card", value=owned)

        if st.form_submit_button("Salvar Alterações"):
            update_card(card_id, new_name, new_card_number, new_collection_total, new_language, new_condition, new_grading_note, new_owned)
            st.rerun()

if not cards:
    st.info("Nenhum card nesta lista ainda. Adicione um abaixo.")
else:
    for i, card in enumerate(cards):
        card_id, name, photo_url, number, total, lang, order, grading_note, condition, owned = card
        
        # Deixa a coluna da imagem mais larga para telas menores
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(photo_url, width=360)
            if st.button("🔍 Ampliar", key=f"zoom_{card_id}"):
                show_card_image(photo_url, name)
        
        with col2:
            st.subheader(name)
            if total:
                st.write(f"**Número:** {number}/{total}")
            else:
                st.write(f"**Número:** {number}")
            st.write(f"**Linguagem:** {lang}")
            st.write(f"**Condição:** {condition}")
            if grading_note:
                st.write(f"**Nota:** {grading_note}")

            status_text = "Na coleção" if owned else "Desejo"
            st.write(f"**Status:** {status_text}")

            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Mudar Status", key=f"toggle_{card_id}"):
                    toggle_owned_status(card_id, owned)
            with action_col2:
                if st.button("Editar", key=f"edit_{card_id}"):
                    edit_card_dialog(card)
            
            # Botões de Reordenação
            reorder_col1, reorder_col2, reorder_col3 = st.columns(3)
            with reorder_col1:
                if i > 0: # Se não for o primeiro item
                    if st.button("⬆️ Para Cima", key=f"up_{card_id}"):
                        prev_card = cards[i-1]
                        swap_card_order(card_id, order, prev_card[0], prev_card[6])
            with reorder_col2:
                if i < len(cards) - 1: # Se não for o último item
                    if st.button("⬇️ Para Baixo", key=f"down_{card_id}"):
                        next_card = cards[i+1]
                        swap_card_order(card_id, order, next_card[0], next_card[6])
        st.markdown("---")

# --- Formulário para Adicionar Novo Card à Lista ---
with st.expander("Adicionar Novo Card à Lista"):
    with st.form(key="add_card_form", clear_on_submit=True):
        card_name = st.text_input("Nome do Card")
        uploaded_file = st.file_uploader("Foto do Card", type=["png", "jpg", "jpeg"])
        
        c1, c2 = st.columns(2)
        card_number = c1.text_input("Número do Card")
        collection_total = c2.text_input("Total da Coleção (Opcional)")
        
        c3, c4 = st.columns(2)
        language = c3.selectbox("Linguagem", options=LANGUAGES)
        condition = c4.selectbox("Condição", options=['GM', 'M', 'NM', 'SP', 'MP', 'HP', 'D'])
        
        grading_note = st.number_input("Nota da Graduação (Opcional)", min_value=1, max_value=10, step=1, value=None)
        
        owned = st.checkbox("Tenho este card", value=True)

        submitted = st.form_submit_button("Adicionar Card")
        if submitted:
            if uploaded_file and card_name and card_number:
                try:
                    upload_result = cloudinary.uploader.upload(uploaded_file)
                    photo_url = upload_result['secure_url']
                    
                    conn = get_db_connection()
                    cur = conn.cursor()
                    # Insere o card com a próxima ordem disponível
                    cur.execute(
                        "INSERT INTO cards (name, photo_url, card_number, collection_total, language, list_id, card_order, condition, grading_note, owned) VALUES (%s, %s, %s, %s, %s, %s, (SELECT COALESCE(MAX(card_order), 0) + 1 FROM cards WHERE list_id = %s), %s, %s, %s)",
                        (card_name, photo_url, card_number, collection_total, language, list_id, list_id, condition, grading_note, owned)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f'Card "{card_name}" adicionado!')
                    st.rerun()
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")
            else:
                st.warning("Por favor, preencha todos os campos obrigatórios e envie uma imagem.")
