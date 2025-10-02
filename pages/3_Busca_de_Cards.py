import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv

# --- Configuração Inicial e Funções de DB ---
load_dotenv()

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# --- Título da Página ---
st.title("Busca de Cards na Coleção")
st.write("Procure por um card para ver se você já o possui em alguma de suas listas.")

# --- Lógica de Busca ---
search_term = st.text_input("Digite o nome do card que você está procurando:", "")

if search_term:
    @st.dialog("Imagem do Card")
    def show_card_image(image_url, card_name):
        st.image(image_url, caption=card_name)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # A busca será case-insensitive com o uso de ILIKE
        query = """
            SELECT c.name, c.photo_url, c.card_number, c.collection_total, c.language, l.name, c.id, c.grading_note, c.condition, c.owned
            FROM cards c
            JOIN lists l ON c.list_id = l.id
            WHERE c.name ILIKE %s
            ORDER BY l.name, c.name;
        """
        cur.execute(query, (f'%{search_term}%',))
        
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        if not results:
            st.info(f'Nenhum card encontrado com o nome "{search_term}".')
        else:
            st.success(f'{len(results)} card(s) encontrado(s) com o nome "{search_term}":')
            
            for card in results:
                card_name, photo_url, number, total, lang, list_name, card_id, grading_note, condition, owned = card
                
                st.divider()
                col1, col2 = st.columns([0.5, 3.5])
                
                with col1:
                    st.image(photo_url, use_container_width=True)
                    if st.button("🔍 Ampliar", key=f"zoom_{card_id}"):
                        show_card_image(photo_url, card_name)
                
                with col2:
                    st.subheader(card_name)
                    st.write(f"**Lista:** {list_name}")
                    st.write(f"**Número:** {number}/{total}")
                    st.write(f"**Linguagem:** {lang}")
                    st.write(f"**Condição:** {condition}")
                    if grading_note:
                        st.write(f"**Nota:** {grading_note}")
                    status_text = "Na coleção" if owned else "Desejo"
                    st.write(f"**Status:** {status_text}")

    except Exception as e:
        st.error(f"Erro ao buscar os cards: {e}")
