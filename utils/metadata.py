import requests

def lookup_book_metadata(isbn):
    clean = isbn.replace("-", "").strip()
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean}"
    r = requests.get(url, timeout=5).json()

    if "items" not in r:
        return None

    info = r["items"][0]["volumeInfo"]

    title = info.get("title", "Unknown Title")
    authors = info.get("authors", ["Unknown Author"])

    return title, authors[0]
