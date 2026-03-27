import streamlit as st
from utils.db import get_connection
from utils.metadata import lookup_book_metadata
from utils.state import reset_checkout, ensure_isbn_widget_key

def render():
    st.header("📘 Book Checkout")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Reader selection
    st.subheader("1. Select Reader")

    reader = None

    if "active_reader_id" in st.session_state:
        cursor.execute("SELECT * FROM readers WHERE reader_id=%s", (st.session_state["active_reader_id"],))
        reader = cursor.fetchone()
        if reader:
            st.success(f"Selected reader: {reader['first_name']} {reader['last_name']}")
        else:
            del st.session_state["active_reader_id"]

    if reader is None:
        name = st.text_input("Enter part of the reader's name:")
        cursor.execute("""
            SELECT * FROM readers
            WHERE first_name LIKE %s OR last_name LIKE %s
        """, (f"%{name}%", f"%{name}%"))
        readers = cursor.fetchall()

        if readers:
            reader = st.selectbox(
                "Choose reader:",
                readers,
                format_func=lambda r: f"{r['first_name']} {r['last_name']}"
            )
        else:
            st.info("No matching reader found.")

    if not reader:
        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    # Step 2: ISBN
    st.subheader("2. Scan ISBN")

    ensure_isbn_widget_key()
    isbn = st.text_input("Scan or enter ISBN:", key=st.session_state["isbn_widget_key"])

    if not isbn:
        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    cursor.execute("SELECT * FROM books WHERE isbn=%s", (isbn,))
    book = cursor.fetchone()

    # Book not in DB
    if not book:
        st.warning("This book is not in the database yet.")

        meta = lookup_book_metadata(isbn)
        if meta:
            title, author = meta
            st.success(f"Found: {title} — {author}")
        else:
            title = st.text_input("Title")
            author = st.text_input("Author")

        if st.button("Add book to database"):
            cursor.execute("""
                INSERT INTO books (isbn, title, author)
                VALUES (%s, %s, %s)
            """, (isbn, title, author))
            conn.commit()

            st.success("Book added!")

            if st.button("📘 Continue checkout for this reader"):
                st.session_state["active_reader_id"] = reader["reader_id"]
                st.session_state["isbn_widget_key"] = f"isbn_{st.session_state.get('reset_counter', 0)}"
                st.session_state["reset_counter"] += 1
                st.session_state["page"] = "📘 Checkout"
                st.rerun()

        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    # Book exists → check loan
    book_id = book["book_id"]

    cursor.execute("""
        SELECT c.checkout_id, r.first_name, r.last_name
        FROM checkouts c
        JOIN readers r ON c.reader_id = r.reader_id
        WHERE c.book_id=%s AND c.return_date IS NULL
    """, (book_id,))
    loan = cursor.fetchone()

    if loan:
        st.error(f"This book is currently on loan to {loan['first_name']} {loan['last_name']}.")

        if st.button("📦 I have another copy"):
            cursor.execute("UPDATE books SET cpy = cpy + 1 WHERE book_id=%s", (book_id,))
            conn.commit()
            st.session_state["isbn_widget_key"] = f"isbn_{st.session_state.get('reset_counter', 0)}"
            st.session_state["reset_counter"] += 1
            st.rerun()

        if st.button("📄 Force check-in"):
            cursor.execute("""
                UPDATE checkouts SET return_date=CURDATE()
                WHERE checkout_id=%s
            """, (loan["checkout_id"],))
            conn.commit()
            st.session_state["isbn_widget_key"] = f"isbn_{st.session_state.get('reset_counter', 0)}"
            st.session_state["reset_counter"] += 1
            st.rerun()

        if st.button("🏠 Back to Home"):
            reset_checkout()
        st.stop()

    # Book available → checkout
    st.success(f"Book available: {book['title']} — {book['author']}")

    due = st.date_input("Due date (optional)", value=None)

    if st.button("Check out"):
        cursor.execute("""
            INSERT INTO checkouts (book_id, reader_id, loan_date, due_date)
            VALUES (%s, %s, CURDATE(), %s)
        """, (book_id, reader["reader_id"], due))
        conn.commit()

        st.success("Book checked out!")

        if st.button("📘 Check out another book"):
            st.session_state["active_reader_id"] = reader["reader_id"]
            st.session_state["isbn_widget_key"] = f"isbn_{st.session_state.get('reset_counter', 0)}"
            st.session_state["reset_counter"] += 1
            st.session_state["page"] = "📘 Checkout"
            st.rerun()

    if st.button("🏠 Back to Home"):
        reset_checkout()