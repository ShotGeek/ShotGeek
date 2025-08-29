import pytest


@pytest.fixture
def player_name():
    return "Kobe Bryant"

@pytest.fixture
def player_id():
    return 977

@pytest.fixture
def default_player1_name():
    return "Michael Jordan"

@pytest.fixture
def default_player2_name():
    return "LeBron James"



class TestHome:

    @pytest.mark.django_db
    def test_home(self, default_player1_name, default_player2_name, client):
        response = client.get("/")

        assert response.status_code == 200

        content = response.content.decode()
        assert default_player1_name in content
        assert default_player2_name in content

    @pytest.mark.django_db
    def test_search_player_without_follow_redirect(self, player_name, client):
        data = {
            "player_name": player_name
        }

        response = client.post("/", data)
        assert response.status_code == 302
    
    @pytest.mark.django_db
    def test_search_player_with_follow_redirect(self, player_name, client):
        data = {
            "player_name": player_name
        }

        response = client.post("/", data, follow=True)
        
        assert response.status_code == 200
        assert player_name in response.content.decode()



def test_about_view(client):
    response = client.get("/about/")

    assert response.status_code == 200
    assert "About ShotGeek" in response.content.decode()


@pytest.mark.django_db
def test_show_career_awards_player1(player_name, player_id, client):
    response = client.get(f"/show-career-awards-player1/{player_name}/{player_id}")

    assert response.status_code == 200
    assert "Career Awards" in response.content.decode()


@pytest.mark.django_db
def test_show_career_awards_player2(player_name, player_id, client):
    response = client.get(f"/show-career-awards-player2/{player_name}/{player_id}")

    assert response.status_code == 200
    assert "Career Awards" in response.content.decode()


