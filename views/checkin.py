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
    cursor.execute("SELECT * FROM books WHERE isbn=%s LIMIT 1", (isbn,))
    book = cursor.fetchone()

    if not book:
        st.info("This ISBN is not in the database.")
        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    book_id = book["book_id"]

    # Check if there is an active loan
    cursor.execute("""
        SELECT c.checkout_id, r.first_name, r.last_name, b.title, b.cpy
        FROM checkouts c
        JOIN readers r ON c.reader_id = r.reader_id
        JOIN books b ON c.book_id = b.book_id
        WHERE b.isbn=%s AND c.return_date IS NULL
    """, (isbn,))

    loans = cursor.fetchall()

    if not loans:
        st.info("No active loan for this book.")
        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    # If multiple copies exist, let the user choose
    if len(loans) > 1:
        st.warning("Multiple copies of this book are currently checked out.")

        options = {
            f"Copy {loan['cpy']} — borrowed by {loan['first_name']} {loan['last_name']}":
            loan["checkout_id"]
            for loan in loans
        }

        choice = st.selectbox("Select which copy is being returned:", list(options.keys()))
        selected_checkout_id = options[choice]

    else:
        # Only one active loan
        loan = loans[0]
        st.success(f"{loan['title']} is borrowed by {loan['first_name']} {loan['last_name']}.")
        selected_checkout_id = loan["checkout_id"]


    if st.button("Check in"):
        cursor.execute("""
            UPDATE checkouts SET return_date=CURDATE()
            WHERE checkout_id=%s
        """, (selected_checkout_id,))
        conn.commit()
        st.success("Book checked in!")


    if st.button("🏠 Back to Home"):
        reset_checkout()