from django.core.management.base import BaseCommand
from django.conf import settings
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
from nba_stats.models import Player, PlayerBio, PlayerStats, SeasonStat, CareerStat, SeasonRanking
from nba_teams.models import NBATeam
from balldontlie import BalldontlieAPI
import time
import os

API_KEY = os.getenv('BDL_API')
api = BalldontlieAPI(api_key=API_KEY)

# Only positions that fit max_length=2 and match PlayerBio.POSITION_CHOICES
_VALID_POSITIONS = {'PG', 'SG', 'G', 'SF', 'PF', 'F', 'C'}


def _clean_position(pos):
    """Return pos if it's a recognised 1-2 char code, else None."""
    if pos in _VALID_POSITIONS:
        return pos
    elif pos == 'G-F':
        return 'SF'
    elif pos == 'F-G':
        return 'SF'
    elif pos == 'F-C':
        return 'PF'
    elif pos == 'C-F':
        return 'PF'
    return None



NBA_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}


def create_proxy_url():
    username = getattr(settings, 'SMARTPROXY_USERNAME', None)
    password = getattr(settings, 'SMARTPROXY_PASSWORD', None)
    if username and password:
        return f"http://{username}:{password}@gate.smartproxy.com:10001"
    return None

class Command(BaseCommand):
    help = "Bulk populate Player Bios using Free BallDontLie API"

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only process active players locally (Note: API returns all, we filter matching).',
        )

    def handle(self, *args, **kwargs):
        active_only = kwargs['active_only']
        
        self.stdout.write(self.style.SUCCESS("Starting bulk sync (100 players per request)..."))

        # Build in-memory lookup maps for teams to minimize DB hits during player processing
        nba_teams = list(NBATeam.objects.all())
        teams_by_full_name = {t.full_name.lower(): t for t in nba_teams}
        teams_by_name = {t.name.lower(): t for t in nba_teams}
        teams_by_abbreviation = {t.abbreviation.upper(): t for t in nba_teams}
        teams_by_city_name = {f"{t.city} {t.name}".lower(): t for t in nba_teams}

        cursor = 0
        processed = 0
        updated = 0

        while True:
            try:
                # Access the API (Returns a PaginatedListResponse object)
                response = api.nba.players.list(per_page=100, cursor=cursor)
                data = response.data  # List of NBAPlayer objects
                meta = response.meta  # Metadata object

                for item in data:
                    processed += 1
                    
                    # Match API data to local database (Player Model)
                    # Using case-insensitive matching for robustness
                    player_qs = Player.objects.filter(
                        first_name__iexact=item.first_name, 
                        last_name__iexact=item.last_name
                    )
                    
                    # If we're filtering by active players
                    if active_only:
                        player_qs = player_qs.filter(status='Active')
                    
                    player = player_qs.first()

                    if player:
                        fields_to_update = [] # will store any fields we need to update based on API data

                        # Resolve and store NBATeam FK from API team info
                        api_team = getattr(item, 'team', None)
                        resolved_team = None
                        if api_team:
                            full_name = getattr(api_team, 'full_name', None)
                            abbreviation = getattr(api_team, 'abbreviation', None)
                            name = getattr(api_team, 'name', None)
                            city = getattr(api_team, 'city', None)

                            if full_name:
                                resolved_team = teams_by_full_name.get(full_name.lower())
                            if not resolved_team and abbreviation:
                                resolved_team = teams_by_abbreviation.get(abbreviation.upper())
                            if not resolved_team and name:
                                resolved_team = teams_by_name.get(name.lower())
                            if not resolved_team and city and name:
                                resolved_team = teams_by_city_name.get(f"{city} {name}".lower())

                        if resolved_team and player.team_id != resolved_team.team_id:
                            player.team = resolved_team
                            fields_to_update.append('team')

                        if fields_to_update:
                            player.save(update_fields=fields_to_update)

                        # Create or Update Bio
                        PlayerBio.objects.update_or_create(
                            player=player,
                            defaults={
                                'position': _clean_position(item.position),
                                'school': item.college,
                                'country': item.country,
                                'height': item.height,
                                'weight': item.weight if item.weight else None,
                                'draft_year': item.draft_year if item.draft_year else None,
                                'draft_round': item.draft_round if item.draft_round else None,
                                'draft_num': item.draft_number if item.draft_number else None,
                                'number': item.jersey_number if item.jersey_number else None,
                            }
                        )
                        updated += 1

                self.stdout.write(f"Processed {processed} API records... matched {updated} players.")

                # Check if there's a next page
                cursor = meta.next_cursor
                if cursor is None:
                    break

                # Respect the 5 RPM Free Tier (12.5s delay between requests)
                time.sleep(12.5)

            except Exception as e:
                if "Too Many Requests" in str(e):
                    self.stdout.write(self.style.WARNING("Rate limit hit. Sleeping for 60s..."))
                    time.sleep(60)
                    continue 
                else:
                    self.stdout.write(self.style.ERROR(f"Error: {e}"))
                    break

        self.stdout.write(self.style.SUCCESS(f"\nFinished. Total players updated: {updated}"))


