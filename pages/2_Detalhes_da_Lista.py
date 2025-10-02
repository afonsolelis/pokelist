import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# --- Configuração e Funções de DB ---
load_dotenv()

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
    st.page_link("app.py", label="Voltar para o Gerenciador de Listas", icon="🏠")
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

# --- Título da Página ---
st.title(f"Cards da Lista: {list_name}")
st.page_link("app.py", label="Voltar para todas as listas", icon="⬅️")
st.divider()

# --- Exibição dos Cards ---
cards = get_cards_for_list(list_id)

@st.dialog("Imagem do Card")
def show_card_image(image_url, card_name):
    st.image(image_url, caption=card_name)

if not cards:
    st.info("Nenhum card nesta lista ainda. Adicione um abaixo.")
else:
    for i, card in enumerate(cards):
        card_id, name, photo_url, number, total, lang, order, grading_note, condition, owned = card
        
        col1, col2 = st.columns([0.5, 3.5])
        with col1:
            st.image(photo_url, use_container_width=True)
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

            if st.button("Mudar Status", key=f"toggle_{card_id}"):
                toggle_owned_status(card_id, owned)
            
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
        collection_total = c2.number_input("Total da Coleção (Opcional)", min_value=1, step=1, value=None)
        
        c3, c4 = st.columns(2)
        language = c3.selectbox("Linguagem", options=LANGUAGES)
        condition = c4.selectbox("Condição", options=['NM', 'SP', 'MP', 'HP', 'D'])
        
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
