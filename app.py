import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv

# --- Configuração Inicial e Funções de DB ---
load_dotenv()
st.set_page_config(layout="wide")

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# --- Funções da Página ---
def handle_list_rename(list_id, new_name):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE lists SET name = %s WHERE id = %s", (new_name, list_id))
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"Lista renomeada para '{new_name}'!")
        del st.session_state[f'rename_{list_id}'] # Fecha o campo de renomear
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao renomear: {e}")

def handle_list_delete(list_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM lists WHERE id = %s", (list_id,))
        conn.commit()
        cur.close()
        conn.close()
        st.success("Lista deletada com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")

# --- Título da Página ---
st.title("Gerenciador de Listas de Cards Pokémon")
st.write("Crie novas listas ou gerencie as existentes.")

# --- Formulário para Criar Nova Lista ---
with st.expander("Adicionar Nova Lista", expanded=False):
    with st.form("new_list_form", clear_on_submit=True):
        new_list_name = st.text_input("Nome da nova lista")
        submitted = st.form_submit_button("Criar Lista")
        if submitted and new_list_name:
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO lists (name) VALUES (%s)", (new_list_name,))
                conn.commit()
                cur.close()
                conn.close()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao criar lista: {e}")

st.divider()

# --- Tabela de Listas Existentes ---
st.header("Minhas Listas")

all_lists = []
try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM lists ORDER BY name ASC")
    all_lists = cur.fetchall()
    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Não foi possível buscar as listas: {e}")

if not all_lists:
    st.info("Nenhuma lista encontrada. Crie uma no formulário acima.")
else:
    # Cabeçalho da "tabela"
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
    col1.write("**Nome da Lista**")
    col2.write("**Cards**")
    col3.write("**Renomear**")
    col4.write("**Deletar**")

    for list_id, list_name in all_lists:
        col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
        
        with col1:
            # Se o modo de renomear estiver ativo para esta lista
            if st.session_state.get(f'rename_{list_id}'):
                new_name = st.text_input("Novo nome", value=list_name, key=f"new_name_{list_id}")
                if st.button("Salvar", key=f"save_{list_id}"):
                    handle_list_rename(list_id, new_name)
            else:
                st.write(list_name)

        with col2:
            if st.button("Ver / Editar Cards", key=f"view_{list_id}"):
                st.session_state['current_list_id'] = list_id
                st.session_state['current_list_name'] = list_name
                st.switch_page("pages/2_Detalhes_da_Lista.py")

        with col3:
            if st.button("Renomear", key=f"rename_btn_{list_id}"):
                st.session_state[f'rename_{list_id}'] = True
                st.rerun()

        with col4:
            if st.button("Deletar", key=f"delete_{list_id}"):
                handle_list_delete(list_id)