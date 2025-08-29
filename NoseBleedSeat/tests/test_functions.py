import pytest
from NoseBleedSeat.functions import (
    get_accolades,
    get_word_of_the_day,
    fetch_player_data,
    get_player_awards,
    get_league_leaders,
    get_per_game_stats,
    search_team_by_name,
    get_player_bio,

)
from nba_teams.models import EasternConferenceTeams, WesternConferenceTeams
from django.core.management import call_command


@pytest.fixture
def player_name():
    return "Kobe Bryant"

@pytest.fixture
def player_id():
    return 977

@pytest.fixture
def invalid_player_id():
    return -1


class TestWordOfTheDay:

    def test_get_word_of_the_day(self):
        word_of_the_day = get_word_of_the_day()

        assert word_of_the_day is not None
        assert isinstance(word_of_the_day, str)
    
    def test_randomness(self):
        first_word_of_the_day = get_word_of_the_day()
        second_word_of_the_day = get_word_of_the_day()

        assert first_word_of_the_day is not None
        assert second_word_of_the_day is not None

        assert isinstance(first_word_of_the_day, str)
        assert isinstance(second_word_of_the_day, str)

        assert first_word_of_the_day != second_word_of_the_day


class TestPlayerData:

    @pytest.mark.django_db
    def test_fetch_player_data_by_player_name(self, player_name, player_id):
        player_data = fetch_player_data(player_name=player_name)

        assert player_data is not None
        assert player_data[1]["player_name"] == player_name
        assert player_data[1]["player_id"] == player_id
    
    @pytest.mark.django_db
    def test_fetch_player_data_by_player_id(self, player_name, player_id):
        player_data = fetch_player_data(player_name="xxxxx", player_id=player_id)

        assert player_data is not None
        assert player_data[1]["player_id"] == player_id


class TestSearchTeamByName:

    @pytest.fixture
    def eastern_teams(self):
        return EasternConferenceTeams.objects.all()
    
    @pytest.fixture
    def western_teams(self):
        return WesternConferenceTeams.objects.all()
    
    @pytest.fixture
    def team_name(self):
        return "LA Clippers"

    @pytest.fixture(scope="function", autouse=True)
    def load_teams_data(self):
        call_command("insert_teams")
    
    
    @pytest.mark.django_db
    def test_get_player_awards(self, team_name, eastern_teams, western_teams):
        team_id = search_team_by_name(team_name, eastern_teams, western_teams)
        
        assert team_id is not None
        assert isinstance(team_id, int)
    

class TestPlayerAwards:


    @pytest.mark.django_db
    def test_get_player_awards(self, player_name, player_id):
        player_awards = get_player_awards(player_name, player_id)

        assert player_awards, "Expected to have award data"
        assert isinstance(player_awards, dict)


class TestLeagueLeaders:

    @pytest.mark.django_db
    @pytest.mark.skip(reason="function not used!")
    def test_get_league_leaders(self):
        get_league_leaders()


class TestPerGameStats:

    @pytest.mark.django_db
    def test_get_per_game_stats(self, player_id):
        game_stats = get_per_game_stats(player_id)

        assert game_stats
        assert isinstance(game_stats, list)
    
    @pytest.mark.django_db
    def test_get_invalid_per_game_stats(self, invalid_player_id):
        with pytest.raises(KeyError):
            get_per_game_stats(invalid_player_id)


class TestPlayerBio:

    @pytest.mark.django_db
    def test_get_player_bio(self, player_id):
        player_bio = get_player_bio(player_id)
        
        assert player_bio
        assert isinstance(player_bio, dict)
    
    @pytest.mark.django_db
    def test_get_invalid_player_bio(self, invalid_player_id):
        with pytest.raises(KeyError):
            get_player_bio(invalid_player_id)


class TestAccolades:

    @pytest.mark.django_db
    def test_get_accolades(self, player_id):
        accolades = get_accolades(player_id)

        assert accolades
        assert isinstance(accolades, dict)
    
    @pytest.mark.django_db
    def test_get_invalid_accolades(self, invalid_player_id):
        with pytest.raises(KeyError):
            get_accolades(invalid_player_id)

