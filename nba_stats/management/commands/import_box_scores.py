import os

import kagglehub
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

CHUNK_SIZE = 50_000


class Command(BaseCommand):
    help = "Import Kaggle player box scores into SeasonStat, CareerStat, and PlayerStats."

    def handle(self, *args, **kwargs):
        self.stdout.write("Downloading Kaggle dataset...")
        try:
            dataset_path = kagglehub.dataset_download(
                "eoinamoore/historical-nba-data-and-player-box-scores"
            )
            csv_path = os.path.join(dataset_path, "PlayerStatistics.csv")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to download dataset: {e}"))
            return

        # Only read columns we actually need — keeps each chunk small
        needed = {'personId', 'gameDateTimeEst', 'gameType'} | set(COL_MAP.keys())

        # Build player_id -> Player lookup once to avoid per-row DB hits
        player_ids = set(Player.objects.values_list('player_id', flat=True))
        player_map = {p.player_id: p for p in Player.objects.all()}

        # Accumulate totals in memory across all chunks before any DB writes.
        # These dicts stay small (~players × seasons) regardless of CSV size.
        # season_buckets: (person_id, season_id, season_type) -> {field: total, 'gp': int}
        # career_buckets: (person_id, season_type)            -> {field: total, 'gp': int}
        season_buckets: dict = {}
        career_buckets: dict = {}

        self.stdout.write("Processing CSV in chunks...")
        total_rows = 0

        try:
            reader = pd.read_csv(
                csv_path,
                usecols=lambda c: c in needed,
                chunksize=CHUNK_SIZE,
                low_memory=False,
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to open CSV: {e}"))
            return

        for chunk in reader:
            total_rows += len(chunk)

            # Normalise personId
            chunk['personId'] = pd.to_numeric(chunk['personId'], errors='coerce')
            chunk = chunk.dropna(subset=['personId'])
            chunk['personId'] = chunk['personId'].astype(int)

            # Drop rows for players not in our DB early to save work
            chunk = chunk[chunk['personId'].isin(player_ids)]
            if chunk.empty:
                continue

            # Derive season and type
            chunk['season_id'] = chunk['gameDateTimeEst'].apply(_season_from_date)
            chunk = chunk.dropna(subset=['season_id'])
            chunk['season_type'] = chunk['gameType'].map(GAME_TYPE_MAP)
            chunk = chunk[chunk['season_type'].notna()]

            # Coerce stat columns to numeric
            for col in COL_MAP:
                if col in chunk.columns:
                    chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0)

            # Accumulate into buckets (one entry per player/season, not per row)
            for (person_id, season_id, season_type), group in chunk.groupby(
                ['personId', 'season_id', 'season_type']
            ):
                gp = len(group)
                totals = {
                    field: int(group[csv_col].sum())
                    for csv_col, field in COL_MAP.items()
                    if csv_col in chunk.columns
                }
                for field in COL_MAP.values():
                    totals.setdefault(field, 0)

                s_key = (person_id, season_id, season_type)
                if s_key not in season_buckets:
                    season_buckets[s_key] = {'gp': 0, **{f: 0 for f in COL_MAP.values()}}
                season_buckets[s_key]['gp'] += gp
                for field, val in totals.items():
                    season_buckets[s_key][field] += val

                c_key = (person_id, season_type)
                if c_key not in career_buckets:
                    career_buckets[c_key] = {'gp': 0, **{f: 0 for f in COL_MAP.values()}}
                career_buckets[c_key]['gp'] += gp
                for field, val in totals.items():
                    career_buckets[c_key][field] += val

        self.stdout.write(f"Read {total_rows:,} rows. Writing to database...")

        season_count = career_count = stats_count = 0

        with transaction.atomic():
            self.stdout.write("Writing season stats...")
            for (person_id, season_id, season_type), bucket in season_buckets.items():
                player = player_map.get(person_id)
                if not player:
                    continue

                gp = bucket['gp']
                fga, fgm = bucket['fga'], bucket['fgm']
                fg3a, fg3m = bucket['fg3a'], bucket['fg3m']
                fta, ftm = bucket['fta'], bucket['ftm']

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
                        **{f: v for f, v in bucket.items() if f != 'gp'},
                    }
                )
                season_count += 1

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
