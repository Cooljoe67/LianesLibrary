# pages/checkin.py

import streamlit as st
from utils.db import get_connection
from utils.state import reset_checkout

def render():
    st.header("📗 Book Check‑In")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # ISBN input for check-in
    isbn = st.text_input("Scan ISBN to check in:")

    if not isbn:
        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    # Look up book by ISBN
    cursor.execute("SELECT * FROM books WHERE isbn=%s", (isbn,))
    book = cursor.fetchone()

    if not book:
        st.info("This ISBN is not in the database.")
        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    book_id = book["book_id"]

    # Check if there is an active loan
    cursor.execute("""
        SELECT c.checkout_id, r.first_name, r.last_name, b.title
        FROM checkouts c
        JOIN readers r ON c.reader_id = r.reader_id
        JOIN books b ON c.book_id = b.book_id
        WHERE c.book_id=%s AND c.return_date IS NULL
    """, (book_id,))
    loan = cursor.fetchone()

    if not loan:
        st.info("No active loan for this book.")
        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    st.success(f"{loan['title']} is borrowed by {loan['first_name']} {loan['last_name']}.")

    if st.button("Check in"):
        cursor.execute("""
            UPDATE checkouts SET return_date=CURDATE()
            WHERE checkout_id=%s
        """, (loan["checkout_id"],))
        conn.commit()
        st.success("Book checked in!")

    if st.button("🏠 Back to Home"):
        reset_checkout()