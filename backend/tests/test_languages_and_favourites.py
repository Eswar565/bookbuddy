import pytest
from app import app
from app.services.languages import parse_languages, get_distinct_languages, sync_book_languages
from app.routes.site import get_db

def test_parse_languages():
    assert parse_languages("English, Tamil") == ["English", "Tamil"]
    assert parse_languages("English / Tamil") == ["English", "Tamil"]
    assert parse_languages("English & Hindi") == ["English", "Hindi"]
    assert parse_languages("English; French") == ["English", "French"]
    assert parse_languages("English | German") == ["English", "German"]
    assert parse_languages("English and Tamil") == ["English", "Tamil"]
    assert parse_languages("  english  ") == ["English"]
    assert parse_languages("English, english, ENGLISH") == ["English"]
    assert parse_languages("") == []
    assert parse_languages(None) == []

def test_get_distinct_languages_no_combined_or_duplicates():
    with app.app_context():
        db = get_db()
        langs = get_distinct_languages(db)
        assert isinstance(langs, list)
        for lang in langs:
            assert "," not in lang
            assert "/" not in lang
            assert "&" not in lang
            assert ";" not in lang
            assert "|" not in lang
            assert " and " not in lang.lower()
            assert lang == lang.strip().title()
        # Ensure no duplicates case-insensitively
        assert len(langs) == len(set(l.lower() for l in langs))
        # Ensure sorted A-Z
        assert langs == sorted(langs)

def test_api_filter_options_languages():
    app.config["TESTING"] = True
    with app.test_client() as client:
        res = client.get("/api/v1/books")
        assert res.status_code == 200
        data = res.get_json()["data"]
        filter_options = data.get("filter_options", {})
        
        for key in ["language", "languages"]:
            langs = filter_options.get(key, [])
            assert isinstance(langs, list)
            assert len(langs) > 0
            for lang in langs:
                assert "," not in lang
                assert "/" not in lang
                assert "&" not in lang
                assert " and " not in lang.lower()
            assert len(langs) == len(set(l.lower() for l in langs))

def test_multilingual_book_filtering():
    app.config["TESTING"] = True
    with app.app_context():
        db = get_db()
        # Create or update a book with English, Tamil
        cursor = db.cursor()
        cursor.execute("SELECT id FROM books LIMIT 1")
        book = cursor.fetchone()
        assert book is not None
        book_id = book["id"]
        
        cursor.execute("UPDATE books SET language = 'English, Tamil' WHERE id = ?", (book_id,))
        db.commit()
        sync_book_languages(db, book_id, "English, Tamil")

    with app.test_client() as client:
        # Search by English
        res_en = client.get("/api/v1/books?lang=English")
        assert res_en.status_code == 200
        books_en = res_en.get_json()["data"]["books"]
        ids_en = [b["id"] for b in books_en]
        assert book_id in ids_en

        # Search by Tamil
        res_ta = client.get("/api/v1/books?lang=Tamil")
        assert res_ta.status_code == 200
        books_ta = res_ta.get_json()["data"]["books"]
        ids_ta = [b["id"] for b in books_ta]
        assert book_id in ids_ta

def test_library_favourites_page_guest_and_member():
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Guest request to Jinja /library/favourites/ must return 200 without UndefinedError
        res_guest = client.get("/library/favourites/")
        assert res_guest.status_code == 200
        html = res_guest.get_data(as_text=True)
        assert "My Favourite Books" in html
        assert "Log in to save your favourites to your account" in html
        assert "No favourites yet. Tap the heart on a book to save it." in html

        # Logged in member request
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user"] = {"id": 1, "name": "Test User", "role": "member", "is_member": True}

        res_member = client.get("/library/favourites/")
        assert res_member.status_code == 200
        html_member = res_member.get_data(as_text=True)
        assert "My Favourite Books" in html_member

def test_api_favourites_guest_and_member_flow():
    app.config["TESTING"] = True
    with app.test_client() as client:
        # 1. Guest get favourites
        res = client.get("/api/v1/library/favourites")
        assert res.status_code == 200
        body = res.get_json()["data"]
        assert body["is_guest"] is True
        assert body["book_ids"] == []

        # 2. Guest get favourites with ?ids=1
        res_with_ids = client.get("/api/v1/library/favourites?ids=1")
        assert res_with_ids.status_code == 200
        body_ids = res_with_ids.get_json()["data"]
        assert body_ids["is_guest"] is True
        assert len(body_ids["favourites"]) == 1
        assert body_ids["favourites"][0]["id"] == 1

        # 3. Logged-in member flow
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user"] = {"id": 1, "name": "Test User", "role": "member", "is_member": True}

        # Add book 1 to favourites
        add_res = client.post("/api/v1/library/favourites", json={"book_id": 1})
        assert add_res.status_code == 200
        assert add_res.get_json()["ok"] is True
        assert add_res.get_json()["data"]["is_favourite"] is True

        # Duplicate add is idempotent
        dup_res = client.post("/api/v1/library/favourites", json={"book_id": 1})
        assert dup_res.status_code == 200
        assert dup_res.get_json()["ok"] is True
        assert dup_res.get_json()["data"]["is_favourite"] is True

        # Check favourites list
        list_res = client.get("/api/v1/library/favourites")
        assert list_res.status_code == 200
        list_body = list_res.get_json()["data"]
        assert list_body["is_guest"] is False
        assert 1 in list_body["book_ids"]
        fav_ids = [b["id"] for b in list_body["favourites"]]
        assert 1 in fav_ids
        assert len([x for x in list_body["book_ids"] if x == 1]) == 1  # No duplicate entries

        # Delete book 1 from favourites
        del_res = client.delete("/api/v1/library/favourites/1")
        assert del_res.status_code == 200
        assert del_res.get_json()["ok"] is True
        assert del_res.get_json()["data"]["is_favourite"] is False

        # Idempotent delete
        del_res2 = client.delete("/api/v1/library/favourites/1")
        assert del_res2.status_code == 200

        # Check favourites list again
        list_res2 = client.get("/api/v1/library/favourites")
        list_body2 = list_res2.get_json()["data"]
        assert 1 not in list_body2["book_ids"]


def test_api_favourites_unauthorised_and_csrf():
    """Verify 401 for unauthorised mutations and proper CSRF handling."""
    with app.test_client() as client:
        # 1. Unauthorised POST -> 401
        res = client.post("/api/v1/library/favourites", json={"book_id": 1})
        assert res.status_code == 401
        assert res.get_json()["error"]["code"] == "AUTH_REQUIRED"

        # 2. Unauthorised DELETE -> 401
        res_del = client.delete("/api/v1/library/favourites/1")
        assert res_del.status_code == 401
        assert res_del.get_json()["error"]["code"] == "AUTH_REQUIRED"

        # 3. Logged-in session with CSRF protection enabled
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = "valid_test_token_123"

        # Turn TESTING temporarily off to test real CSRF verification logic
        app.config["TESTING"] = False
        try:
            # Missing CSRF -> 403
            res_bad_csrf = client.post("/api/v1/library/favourites", json={"book_id": 1})
            assert res_bad_csrf.status_code == 403
            assert res_bad_csrf.get_json()["error"]["code"] == "CSRF_FAILED"

            # Valid X-CSRF-Token header -> 200
            res_good_csrf = client.post(
                "/api/v1/library/favourites",
                json={"book_id": 1},
                headers={"X-CSRF-Token": "valid_test_token_123"}
            )
            assert res_good_csrf.status_code == 200
            assert res_good_csrf.get_json()["ok"] is True
        finally:
            app.config["TESTING"] = True

