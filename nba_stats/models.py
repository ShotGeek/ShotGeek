from django.db import models
from nba_teams.models import NBATeam
from django.utils import timezone
from django.db.models import F, Value
from django.db.models.functions import Coalesce, Greatest, NullIf, Substr, StrIndex, Length
import requests
from bs4 import BeautifulSoup

# Dictionary for team colors
TEAM_COLOURS = {
    1610612737: '#e03a3e', 1610612738: '#007A33', 1610612751: '#000000', 1610612766: '#00788c',
    1610612749: '#00471b', 1610612754: '#002d62', 1610612748: '#98002e', 1610612755: '#006bb6',
    1610612752: '#f58426', 1610612765: '#c8102e', 1610612757: '#e03a3e', 1610612759: '#c4ced4',
    1610612760: '#007ac1', 1610612758: '#5a2d81', 1610612761: '#ce1141', 1610612762: '#00a9e0',
    1610612740: '#0c2340', 1610612742: '#00538c', 1610612747: '#f9a01b', 1610612743: '#1d428a',
    1610612744: '#ffc72c', 1610612745: '#ce1141', 1610612746: '#1d428a', 1610612763: '#5d76a9',
    1610612750: '#236192', 1610612753: '#0077c0', 1610612756: '#e56020', 1610612764: '#002b5c',
    1610612739: '#860038', 1610612741: '#ce1141'
}

# Dictionary for team names
TEAMS = {
    1610612737: 'Hawks', 1610612738: 'Celtics', 1610612751: 'Nets', 1610612766: 'Hornets', 1610612749: 'Bucks',
    1610612754: 'Pacers', 1610612748: 'Heat', 1610612755: 'Sixers', 1610612752: 'Knicks', 1610612765: 'Pistons',
    1610612757: 'Blazers', 1610612759: 'Spurs', 1610612760: 'Thunder', 1610612758: 'Kings', 1610612761: 'Raptors',
    1610612762: 'Jazz', 1610612740: 'Pelicans', 1610612742: 'Mavericks', 1610612747: 'Lakers',
    1610612743: 'Nuggets', 1610612744: 'Warriors', 1610612745: 'Rockets', 1610612746: 'Clippers',
    1610612763: 'Grizzlies', 1610612750: 'Timberwolves', 1610612753: 'Magic', 1610612756: 'Suns',
    1610612764: 'Wizards', 1610612739: 'Cavaliers', 1610612741: 'Bulls'
}
    

class Player(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    player_id = models.IntegerField(primary_key=True)
    bdl_id = models.IntegerField(unique=True, null=True) # ball don't lie ID
    full_name = models.CharField(max_length=500)

    # Extract first name (everything before the first space).
    # Greatest(..., 0) prevents a negative length for single-name players (e.g. "Nene").
    # NullIf/Coalesce falls back to full_name when there is no space at all.
    first_name = models.GeneratedField(
        expression=Coalesce(
            NullIf(
                Substr('full_name', 1, Greatest(StrIndex('full_name', Value(' ')) - 1, Value(0))),
                Value(''),
            ),
            F('full_name'),
            output_field=models.CharField(max_length=100),
        ),
        output_field=models.CharField(max_length=100),
        db_persist=True,
    )

    # Extract last name (everything after the first space)
    last_name = models.GeneratedField(
        expression=Substr(
            'full_name',
            StrIndex('full_name', Value(' ')) + 1,
            Length('full_name')
        ),
        output_field=models.CharField(max_length=100),
        db_persist=True
    )

    image_url = models.URLField(
        default="https://static.vecteezy.com/system/resources/thumbnails/004/511/281/small_2x/default-avatar-photo-placeholder-profile-picture-vector.jpg"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    team = models.ForeignKey(
        'nba_teams.NBATeam',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="players"
    )

    def scrape_player_image(self):
        # begin scrapping for image url
        url = f'https://www.nba.com/player/{self.player_id}'

        # Make an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the player image tag within the appropriate class or element
        player_image_div = soup.find('div', {'class': 'PlayerSummary_mainInnerTeam____nFZ'})
        if player_image_div:
            img_tag = player_image_div.find('img',
                                            {'class': 'PlayerImage_image__wH_YX PlayerSummary_playerImage__sysif'})

            if img_tag:
                head_shot_url = img_tag['src']
                return head_shot_url

        return None 

    def __str__(self):
        return self.full_name


class PlayerBio(models.Model):
    POSITION_CHOICES = [
        ('PG', 'Point Guard'),
        ('SG', 'Shooting Guard'),
        ('G', 'Guard'),
        ('SF', 'Small Forward'),
        ('PF', 'Power Forward'),
        ('F', 'Forward'),
        ('C', 'Center'),
    ]
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="bio", null=True)
    position = models.CharField(max_length=2, choices=POSITION_CHOICES, blank=True, null=True)
    school = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    height = models.CharField(max_length=10, blank=True, null=True)
    weight = models.CharField(blank=True, null=True)
    draft_year = models.CharField(blank=True, null=True)
    number = models.CharField(blank=True, null=True)
    draft_round = models.CharField(blank=True, null=True)
    draft_num = models.CharField(blank=True, null=True)

    def __str__(self):
        return f"{self.player.full_name} Bio"


class PlayerStats(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="stats")
    PTS = models.FloatField(default=0)
    REB = models.FloatField(default=0)
    AST = models.FloatField(default=0)
    BLK = models.FloatField(default=0)
    STL = models.FloatField(default=0)

    def __str__(self):
        return f"{self.player.full_name} Stats"
    
class SeasonStat(models.Model):
    SEASON_TYPE_CHOICES = [
        ("Regular", "Regular Season"),
        ("Post", "Post Season")
    ]

    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="season_stats")
    team = models.ForeignKey("nba_teams.NBATeam", on_delete=models.SET_NULL, null=True)
    season_id = models.CharField(max_length=9)  # e.g. "2024-25"
    season_type = models.CharField(max_length=10, choices=SEASON_TYPE_CHOICES)
    player_age = models.FloatField(blank=True, null=True)
    games_played = models.PositiveIntegerField()
    games_started = models.PositiveIntegerField()
    minutes = models.PositiveIntegerField()
    
    # shooting
    fgm = models.PositiveIntegerField() # Field Goals Made
    fga = models.PositiveIntegerField() # Field Goals Attempted
    fg_pct = models.FloatField() # Field Goal Percentage
    fg3m = models.PositiveIntegerField() # 3-Point Field Goals Made
    fg3a = models.PositiveIntegerField() # 3-Point Field Goals Attempted
    fg3_pct = models.FloatField() # 3-Point Field Goal Percentage
    ftm = models.PositiveIntegerField() # Free Throws Made
    fta = models.PositiveIntegerField() # Free Throws Attempted
    ft_pct = models.FloatField() # Free Throw Percentage

    # other box stats
    oreb = models.PositiveIntegerField() # Offensive Rebounds
    dreb = models.PositiveIntegerField() # Defensive Rebounds
    reb = models.PositiveIntegerField() # Total Rebounds
    ast = models.PositiveIntegerField() # Assists
    stl = models.PositiveIntegerField() # Steals
    blk = models.PositiveIntegerField() # Blocks
    tov = models.PositiveIntegerField() # Turnovers
    pf = models.PositiveIntegerField() # Personal Fouls
    pts = models.PositiveIntegerField() # Points

    class Meta:
        unique_together = ("player", "season_id", "season_type")


