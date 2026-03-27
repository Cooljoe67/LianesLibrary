import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="Liane",
        password="LibPass2025!",
        database="LianesLibrary"
    )