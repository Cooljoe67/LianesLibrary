import streamlit as st
from utils.db import get_connection
from utils.metadata import lookup_book_metadata
from utils.state import reset_checkout, ensure_isbn_widget_key


def _refresh_isbn_input_key():
    current_key = st.session_state.get("isbn_widget_key")
    if current_key in st.session_state:
        del st.session_state[current_key]

    next_counter = st.session_state.get("reset_counter", 0) + 1
    st.session_state["reset_counter"] = next_counter
    st.session_state["isbn_widget_key"] = f"isbn_{next_counter}"


def _return_home_if_clicked():
    if st.button("🏠 Back to Home"):
        reset_checkout()


def _continue_checkout_for_reader(reader_id):
    st.session_state["active_reader_id"] = reader_id
    _refresh_isbn_input_key()
    st.session_state["page"] = "📘 Checkout"
    st.rerun()


def _select_reader(cursor, conn):
    reader = None

    if "show_add_reader_form" not in st.session_state:
        st.session_state["show_add_reader_form"] = False

    if "active_reader_id" in st.session_state:
        read_cursor = conn.cursor(dictionary=True)
        read_cursor.execute("SELECT * FROM readers WHERE reader_id=%s", (st.session_state["active_reader_id"],))
        reader = read_cursor.fetchone()
        read_cursor.fetchall()  # Consume remaining results
        read_cursor.close()
        if reader:
            st.success(f"Selected reader: {reader['first_name']} {reader['last_name']}")
        else:
            del st.session_state["active_reader_id"]

    if reader is None:
        st.caption("Enter part of the reader's name:")
        search_col, add_col = st.columns([5, 1])
        with search_col:
            name = st.text_input(
                "Enter part of the reader's name:",
                label_visibility="collapsed",
                placeholder="Type first or last name",
            )
        with add_col:
            if st.button("Add", key="add_reader_button"):
                st.session_state["show_add_reader_form"] = True

        if st.session_state.get("show_add_reader_form"):
            with st.form("add_reader_form"):
                st.markdown("**Add New Reader**")
                first_name = st.text_input("First name")
                last_name = st.text_input("Last name")
                phone = st.text_input("Phone number")
                email = st.text_input("Email address")

                submit_col, cancel_col = st.columns(2)
                submitted = submit_col.form_submit_button("Submit")
                canceled = cancel_col.form_submit_button("Cancel")

            if canceled:
                st.session_state["show_add_reader_form"] = False
                st.rerun()

            if submitted:
                if not first_name.strip() or not last_name.strip():
                    st.warning("First name and last name are required.")
                else:
                    fresh_conn = get_connection()
                    write_cursor = fresh_conn.cursor()
                    write_cursor.execute(
                        """
                        INSERT INTO readers (last_name, first_name, email, phone)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (last_name.strip(), first_name.strip(), email.strip() or None, phone.strip() or None),
                    )
                    fresh_conn.commit()
                    st.session_state["active_reader_id"] = write_cursor.lastrowid
                    write_cursor.close()
                    fresh_conn.close()
                    st.session_state["show_add_reader_form"] = False
                    st.success("Reader added and selected.")
                    st.rerun()

        search_cursor = conn.cursor(dictionary=True)
        search_cursor.execute(
            """
            SELECT * FROM readers
            WHERE first_name LIKE %s OR last_name LIKE %s
            """,
            (f"%{name}%", f"%{name}%"),
        )
        readers = search_cursor.fetchall()
        search_cursor.close()

        if readers:
            reader = st.selectbox(
                "Choose reader:",
                readers,
                format_func=lambda r: f"{r['first_name']} {r['last_name']}",
            )
        else:
            st.info("No matching reader found.")

    return reader


def render():
    st.header("📘 Book Checkout")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Reader selection
    st.subheader("1. Select Reader")

    reader = _select_reader(cursor, conn)

    if not reader:
        _return_home_if_clicked()
        st.stop()

    # Step 2: ISBN
    st.subheader("2. Scan ISBN")

    ensure_isbn_widget_key()

    if st.session_state.pop("checkout_just_completed", False):
        st.success("Book checked out! Scan the next ISBN.")

    isbn = st.text_input("Scan or enter ISBN:", key=st.session_state["isbn_widget_key"])

    if not isbn:
        _return_home_if_clicked()
        st.stop()

    cursor.execute(
        """
        SELECT b.book_id, b.isbn, b.title, b.author, b.cpy,
               c.checkout_id, r.first_name AS loan_first_name, r.last_name AS loan_last_name
        FROM books b
        LEFT JOIN checkouts c ON c.book_id = b.book_id AND c.return_date IS NULL
        LEFT JOIN readers r ON r.reader_id = c.reader_id
        WHERE b.isbn = %s
        ORDER BY b.cpy
        """,
        (isbn,),
    )
    copies = cursor.fetchall()
    cursor.close()

    book = next((copy for copy in copies if copy["checkout_id"] is None), None)

    # Book not in DB
    if not copies:
        st.warning("This book is not in the database yet.")

        meta = lookup_book_metadata(isbn)
        if meta:
            title, author = meta
            st.success(f"Found: {title} — {author}")
        else:
            title = st.text_input("Title")
            author = st.text_input("Author")

        if st.button("Add book to database"):
            fresh_conn = get_connection()
            write_cursor = fresh_conn.cursor()
            write_cursor.execute("""
                INSERT INTO books (isbn, title, author)
                VALUES (%s, %s, %s)
            """, (isbn, title, author))
            fresh_conn.commit()
            write_cursor.close()
            fresh_conn.close()

            st.success("Book added!")

            if st.button("📘 Continue checkout for this reader"):
                _continue_checkout_for_reader(reader["reader_id"])

        _return_home_if_clicked()
        st.stop()

    # Book exists → find free copy or show all-on-loan state
    if book is None:
        loaned_copies = [copy for copy in copies if copy["checkout_id"] is not None]
        loaned_copy = loaned_copies[0]
        st.error(
            f"All copies are currently on loan. Example: copy {loaned_copy['cpy']} is with "
            f"{loaned_copy['loan_first_name']} {loaned_copy['loan_last_name']}."
        )

        selected_loan = loaned_copy
        if len(loaned_copies) > 1:
            selected_loan = st.selectbox(
                "Select copy to force check-in:",
                loaned_copies,
                format_func=lambda copy: (
                    f"Copy {copy['cpy']} - {copy['loan_first_name']} {copy['loan_last_name']}"
                ),
                key="force_checkin_copy_select",
            )

        if st.button("📦 I have another copy"):
            fresh_conn = get_connection()
            write_cursor = fresh_conn.cursor()
            write_cursor.execute(
                """
                INSERT INTO books (isbn, title, author, cpy)
                SELECT b.isbn, b.title, b.author,
                       (SELECT COALESCE(MAX(cpy), 0) + 1 FROM books WHERE isbn=%s)
                FROM books b
                WHERE b.isbn=%s
                ORDER BY b.cpy DESC
                LIMIT 1
                """,
                (isbn, isbn),
            )
            fresh_conn.commit()
            write_cursor.close()
            fresh_conn.close()
            st.success("New copy added to library!")
            _refresh_isbn_input_key()
            st.rerun()

        if st.button("📄 Force check-in"):
            fresh_conn = get_connection()
            write_cursor = fresh_conn.cursor()
            write_cursor.execute("""
                UPDATE checkouts SET return_date=CURDATE()
                WHERE checkout_id=%s
            """, (selected_loan["checkout_id"],))
            fresh_conn.commit()
            write_cursor.close()
            fresh_conn.close()
            _refresh_isbn_input_key()
            st.rerun()

        _return_home_if_clicked()
        st.stop()

    # Book available → checkout
    book_id = book["book_id"]
    st.success(f"Book available: {book['title']} — {book['author']}")

    due = st.date_input("Due date (optional)", value=None)

    if st.button("Check out"):
        fresh_conn = get_connection()
        write_cursor = fresh_conn.cursor()
        write_cursor.execute("""
            INSERT INTO checkouts (book_id, reader_id, loan_date, due_date)
            VALUES (%s, %s, CURDATE(), %s)
        """, (book_id, reader["reader_id"], due))
        fresh_conn.commit()
        write_cursor.close()
        fresh_conn.close()

        st.session_state["checkout_just_completed"] = True
        _continue_checkout_for_reader(reader["reader_id"])


    _return_home_if_clicked()