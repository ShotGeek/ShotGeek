import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from nba_stats.models import Player, PlayerStats, SeasonStat, CareerStat


def _season_from_date(date_str):
    try:
        s = str(date_str)
        year = int(s[:4])
        month = int(s[5:7])
        start = year if month >= 10 else year - 1
        return f"{start}-{str(start + 1)[2:]}"
    except (ValueError, IndexError):
        return None


# Maps CSV column names -> SeasonStat / CareerStat field names
COL_MAP = {
    'fieldGoalsMade':         'fgm',
    'fieldGoalsAttempted':    'fga',
    'threePointersMade':      'fg3m',
    'threePointersAttempted': 'fg3a',
    'freeThrowsMade':         'ftm',
    'freeThrowsAttempted':    'fta',
    'reboundsOffensive':      'oreb',
    'reboundsDefensive':      'dreb',
    'reboundsTotal':          'reb',
    'assists':                'ast',
    'steals':                 'stl',
    'blocks':                 'blk',
    'turnovers':              'tov',
    'foulsPersonal':          'pf',
    'points':                 'pts',
}

GAME_TYPE_MAP = {
    'Regular Season': 'Regular',
    'Playoffs': 'Post',
}


class Command(BaseCommand):
    help = "Import Kaggle player box scores into SeasonStat, CareerStat, and PlayerStats."

    def handle(self, *args, **kwargs):
        self.stdout.write("Downloading Kaggle dataset...")
        try:
            df = kagglehub.load_dataset(
                KaggleDatasetAdapter.PANDAS,
                "eoinamoore/historical-nba-data-and-player-box-scores",
                "PlayerStatistics.csv",
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to load dataset: {e}"))
            return

        self.stdout.write(f"Loaded {len(df):,} rows. Processing...")

        # Normalise personId
        df['personId'] = pd.to_numeric(df['personId'], errors='coerce')
        df = df.dropna(subset=['personId'])
        df['personId'] = df['personId'].astype(int)

        # Derive season and season type
        df['season_id'] = df['gameDateTimeEst'].apply(_season_from_date)
        df = df.dropna(subset=['season_id'])
        df['season_type'] = df['gameType'].map(GAME_TYPE_MAP)
        df = df[df['season_type'].notna()]

        # Coerce all stat columns that exist in this CSV to numeric
        present_cols = [c for c in COL_MAP if c in df.columns]
        for col in present_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Build player_id -> Player lookup once to avoid per-row DB hits
        player_map = {p.player_id: p for p in Player.objects.all()}

        season_count = career_count = stats_count = 0

        # Accumulate career totals while processing seasons
        # key: (person_id, season_type) -> {field: total, 'gp': int}
        career_buckets: dict = {}

        self.stdout.write("Writing season stats...")
        with transaction.atomic():
            for (person_id, season_id, season_type), group in df.groupby(
                ['personId', 'season_id', 'season_type']
            ):
                player = player_map.get(person_id)
                if not player:
                    continue

                gp = len(group)

                # Sum each stat column that exists; default absent columns to 0
                totals = {
                    field: int(group[csv_col].sum())
                    for csv_col, field in COL_MAP.items()
                    if csv_col in df.columns
                }
                # Ensure every SeasonStat field has a value even if CSV col is absent
                for field in COL_MAP.values():
                    totals.setdefault(field, 0)

                fga, fgm = totals['fga'], totals['fgm']
                fg3a, fg3m = totals['fg3a'], totals['fg3m']
                fta, ftm = totals['fta'], totals['ftm']

                SeasonStat.objects.update_or_create(
                    player=player,
                    season_id=season_id,
                    season_type=season_type,
                    defaults={
                        'team': None,
                        'player_age': None,
                        'games_played': gp,
                        'games_started': 0,
                        'minutes': 0,
                        'fg_pct': round(fgm / fga, 3) if fga > 0 else 0.0,
                        'fg3_pct': round(fg3m / fg3a, 3) if fg3a > 0 else 0.0,
                        'ft_pct': round(ftm / fta, 3) if fta > 0 else 0.0,
                        **totals,
                    }
                )
                season_count += 1

                # Accumulate into career bucket
                key = (person_id, season_type)
                if key not in career_buckets:
                    career_buckets[key] = {'gp': 0, **{f: 0 for f in COL_MAP.values()}}
                career_buckets[key]['gp'] += gp
                for field, val in totals.items():
                    career_buckets[key][field] += val

            self.stdout.write("Writing career stats and player averages...")
            for (person_id, season_type), bucket in career_buckets.items():
                player = player_map.get(person_id)
                if not player:
                    continue

                gp = bucket['gp'] or 1
                fga, fgm = bucket['fga'], bucket['fgm']
                fg3a, fg3m = bucket['fg3a'], bucket['fg3m']
                fta, ftm = bucket['fta'], bucket['ftm']

                CareerStat.objects.update_or_create(
                    player=player,
                    season_type=season_type,
                    defaults={
                        'gp': gp,
                        'gs': 0,
                        'min': 0,
                        'fg_pct': round(fgm / fga, 3) if fga > 0 else 0.0,
                        'fg3_pct': round(fg3m / fg3a, 3) if fg3a > 0 else 0.0,
                        'ft_pct': round(ftm / fta, 3) if fta > 0 else 0.0,
                        **{f: v for f, v in bucket.items() if f != 'gp'},
                    }
                )
                career_count += 1

                # PlayerStats stores career per-game averages, Regular Season only
                if season_type == 'Regular':
                    PlayerStats.objects.update_or_create(
                        player=player,
                        defaults={
                            'PTS': round(bucket['pts'] / gp, 1),
                            'REB': round(bucket['reb'] / gp, 1),
                            'AST': round(bucket['ast'] / gp, 1),
                            'BLK': round(bucket['blk'] / gp, 1),
                            'STL': round(bucket['stl'] / gp, 1),
                        }
                    )
                    stats_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done — SeasonStat: {season_count}, CareerStat: {career_count}, PlayerStats: {stats_count}"
        ))
