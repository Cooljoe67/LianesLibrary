import streamlit as st
import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="Liane",
    password="LibPass2025!",
    database="lianeslibrary"  # optional
)

print("Connected to MySQL!")

connection.close()

st.write("hello world")
x = st.text_input("fafourisd movie???")
st.write("your movie:",x)