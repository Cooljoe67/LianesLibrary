import requests

def lookup_book_metadata(isbn):
    clean = isbn.replace("-", "").strip()

    # ------------------------------------
    # 1) Try Google Books API
    # ------------------------------------
    try:
        g_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean}"
        g = requests.get(g_url, timeout=5).json()

        if "items" in g and len(g["items"]) > 0:
            info = g["items"][0]["volumeInfo"]

            return {
                "title": info.get("title", "Unknown Title"),
                "author": ", ".join(info.get("authors", ["Unknown Author"])),
                "publisher": info.get("publisher"),
                "publish_date": info.get("publishedDate"),
                "pages": info.get("pageCount"),
                "subjects": info.get("categories"),
                "source": "google"
            }
    except:
        pass

    # ------------------------------------
    # 2) Fallback: OpenLibrary
    # ------------------------------------
    try:
        ol_url = f"https://openlibrary.org/isbn/{clean}.json"
        r = requests.get(ol_url, timeout=5)

        if r.status_code != 200:
            return None

        data = r.json()

        # Title
        title = data.get("title", "Unknown Title")

        # Publisher
        publisher = None
        if "publishers" in data and data["publishers"]:
            publisher = data["publishers"][0]

        # Publish date
        publish_date = data.get("publish_date")

        # Pages
        pages = data.get("number_of_pages")

        # Subjects
        subjects = data.get("subjects")

        # Author resolution
        author = "Unknown Author"
        if "authors" in data and data["authors"]:
            try:
                key = data["authors"][0]["key"]
                a = requests.get(f"https://openlibrary.org{key}.json").json()
                author = a.get("name", author)
            except:
                pass

        return {
            "title": title,
            "author": author,
            "publisher": publisher,
            "publish_date": publish_date,
            "pages": pages,
            "subjects": subjects,
            "source": "openlibrary"
        }

    except:
        pass

    # ------------------------------------
    # 3) Nothing found
    # ------------------------------------
    return None