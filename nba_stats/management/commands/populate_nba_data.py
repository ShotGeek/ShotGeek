from django.db import transaction
from django.core.management.base import BaseCommand
from django.conf import settings
from nba_teams.models import NBATeam, RetiredPlayers
from nba_stats.models import Player, TEAM_COLOURS
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import teamdetails, commonteamroster
import time

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


eastern_conference_teams = [
    "Boston Celtics",
    "Brooklyn Nets",
    "New York Knicks",
    "Philadelphia 76ers",
    "Toronto Raptors",
    "Miami Heat",
    "Milwaukee Bucks",
    "Atlanta Hawks",
    "Charlotte Hornets",
    "Chicago Bulls",
    "Cleveland Cavaliers",
    "Detroit Pistons",
    "Indiana Pacers",
    "Orlando Magic",
    "Washington Wizards"
]


class Command(BaseCommand):
    help = "Populate the database with NBA teams and players"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-retired',
            action='store_true',
            help='Skip fetching retired players',
        )

    def handle(self, *args, **kwargs):
        skip_retired = kwargs['skip_retired']
        self.stdout.write(self.style.SUCCESS("Starting NBA data population..."))

        with transaction.atomic():

            # Populate teams from static data (no HTTP request)
            nba_teams = teams.get_teams()
            for team in nba_teams:
                team_id = team["id"]
                logo_url = f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"
                _, created = NBATeam.objects.update_or_create(
                    team_id=team_id,
                    defaults={
                        "full_name": team["full_name"],
                        "name": team["nickname"],
                        "abbreviation": team["abbreviation"],
                        "conference": "East" if team["full_name"] in eastern_conference_teams else "West",
                        "city": team["city"],
                        "logo_url": logo_url,
                        "primary_colour": TEAM_COLOURS.get(team_id, "#FFFFFF"),
                    }
                )
                if created:
                    self.stdout.write(f"Added team: {team['full_name']}")

            self.stdout.write(self.style.SUCCESS(f"Teams populated: {NBATeam.objects.count()}"))

            # Populate all players from static data (no HTTP request)
            all_players = players.get_players()
            created_count = 0
            updated_count = 0

            for player in all_players:
                player_id = player["id"]
                image_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
                status = "Active" if player["is_active"] else "Inactive"

                _, created = Player.objects.update_or_create(
                    player_id=player_id,
                    defaults={
                        "full_name": player["full_name"],
                        "image_url": image_url,
                        "status": status,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Players populated: {created_count} created, {updated_count} updated"
                )
            )

        self.stdout.write(self.style.SUCCESS("NBA data population complete!"))