# class Command(BaseCommand):
#     help = "Populate PlayerBio, PlayerStats, SeasonStat, CareerStat, and SeasonRanking for all players."

#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--active-only',
#             action='store_true',
#             help='Only process active players.',
#         )
#         parser.add_argument(
#             '--skip-existing',
#             action='store_true',
#             help='Skip players who already have both a bio and stats record.',
#         )

#     def handle(self, *args, **kwargs):
#         proxy_url = create_proxy_url()
#         active_only = kwargs['active_only']
#         skip_existing = kwargs['skip_existing']

#         players = Player.objects.all()
#         if active_only:
#             players = players.filter(status='Active')

#         total = players.count()
#         processed = skipped = failed = 0

#         self.stdout.write(
#             f"Starting: {total} players"
#             + (" (active only)" if active_only else "")
#             + (" (skipping existing)" if skip_existing else "")
#         )

#         for i, player in enumerate(players, 1):
#             name = player.full_name
#             player_id = player.player_id

#             if skip_existing:
#                 if (PlayerBio.objects.filter(player=player).exists()
#                         and PlayerStats.objects.filter(player=player).exists()):
#                     skipped += 1
#                     continue

#             self.stdout.write(f"[{i}/{total}] {name}")

#             try:
#                 # ── Bio (commonplayerinfo) ────────────────────────
#                 if proxy_url:
#                     info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, proxy=proxy_url)
#                 else:
#                     info = commonplayerinfo.CommonPlayerInfo(player_id=player_id, headers=NBA_HEADERS)

#                 result = info.get_dict()['resultSets'][0]
#                 data = result['rowSet'][0]
#                 headers = result['headers']

#                 def get(field):
#                     return data[headers.index(field)] if field in headers else None

#                 PlayerBio.objects.update_or_create(
#                     player=player,
#                     defaults={
#                         'team': get('TEAM_NAME') or '',
#                         'position': (get('POSITION') or '')[:2],
#                         'school': get('SCHOOL') or '',
#                         'country': get('COUNTRY') or '',
#                         'height': get('HEIGHT') or '',
#                         'weight': float(get('WEIGHT') or 0) or None,
#                         'year': get('DRAFT_YEAR') or None,
#                         'years_pro': int(get('SEASON_EXP') or 0) or None,
#                         'number': int(get('JERSEY') or 0) or None,
#                     }
#                 )
#                 time.sleep(0.6)

#                 # ── Career stats (playercareerstats) ──────────────
#                 # One call returns season totals, career totals, and
#                 # season rankings for both regular and post season.
#                 if proxy_url:
#                     career = playercareerstats.PlayerCareerStats(player_id=player_id, proxy=proxy_url)
#                 else:
#                     career = playercareerstats.PlayerCareerStats(player_id=player_id, headers=NBA_HEADERS)

#                 d = career.get_normalized_dict()

#                 # ── PlayerStats — career per-game averages ────────
#                 reg_totals = d.get('CareerTotalsRegularSeason', [])
#                 if reg_totals:
#                     t = reg_totals[0]
#                     gp = t['GP'] or 1
#                     PlayerStats.objects.update_or_create(
#                         player=player,
#                         defaults={
#                             'PTS': round(t['PTS'] / gp, 1),
#                             'REB': round(t['REB'] / gp, 1),
#                             'AST': round(t['AST'] / gp, 1),
#                             'BLK': round(t['BLK'] / gp, 1),
#                             'STL': round(t['STL'] / gp, 1),
#                         }
#                     )

