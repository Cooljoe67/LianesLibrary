import streamlit as st

def reset_checkout():
    for key in list(st.session_state.keys()):
        if key not in ["page"]:
            del st.session_state[key]

    st.session_state["isbn_widget_key"] = f"isbn_{st.session_state.get('reset_counter', 0)}"
    st.session_state["reset_counter"] = st.session_state.get("reset_counter", 0) + 1

    st.session_state["page"] = "🏠 Home"
    st.rerun()

def ensure_isbn_widget_key():
    if "isbn_widget_key" not in st.session_state:
        st.session_state["isbn_widget_key"] = f"isbn_{st.session_state.get('reset_counter', 0)}"
        st.session_state["reset_counter"] = st.session_state.get("reset_counter", 0) + 1
        st.rerun()