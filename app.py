import streamlit as st
from views import home, checkout, checkin

PAGES = {
    "🏠 Home": home,
    "📘 Checkout": checkout,
    "📗 Check‑In": checkin,
}

if "page" not in st.session_state:
    st.session_state["page"] = "🏠 Home"

page = st.sidebar.radio("Navigation", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state["page"]))
st.session_state["page"] = page

PAGES[page].render()