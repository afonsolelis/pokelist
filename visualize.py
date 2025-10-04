import os
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# Visualização somente-leitura das listas e cards

load_dotenv()
st.set_page_config(page_title="Pokélist - Visualização", layout="wide")


def get_db_connection_readonly():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    # Garante transações somente-leitura e sem commits
    try:
        conn.set_session(readonly=True, autocommit=True)
    except Exception:
        # Fallback para garantir o modo somente-leitura via comando SQL
        with conn.cursor() as cur:
            cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
    return conn


def get_lists_with_counts():
    conn = get_db_connection_readonly()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.id, l.name, COUNT(c.id) AS total_cards
        FROM lists l
        LEFT JOIN cards c ON c.list_id = l.id
        GROUP BY l.id, l.name
        ORDER BY l.name ASC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_cards_for_list(list_id: int):
    conn = get_db_connection_readonly()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, photo_url, card_number, collection_total, language,
               card_order, grading_note, condition, owned
        FROM cards
        WHERE list_id = %s
        ORDER BY card_order ASC
        """,
        (list_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# --- Estilos ---
st.markdown(
    """
    <style>
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
    .list-card, .poke-card {
        border-radius: 12px; border: 1px solid #e6e6e6; padding: 14px; background: #fff;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }
    .list-card:hover, .poke-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
    .list-title { font-weight: 600; font-size: 1rem; margin: 6px 0 2px; }
    .list-sub { color: #666; font-size: 0.9rem; }
    .poke-card img { width: 100%; height: auto; border-radius: 8px; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.8rem; background: #f1f5f9; color: #0f172a; margin-right: 6px; }
    .meta { color: #475569; font-size: 0.9rem; }
    .name { font-weight: 700; margin: 8px 0 4px; font-size: 1.05rem; }
    .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_lists_view():
    st.title("Listas Públicas")
    st.caption("Selecione uma lista para visualizar os cards.")

    lists = get_lists_with_counts()
    if not lists:
        st.info("Nenhuma lista encontrada.")
        return

    cols_per_row = 4
    for i in range(0, len(lists), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            if i + idx >= len(lists):
                break
            list_id, list_name, total_cards = lists[i + idx]
            with col:
                with st.container(border=True):
                    st.markdown(
                        f"<div class='list-card'>"
                        f"<div class='list-title'>{list_name}</div>"
                        f"<div class='list-sub'>{total_cards} card(s)</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("Abrir", key=f"open_list_{list_id}"):
                        st.session_state["visualize_selected_list_id"] = list_id
                        st.session_state["visualize_selected_list_name"] = list_name
                        st.rerun()


def show_list_detail_view(list_id: int, list_name: str):
    st.title(f"{list_name}")
    st.caption("Visualização somente-leitura.")
    st.button("⬅️ Voltar", on_click=lambda: [st.session_state.pop("visualize_selected_list_id", None), st.session_state.pop("visualize_selected_list_name", None), st.rerun()])

    cards = get_cards_for_list(list_id)
    if not cards:
        st.info("Esta lista não possui cards.")
        return

    # Barra superior com contagem
    st.markdown(
        f"<div class='topbar'><div class='meta'>Total: {len(cards)} cards</div></div>",
        unsafe_allow_html=True,
    )

    # Grade de cards
    cols_per_row = 3
    for i in range(0, len(cards), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            if i + idx >= len(cards):
                break
            card = cards[i + idx]
            card_id, name, photo_url, number, total, lang, order, grading_note, condition, owned = card
            with col:
                with st.container(border=True):
                    st.markdown("<div class='poke-card'>", unsafe_allow_html=True)
                    st.image(photo_url, use_container_width=True)
                    st.markdown(f"<div class='name'>{name}</div>", unsafe_allow_html=True)

                    # Metadados em linha
                    meta_parts = []
                    if number:
                        meta_parts.append(f"# {number}{'/' + str(total) if total else ''}")
                    if lang:
                        meta_parts.append(lang)
                    st.markdown(
                        f"<div class='meta'>{' • '.join(meta_parts)}</div>",
                        unsafe_allow_html=True,
                    )

                    # Pills
                    pills = []
                    if condition:
                        pills.append(f"<span class='pill'>Cond.: {condition}</span>")
                    if grading_note:
                        pills.append(f"<span class='pill'>Nota: {grading_note}</span>")
                    if owned is not None:
                        pills.append(f"<span class='pill'>{'Na coleção' if owned else 'Desejo'}</span>")
                    if pills:
                        st.markdown(" ".join(pills), unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)


# --- Roteamento simples por sessão ---
selected_id = st.session_state.get("visualize_selected_list_id")
selected_name = st.session_state.get("visualize_selected_list_name")

if selected_id and selected_name:
    show_list_detail_view(selected_id, selected_name)
else:
    show_lists_view()

