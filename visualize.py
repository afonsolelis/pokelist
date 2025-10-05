import os
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# Visualização somente-leitura das listas e cards (100% Streamlit)

load_dotenv()
st.set_page_config(page_title="Pokélist - Visualização", layout="wide", initial_sidebar_state="collapsed")


def get_db_connection_readonly():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        conn.set_session(readonly=True, autocommit=True)
    except Exception:
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

def get_all_languages():
    try:
        conn = get_db_connection_readonly()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT language FROM cards WHERE language IS NOT NULL AND language <> '' ORDER BY language ASC")
        langs = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return langs
    except Exception:
        return []

def search_cards(name_term: str | None, language: str | None, status: str | None, condition: str | None, min_note: int | None, max_note: int | None, sort: str = "name"):
    # Retorna: name, photo_url, number, total, lang, list_name, card_id, grading_note, condition, owned
    sql = [
        """
        SELECT c.name, c.photo_url, c.card_number, c.collection_total, c.language,
               l.name as list_name, c.id, c.grading_note, c.condition, c.owned
        FROM cards c
        JOIN lists l ON c.list_id = l.id
        WHERE 1=1
        """
    ]
    params: list = []
    if name_term:
        sql.append("AND c.name ILIKE %s")
        params.append(f"%{name_term}%")
    if language:
        sql.append("AND c.language = %s")
        params.append(language)
    if status == "owned":
        sql.append("AND c.owned = TRUE")
    elif status == "wish":
        sql.append("AND (c.owned = FALSE OR c.owned IS NULL)")
    if condition:
        sql.append("AND c.condition = %s")
        params.append(condition)
    if min_note is not None:
        sql.append("AND c.grading_note >= %s")
        params.append(min_note)
    if max_note is not None:
        sql.append("AND c.grading_note <= %s")
        params.append(max_note)

    order = "l.name, c.name"
    if sort == "grade_desc":
        order = "c.grading_note DESC NULLS LAST, l.name, c.name"
    elif sort == "name":
        order = "l.name, c.name"
    elif sort == "number":
        order = "l.name, c.card_number, c.name"

    sql.append(f"ORDER BY {order}")

    try:
        conn = get_db_connection_readonly()
        cur = conn.cursor()
        cur.execute("\n".join(sql), tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return []


# Esconde a navegação padrão da pasta pages
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _normalize_cloudinary(url: str, width: int = 900, height: int | None = 1200) -> str:
    if not url or "res.cloudinary.com" not in url or "/image/upload" not in url:
        return url
    try:
        before, after = url.split("/image/upload/", 1)
        first_segment = after.split("/", 1)[0]
        if any(token in first_segment for token in ("w_", "h_", "c_", "q_", "f_", "ar_")):
            return url
        if height is None:
            transform = f"f_auto,q_auto,c_limit,w_{width}"
        else:
            transform = f"f_auto,q_auto,c_pad,b_white,w_{width},h_{height}"
        return f"{before}/image/upload/{transform}/{after}"
    except Exception:
        return url


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
                    st.subheader(list_name)
                    st.caption(f"{total_cards} card(s)")
                    if st.button("Abrir", key=f"open_list_{list_id}"):
                        st.session_state["visualize_selected_list_id"] = list_id
                        st.session_state["visualize_selected_list_name"] = list_name
                        st.rerun()


def show_list_detail_view(list_id: int, list_name: str):
    st.title(f"{list_name}")
    st.caption("Visualização somente-leitura.")

    if st.button("⬅️ Voltar"):
        st.session_state.pop("visualize_selected_list_id", None)
        st.session_state.pop("visualize_selected_list_name", None)
        st.rerun()

    cards = get_cards_for_list(list_id)
    if not cards:
        st.info("Esta lista não possui cards.")
        return

    st.write(f"Total: {len(cards)} cards")

    cols_per_row = 4
    for i in range(0, len(cards), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col in enumerate(cols):
            if i + idx >= len(cards):
                break
            card_id, name, photo_url, number, total, lang, order, grading_note, condition, owned = cards[i + idx]
            with col:
                with st.container(border=True):
                    img_url = _normalize_cloudinary(photo_url, width=900, height=1200)
                    st.image(img_url, use_container_width=True)
                    st.write(f"**{name}**")
                    meta = []
                    if number:
                        meta.append(f"# {number}{'/' + str(total) if total else ''}")
                    if lang:
                        meta.append(lang)
                    if meta:
                        st.markdown(
                            f"<div style='font-size:0.80rem;color:#475569;'>{' • '.join(meta)}</div>",
                            unsafe_allow_html=True,
                        )
                    info = []
                    if condition:
                        info.append(f"Cond.: {condition}")
                    if grading_note:
                        info.append(f"Nota: {grading_note}")
                    if owned is not None:
                        info.append('Na coleção' if owned else 'Desejo')
                    if info:
                        st.markdown(
                            f"<div style='font-size:0.78rem;color:#5b6778;'>" + " | ".join(info) + "</div>",
                            unsafe_allow_html=True,
                        )


# --- Roteamento simples por sessão ---
tab_listas, tab_busca = st.tabs(["Listas", "Buscar"])

with tab_listas:
    selected_id = st.session_state.get("visualize_selected_list_id")
    selected_name = st.session_state.get("visualize_selected_list_name")
    if selected_id and selected_name:
        show_list_detail_view(selected_id, selected_name)
    else:
        show_lists_view()

with tab_busca:
    st.title("Busca de Cards")
    st.caption("Filtre por nome, língua, condição, status e nota.")

    with st.form("search_form", clear_on_submit=False):
        name_term = st.text_input("Nome contém", "")
        cols = st.columns(3)
        with cols[0]:
            langs = [""] + get_all_languages()
            language = st.selectbox("Língua", options=langs, format_func=lambda v: v if v else "Todas")
        with cols[1]:
            status_map = {"Todos": "", "Na coleção": "owned", "Desejo": "wish"}
            status_label = st.selectbox("Status", options=list(status_map.keys()))
            status = status_map[status_label]
        with cols[2]:
            condition = st.selectbox("Condição", options=["", "GM", "M", "NM", "SP", "MP", "HP", "D"], format_func=lambda v: v if v else "Todas")

        cols2 = st.columns(3)
        with cols2[0]:
            sort_label = st.selectbox("Ordenar por", options=["Nome", "Número", "Nota (desc)"])
            sort = {"Nome": "name", "Número": "number", "Nota (desc)": "grade_desc"}[sort_label]
        with cols2[1]:
            min_note = st.number_input("Nota mínima", min_value=1, max_value=10, value=1)
        with cols2[2]:
            max_note = st.number_input("Nota máxima", min_value=1, max_value=10, value=10)

        submitted = st.form_submit_button("Buscar")

    if submitted:
        results = search_cards(
            name_term=name_term or None,
            language=language or None,
            status=status or None,
            condition=condition or None,
            min_note=min_note if min_note else None,
            max_note=max_note if max_note else None,
            sort=sort,
        )

        if not results:
            st.info("Nenhum card encontrado com os filtros informados.")
        else:
            st.success(f"{len(results)} card(s) encontrado(s)")
            cols_per_row = 4
            for i in range(0, len(results), cols_per_row):
                cols = st.columns(cols_per_row)
                for idx, col in enumerate(cols):
                    if i + idx >= len(results):
                        break
                    card_name, photo_url, number, total, lang, list_name, card_id, grading_note, condition, owned = results[i + idx]
                    with col:
                        with st.container(border=True):
                            img_url = _normalize_cloudinary(photo_url, width=900, height=1200)
                            st.image(img_url, use_container_width=True)
                            st.write(f"**{card_name}**")
                            st.caption(f"Lista: {list_name}")
                            meta = []
                            if number:
                                meta.append(f"# {number}{'/' + str(total) if total else ''}")
                            if lang:
                                meta.append(lang)
                            if meta:
                                st.markdown(
                                    f"<div style='font-size:0.80rem;color:#475569;'>{' • '.join(meta)}</div>",
                                    unsafe_allow_html=True,
                                )
                            info = []
                            if condition:
                                info.append(f"Cond.: {condition}")
                            if grading_note:
                                info.append(f"Nota: {grading_note}")
                            if owned is not None:
                                info.append('Na coleção' if owned else 'Desejo')
                            if info:
                                st.markdown(
                                    f"<div style='font-size:0.78rem;color:#5b6778;'>" + " | ".join(info) + "</div>",
                                    unsafe_allow_html=True,
                                )
                            if st.button("Abrir lista", key=f"go_{card_id}"):
                                # Buscar o ID da lista e navegar para a aba de Listas > Detalhe
                                try:
                                    conn = get_db_connection_readonly()
                                    cur = conn.cursor()
                                    cur.execute("SELECT id FROM lists WHERE name = %s LIMIT 1", (list_name,))
                                    row = cur.fetchone()
                                    cur.close()
                                    conn.close()
                                    if row:
                                        st.session_state["visualize_selected_list_id"] = row[0]
                                        st.session_state["visualize_selected_list_name"] = list_name
                                        st.rerun()
                                except Exception:
                                    st.warning("Não foi possível abrir a lista.")
