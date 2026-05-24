import pytest
from nba_stats.models import Player, SeasonStat


# ── DB helpers ────────────────────────────────────────────────────────────────

def make_player(player_id, full_name):
    return Player.objects.create(player_id=player_id, full_name=full_name)


def make_season_stat(player, season_id, **kwargs):
    defaults = {
        'season_type': 'Regular',
        'games_played': 82,
        'games_started': 0,
        'minutes': 0,
        'fgm': 0, 'fga': 0, 'fg_pct': 0.0,
        'fg3m': 0, 'fg3a': 0, 'fg3_pct': 0.0,
        'ftm': 0, 'fta': 0, 'ft_pct': 0.0,
        'oreb': 0, 'dreb': 0, 'reb': 0,
        'ast': 0, 'stl': 0, 'blk': 0,
        'tov': 0, 'pf': 0, 'pts': 0,
    }
    defaults.update(kwargs)
    return SeasonStat.objects.create(player=player, season_id=season_id, **defaults)


def _graph(p1_id, p1_name, p2_id, p2_name, stat):
    from NoseBleedSeat.views import _build_archive_graph
    return _build_archive_graph(p1_id, p1_name, p2_id, p2_name, stat)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBuildArchiveGraph:

    def test_unknown_stat_returns_none(self):
        result = _graph(1, 'A', 2, 'B', 'NOT_A_REAL_STAT')
        assert result is None

    @pytest.mark.django_db
    def test_no_season_data_returns_none(self):
        result = _graph(99999, 'Ghost', 99998, 'Nobody', 'PPG')
        assert result is None

    @pytest.mark.django_db
    def test_counting_stat_computes_per_game(self):
        p1 = make_player(1001, 'Test Player One')
        p2 = make_player(1002, 'Test Player Two')
        make_season_stat(p1, '2022-23', pts=2050, games_played=82)   # 25.0 PPG
        make_season_stat(p2, '2020-21', pts=1800, games_played=72)   # 25.0 PPG

        result = _graph(1001, 'Test Player One', 1002, 'Test Player Two', 'PPG')

        assert result is not None
        assert 25.0 in result['datasets'][0]['data']
        assert 25.0 in result['datasets'][1]['data']

    @pytest.mark.django_db
    def test_percentage_stat_converted_to_display_percent(self):
        p1 = make_player(2001, 'Shooter One')
        p2 = make_player(2002, 'Shooter Two')
        # Stored as fractions (0.0–1.0), should be multiplied by 100 for display
        make_season_stat(p1, '2022-23', fg_pct=0.500, games_played=82)
        make_season_stat(p2, '2021-22', fg_pct=0.450, games_played=70)

        result = _graph(2001, 'Shooter One', 2002, 'Shooter Two', 'FG_PCT')

        assert result is not None
        assert 50.0 in result['datasets'][0]['data']
        assert 45.0 in result['datasets'][1]['data']

    @pytest.mark.django_db
    def test_shorter_career_padded_with_zeros(self):
        p1 = make_player(3001, 'Vet Player')
        p2 = make_player(3002, 'Rookie Player')
        make_season_stat(p1, '2020-21', pts=1640, games_played=82)
        make_season_stat(p1, '2021-22', pts=1722, games_played=82)
        make_season_stat(p1, '2022-23', pts=1804, games_played=82)
        make_season_stat(p2, '2022-23', pts=1230, games_played=82)  # 1 season only

        result = _graph(3001, 'Vet Player', 3002, 'Rookie Player', 'PPG')

        assert result is not None
        assert len(result['labels']) == 3
        assert len(result['datasets'][0]['data']) == 3
        assert len(result['datasets'][1]['data']) == 3
        # p2's two missing years are padded
        assert result['datasets'][1]['data'].count(0) == 2

    @pytest.mark.django_db
    def test_chart_structure_and_player_labels(self):
        p1 = make_player(4001, 'Alpha Player')
        p2 = make_player(4002, 'Beta Player')
        make_season_stat(p1, '2022-23', pts=2050, games_played=82)
        make_season_stat(p2, '2022-23', pts=1640, games_played=82)

        result = _graph(4001, 'Alpha Player', 4002, 'Beta Player', 'PPG')

        assert 'labels' in result
        assert 'datasets' in result
        assert len(result['datasets']) == 2
        assert result['datasets'][0]['label'] == 'Alpha Player'
        assert result['datasets'][1]['label'] == 'Beta Player'
        assert result['datasets'][0]['borderColor'] == '#00284D'
        assert result['datasets'][1]['borderColor'] == '#F85D2B'

    @pytest.mark.django_db
    def test_playoffs_rows_excluded(self):
        # Only 'Regular' season_type rows should appear in the graph
        p1 = make_player(5001, 'Regular Season Guy')
        p2 = make_player(5002, 'Playoffs Only Guy')
        make_season_stat(p1, '2022-23', pts=2050, games_played=82, season_type='Regular')
        make_season_stat(p2, '2022-23', pts=500, games_played=20, season_type='Post')

        result = _graph(5001, 'Regular Season Guy', 5002, 'Playoffs Only Guy', 'PPG')

        # p2 has no Regular Season data so result may be None or p2 data is empty
        if result is not None:
            assert all(v == 0 for v in result['datasets'][1]['data'])

    @pytest.mark.django_db
    def test_seasons_ordered_chronologically(self):
        p1 = make_player(6001, 'Career Player')
        p2 = make_player(6002, 'Also Player')
        make_season_stat(p1, '2022-23', pts=2050, games_played=82)
        make_season_stat(p1, '2019-20', pts=1640, games_played=82)
        make_season_stat(p2, '2022-23', pts=1800, games_played=82)

        result = _graph(6001, 'Career Player', 6002, 'Also Player', 'PPG')

        assert result is not None
        # First year should be the earlier season (2019-20: 20.0 PPG)
        assert result['datasets'][0]['data'][0] == 20.0
        # Second year should be 2022-23 (25.0 PPG)
        assert result['datasets'][0]['data'][1] == 25.0
