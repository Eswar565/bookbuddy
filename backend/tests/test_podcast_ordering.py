import pytest
from app import app, get_db

@pytest.fixture
def podcast_test_data():
    app.config["TESTING"] = True
    ids = []
    with app.app_context():
        db = get_db()
        # Clean existing test podcast publications if any
        # Insert episodes 1, 2, 3, 10 with varied dates/labels to verify numeric ordering
        test_episodes = [
            ("Episode 10: The Finale", "Episode 10", "2026-11-01"),
            ("Episode 2: The Fox", "Episode 2", "2026-11-20"),
            ("Episode 1: The Beginning", "Episode 1", "2026-11-15"),
            ("Episode 3: Starry Night", "Episode 3", "2026-11-10"),
        ]
        # Temporarily deactivate others so only these 4 are returned
        db.execute("UPDATE publications SET is_active=0 WHERE kind='podcast'")
        for title, ep_label, pub_date in test_episodes:
            row_id = db.execute(
                """
                INSERT INTO publications (title, kind, episode_label, published_on, is_active, is_paid)
                VALUES (?, 'podcast', ?, ?, 1, 0)
                """,
                (title, ep_label, pub_date)
            ).lastrowid
            ids.append(row_id)
        db.commit()

    yield ids

    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM publications WHERE id IN ({})".format(",".join("?" * len(ids))), ids)
        # Re-activate original podcasts
        db.execute("UPDATE publications SET is_active=1 WHERE kind='podcast'")
        db.commit()


def test_podcast_numeric_ordering_default_and_asc(podcast_test_data):
    """Verify episodes 1, 2, 3, 10 return in numeric ascending order by default and with ?sort=asc."""
    with app.test_client() as client:
        # 1. API endpoint default (should be asc)
        res = client.get("/api/v1/media?kind=podcast")
        assert res.status_code == 200
        data = res.get_json()["data"]["items"]
        titles = [item["title"] for item in data]
        assert len(titles) == 4
        assert titles == [
            "Episode 1: The Beginning",
            "Episode 2: The Fox",
            "Episode 3: Starry Night",
            "Episode 10: The Finale",
        ], f"Expected numeric order 1, 2, 3, 10, got: {titles}"

        # 2. API endpoint ?sort=asc
        res_asc = client.get("/api/v1/media?kind=podcast&sort=asc")
        assert res_asc.status_code == 200
        data_asc = res_asc.get_json()["data"]["items"]
        titles_asc = [item["title"] for item in data_asc]
        assert titles_asc == [
            "Episode 1: The Beginning",
            "Episode 2: The Fox",
            "Episode 3: Starry Night",
            "Episode 10: The Finale",
        ]

        # 3. HTML route /podcasts/
        res_html = client.get("/podcasts/")
        assert res_html.status_code == 200
        html = res_html.get_data(as_text=True)
        # Check order of appearance in HTML
        pos_ep1 = html.find("Episode 1: The Beginning")
        pos_ep2 = html.find("Episode 2: The Fox")
        pos_ep3 = html.find("Episode 3: Starry Night")
        pos_ep10 = html.find("Episode 10: The Finale")
        assert pos_ep1 != -1 and pos_ep2 != -1 and pos_ep3 != -1 and pos_ep10 != -1
        assert pos_ep1 < pos_ep2 < pos_ep3 < pos_ep10, "HTML page should render 1, 2, 3, 10 in order"


def test_podcast_ordering_desc(podcast_test_data):
    """Verify ?sort=desc returns newest/highest numeric episode first (10, 3, 2, 1)."""
    with app.test_client() as client:
        # 1. API endpoint ?sort=desc
        res_desc = client.get("/api/v1/media?kind=podcast&sort=desc")
        assert res_desc.status_code == 200
        data_desc = res_desc.get_json()["data"]["items"]
        titles_desc = [item["title"] for item in data_desc]
        assert titles_desc == [
            "Episode 10: The Finale",
            "Episode 3: Starry Night",
            "Episode 2: The Fox",
            "Episode 1: The Beginning",
        ]

        # 2. HTML route /podcasts/?sort=desc
        res_html = client.get("/podcasts/?sort=desc")
        assert res_html.status_code == 200
        html = res_html.get_data(as_text=True)
        pos_ep1 = html.find("Episode 1: The Beginning")
        pos_ep2 = html.find("Episode 2: The Fox")
        pos_ep3 = html.find("Episode 3: Starry Night")
        pos_ep10 = html.find("Episode 10: The Finale")
        assert pos_ep10 < pos_ep3 < pos_ep2 < pos_ep1, "HTML page with ?sort=desc should render 10, 3, 2, 1 in order"
