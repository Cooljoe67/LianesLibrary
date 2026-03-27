import requests

def lookup_book_metadata(isbn):
    try:
        clean = isbn.replace("-", "").strip()
        url = f"https://openlibrary.org/isbn/{clean}.json"
        r = requests.get(url)
        if r.status_code != 200:
            return None

        data = r.json()
        title = data.get("title", "Unknown Title")
        author = "Unknown Author"

        if "author" in data and isinstance(data["author"], list) and data["author"]:
            author = data["author"][0]
        elif "by_statement" in data:
            author = data["by_statement"]
        elif "authors" in data and data["authors"]:
            try:
                key = data["authors"][0]["key"]
                a = requests.get(f"https://openlibrary.org{key}.json").json()
                author = a.get("name", author)
            except:
                pass
        elif "contributors" in data and data["contributors"]:
            author = data["contributors"][0].get("name", author)

        return title, author

    except:
        return None