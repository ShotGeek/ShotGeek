import pytest
from NoseBleedSeat.forms import PlayerOneForm, PlayerTwoForm



@pytest.fixture
def player_name():
    return "Kobe Bryant"


def test_player_one_form(player_name):
    form_data = {
        "player1_name": player_name 
    }

    form = PlayerOneForm(data=form_data)
    assert form.is_valid()


def test_player_two_form(player_name):
    form_data = {
        "player2_name": player_name
    }

    form = PlayerTwoForm(data=form_data)
    assert form.is_valid()


