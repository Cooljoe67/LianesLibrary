import streamlit as st
from utils.db import get_connection
import pandas as pd

def render():
    st.title("📈 Statistics")

    pd.set_option("mode.string_storage", "python")

    # --- INIT STATE ---
    if "view" not in st.session_state:
        st.session_state.view = "Readers"

    if "search" not in st.session_state:
        st.session_state.search = ""

    # --- VIEW BUTTONS ---
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👤 Readers"):
            st.session_state.view = "Readers"
            st.session_state.search = ""   # reset search on table change

    with col2:
        if st.button("📚 Books"):
            st.session_state.view = "Books"
            st.session_state.search = ""

    with col3:
        if st.button("🔄 Checkouts"):
            st.session_state.view = "Checkouts"
            st.session_state.search = ""

    # --- SEARCH BAR ---
    search_col, btn_search_col, btn_clear_col = st.columns([13, 1, 1])

    with search_col:
        search_text = st.text_input(
            "Search",
            value=st.session_state.search,
            placeholder="Type title, author, genre...",
            label_visibility="collapsed"
        )

    with btn_search_col:
        search_clicked = st.button("🔍")

    with btn_clear_col:
        clear_clicked = st.button("❌")

    # --- HANDLE SEARCH STATE ---
    if clear_clicked:
        st.session_state.search = ""
        search_text = ""

    # Update state when typing or clicking search
    if search_clicked or search_text != st.session_state.search:
        st.session_state.search = search_text.strip()

    # --- BUILD QUERY ---
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if st.session_state.search:
        # Use your generic stored procedure
        query = (
            f"CALL search_generic("
            f"'v_{st.session_state.view.lower()}', "
            f"'{st.session_state.search}'"
            f")"
        )
    else:
        # Load full table
        query = f"SELECT * FROM v_{st.session_state.view.lower()}"

    cursor.execute(query)
    rows = cursor.fetchall()

    df = pd.DataFrame(rows)

    st.subheader(f"📚 {st.session_state.view} Table")
    st.dataframe(df, use_container_width=True)

    cursor.close()
    conn.close()