class CareerStat(models.Model):
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="career_stats")
    season_type = models.CharField(max_length=10, choices=SeasonStat.SEASON_TYPE_CHOICES)
    gp = models.PositiveIntegerField()
    gs = models.PositiveIntegerField()
    min = models.PositiveIntegerField()
    fgm = models.PositiveIntegerField()
    fga = models.PositiveIntegerField()
    fg_pct = models.FloatField()
    fg3m = models.PositiveIntegerField()
    fg3a = models.PositiveIntegerField()
    fg3_pct = models.FloatField()
    ftm = models.PositiveIntegerField()
    fta = models.PositiveIntegerField()
    ft_pct = models.FloatField()
    oreb = models.PositiveIntegerField()
    dreb = models.PositiveIntegerField()
    reb = models.PositiveIntegerField()
    ast = models.PositiveIntegerField()
    stl = models.PositiveIntegerField()
    blk = models.PositiveIntegerField()
    tov = models.PositiveIntegerField()
    pf = models.PositiveIntegerField()
    pts = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.player.full_name} Career Stats - {self.season_type}"

class SeasonHigh(models.Model):
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="season_highs")
    game_id = models.CharField(max_length=20)
    game_date = models.DateField()
    opponent_team = models.ForeignKey("nba_teams.NBATeam", on_delete=models.SET_NULL, null=True)
    stat_name = models.CharField(max_length=20)  # e.g. "PTS"
    stat_value = models.FloatField()

    def __str__(self):
        return f"{self.player.full_name} - {self.game_date} {self.stat_name} High"
    

class SeasonRanking(models.Model):
    player = models.ForeignKey("Player", on_delete=models.CASCADE, related_name="season_rankings")
    season_id = models.CharField(max_length=9)
    season_type = models.CharField(max_length=10, choices=SeasonStat.SEASON_TYPE_CHOICES)
    rank_pts = models.IntegerField(null=True, blank=True)
    rank_ast = models.IntegerField(null=True, blank=True)
    rank_reb = models.IntegerField(null=True, blank=True)
    rank_stl = models.IntegerField(null=True, blank=True)
    rank_blk = models.IntegerField(null=True, blank=True)


class CareerAwards(models.Model):
    player_id = models.IntegerField(primary_key=True)
    player_name = models.CharField(max_length=100, default="N/A")
    accomplishments = models.JSONField(default=dict, blank=True)
    date = models.DateField(default=timezone.now, blank=True)  # Automatically set to today's date

    def __str__(self):
        return f"{self.player_name} Awards. Last Update {self.date}"


class LeagueLeaders(models.Model):
    date = models.DateField(default=timezone.now, blank=True)  # Automatically set to today's date
    leaders = models.JSONField(default=dict)  # Dictionary to store stat leaders

    def __str__(self):
        return f"League Leaders. Last Update {self.date}"