#                 # ── SeasonStat — per-season box totals ────────────
#                 season_sources = [
#                     ('SeasonTotalsRegularSeason', 'Regular'),
#                     ('SeasonTotalsPostSeason', 'Post'),
#                 ]
#                 for key, season_type in season_sources:
#                     for row in d.get(key, []):
#                         team = NBATeam.objects.filter(team_id=row.get('TEAM_ID')).first()
#                         SeasonStat.objects.update_or_create(
#                             player=player,
#                             season_id=row['SEASON_ID'],
#                             season_type=season_type,
#                             defaults={
#                                 'team': team,
#                                 'player_age': row.get('PLAYER_AGE'),
#                                 'games_played': row.get('GP') or 0,
#                                 'games_started': row.get('GS') or 0,
#                                 'minutes': row.get('MIN') or 0,
#                                 'fgm': row.get('FGM') or 0,
#                                 'fga': row.get('FGA') or 0,
#                                 'fg_pct': row.get('FG_PCT') or 0,
#                                 'fg3m': row.get('FG3M') or 0,
#                                 'fg3a': row.get('FG3A') or 0,
#                                 'fg3_pct': row.get('FG3_PCT') or 0,
#                                 'ftm': row.get('FTM') or 0,
#                                 'fta': row.get('FTA') or 0,
#                                 'ft_pct': row.get('FT_PCT') or 0,
#                                 'oreb': row.get('OREB') or 0,
#                                 'dreb': row.get('DREB') or 0,
#                                 'reb': row.get('REB') or 0,
#                                 'ast': row.get('AST') or 0,
#                                 'stl': row.get('STL') or 0,
#                                 'blk': row.get('BLK') or 0,
#                                 'tov': row.get('TOV') or 0,
#                                 'pf': row.get('PF') or 0,
#                                 'pts': row.get('PTS') or 0,
#                             }
#                         )

#                 # ── CareerStat — career box totals ────────────────
#                 career_sources = [
#                     ('CareerTotalsRegularSeason', 'Regular'),
#                     ('CareerTotalsPostSeason', 'Post'),
#                 ]
#                 for key, season_type in career_sources:
#                     rows = d.get(key, [])
#                     if rows:
#                         row = rows[0]
#                         CareerStat.objects.update_or_create(
#                             player=player,
#                             season_type=season_type,
#                             defaults={
#                                 'gp': row.get('GP') or 0,
#                                 'gs': row.get('GS') or 0,
#                                 'min': row.get('MIN') or 0,
#                                 'fgm': row.get('FGM') or 0,
#                                 'fga': row.get('FGA') or 0,
#                                 'fg_pct': row.get('FG_PCT') or 0,
#                                 'fg3m': row.get('FG3M') or 0,
#                                 'fg3a': row.get('FG3A') or 0,
#                                 'fg3_pct': row.get('FG3_PCT') or 0,
#                                 'ftm': row.get('FTM') or 0,
#                                 'fta': row.get('FTA') or 0,
#                                 'ft_pct': row.get('FT_PCT') or 0,
#                                 'oreb': row.get('OREB') or 0,
#                                 'dreb': row.get('DREB') or 0,
#                                 'reb': row.get('REB') or 0,
#                                 'ast': row.get('AST') or 0,
#                                 'stl': row.get('STL') or 0,
#                                 'blk': row.get('BLK') or 0,
#                                 'tov': row.get('TOV') or 0,
#                                 'pf': row.get('PF') or 0,
#                                 'pts': row.get('PTS') or 0,
#                             }
#                         )

#                 # ── SeasonRanking ─────────────────────────────────
#                 ranking_sources = [
#                     ('SeasonRankingsRegularSeason', 'Regular'),
#                     ('SeasonRankingsPostSeason', 'Post'),
#                 ]
#                 for key, season_type in ranking_sources:
#                     for row in d.get(key, []):
#                         SeasonRanking.objects.update_or_create(
#                             player=player,
#                             season_id=row['SEASON_ID'],
#                             season_type=season_type,
#                             defaults={
#                                 'rank_pts': row.get('RANK_PTS'),
#                                 'rank_ast': row.get('RANK_AST'),
#                                 'rank_reb': row.get('RANK_REB'),
#                                 'rank_stl': row.get('RANK_STL'),
#                                 'rank_blk': row.get('RANK_BLK'),
#                             }
#                         )

#                 self.stdout.write(self.style.SUCCESS(f"  ✓ {name}"))
#                 processed += 1

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"  ✗ {name}: {e}"))
#                 failed += 1

#             time.sleep(0.6)

#         self.stdout.write(self.style.SUCCESS(
#             f"\nDone — processed: {processed}, skipped: {skipped}, failed: {failed}"
#         ))
