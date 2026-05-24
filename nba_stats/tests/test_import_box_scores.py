import pandas as pd
import pytest
from unittest.mock import patch
from django.core.management import call_command
from nba_stats.models import Player, PlayerStats, SeasonStat, CareerStat


PATCH_TARGET = 'nba_stats.management.commands.import_box_scores.kagglehub.load_dataset'

# A single realistic game row matching the Kaggle CSV column names
BASE_ROW = {
    'personId': 7001,
    'gameDateTimeEst': '2023-01-15 22:00:00',  # → season 2022-23
    'gameType': 'Regular Season',
    'points': 30,
    'reboundsTotal': 8,
    'reboundsOffensive': 2,
    'reboundsDefensive': 6,
    'assists': 5,
    'steals': 1,
    'blocks': 1,
    'fieldGoalsMade': 12,
    'fieldGoalsAttempted': 22,
    'threePointersMade': 3,
    'threePointersAttempted': 7,
    'freeThrowsMade': 3,
    'freeThrowsAttempted': 4,
    'turnovers': 2,
    'foulsPersonal': 3,
}


@pytest.fixture
def player(db):
    return Player.objects.create(player_id=7001, full_name='Import Test Player')


def run_command(df):
    with patch(PATCH_TARGET, return_value=df):
        call_command('import_box_scores')


# ── SeasonStat ────────────────────────────────────────────────────────────────

class TestSeasonStat:

    @pytest.mark.django_db
    def test_creates_season_stat_record(self, player):
        run_command(pd.DataFrame([BASE_ROW]))
        assert SeasonStat.objects.filter(
            player=player, season_id='2022-23', season_type='Regular'
        ).exists()

    @pytest.mark.django_db
    def test_season_totals_summed_correctly(self, player):
        second_game = {**BASE_ROW, 'points': 20, 'gameDateTimeEst': '2023-02-01 22:00:00'}
        run_command(pd.DataFrame([BASE_ROW, second_game]))

        stat = SeasonStat.objects.get(player=player, season_id='2022-23', season_type='Regular')
        assert stat.games_played == 2
        assert stat.pts == 50   # 30 + 20
        assert stat.ast == 10   # 5 + 5

    @pytest.mark.django_db
    def test_playoff_game_creates_post_season_stat(self, player):
        playoff_row = {**BASE_ROW, 'gameType': 'Playoffs'}
        run_command(pd.DataFrame([playoff_row]))

        assert SeasonStat.objects.filter(player=player, season_type='Post').exists()

    @pytest.mark.django_db
    def test_october_game_assigned_to_correct_season(self, player):
        # October → start of a new season (e.g. Oct 2023 → 2023-24)
        row = {**BASE_ROW, 'gameDateTimeEst': '2023-10-20 22:00:00'}
        run_command(pd.DataFrame([row]))

        assert SeasonStat.objects.filter(player=player, season_id='2023-24').exists()

    @pytest.mark.django_db
    def test_fg_pct_computed_correctly(self, player):
        run_command(pd.DataFrame([BASE_ROW]))  # 12 FGM / 22 FGA = 0.545

        stat = SeasonStat.objects.get(player=player, season_id='2022-23', season_type='Regular')
        assert round(stat.fg_pct, 3) == round(12 / 22, 3)

    @pytest.mark.django_db
    def test_upsert_on_rerun(self, player):
        df = pd.DataFrame([BASE_ROW])
        run_command(df)
        run_command(df)  # second run should update, not duplicate

        assert SeasonStat.objects.filter(player=player, season_id='2022-23').count() == 1


# ── CareerStat ────────────────────────────────────────────────────────────────

class TestCareerStat:

    @pytest.mark.django_db
    def test_creates_career_stat_record(self, player):
        run_command(pd.DataFrame([BASE_ROW]))
        assert CareerStat.objects.filter(player=player, season_type='Regular').exists()

    @pytest.mark.django_db
    def test_career_totals_span_multiple_seasons(self, player):
        season2 = {**BASE_ROW, 'gameDateTimeEst': '2022-01-15 22:00:00'}  # → 2021-22
        run_command(pd.DataFrame([BASE_ROW, season2]))

        career = CareerStat.objects.get(player=player, season_type='Regular')
        assert career.gp == 2
        assert career.pts == 60  # 30 + 30


# ── PlayerStats ───────────────────────────────────────────────────────────────

class TestPlayerStats:

    @pytest.mark.django_db
    def test_creates_player_stats(self, player):
        run_command(pd.DataFrame([BASE_ROW]))
        assert PlayerStats.objects.filter(player=player).exists()

    @pytest.mark.django_db
    def test_player_stats_are_per_game_averages(self, player):
        second_game = {**BASE_ROW, 'points': 20, 'assists': 3,
                       'gameDateTimeEst': '2023-02-01 22:00:00'}
        run_command(pd.DataFrame([BASE_ROW, second_game]))

        stats = PlayerStats.objects.get(player=player)
        assert stats.PTS == 25.0  # (30 + 20) / 2
        assert stats.AST == 4.0   # (5 + 3) / 2

    @pytest.mark.django_db
    def test_playoffs_do_not_create_player_stats(self, player):
        playoff_row = {**BASE_ROW, 'gameType': 'Playoffs'}
        run_command(pd.DataFrame([playoff_row]))
        assert not PlayerStats.objects.filter(player=player).exists()


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:

    @pytest.mark.django_db
    def test_unknown_player_id_skipped(self):
        row = {**BASE_ROW, 'personId': 99999}  # not in Player table
        run_command(pd.DataFrame([row]))
        assert SeasonStat.objects.count() == 0

    @pytest.mark.django_db
    def test_kaggle_failure_exits_gracefully(self):
        with patch(PATCH_TARGET, side_effect=Exception('network error')):
            call_command('import_box_scores')  # should not raise
        assert SeasonStat.objects.count() == 0

    @pytest.mark.django_db
    def test_unknown_game_type_skipped(self, player):
        row = {**BASE_ROW, 'gameType': 'Preseason'}
        run_command(pd.DataFrame([row]))
        assert SeasonStat.objects.count() == 0
