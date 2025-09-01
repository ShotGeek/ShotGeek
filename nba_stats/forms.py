from django import forms
from django.core import validators
from .functions import get_years_played

STAT_OPTIONS = (
    ('--- View Stats By Year ---', '--- View Stats By Year  ---'),
    ('Reg. Season', 'Reg. Season'),
    ('Post Season', 'Post Season'),
    ('Reg. Season Rankings', 'Reg. Season Rankings'),
    ('Post Season Rankings', 'Post Season Rankings'),

)

STAT_OPTIONS2 = (
    ('--- Stats Totals By Year ---', '--- Stats Totals By Year  ---'),
    ('SeasonTotalsRegularSeason', 'Reg. Season'),
    ('SeasonTotalsPostSeason', 'Post Season'),
    ('SeasonRankingsRegularSeason', 'Reg. Season Rankings'),
    ('SeasonRankingsPostSeason', 'Post Season Rankings'),

)

# tuple where the first element is the value stored in the dictionary, and the second element is the user-readable
# option.
COMP_OPTIONS = (
    ('--- Compare Stats By Season ---', '--- Compare Stats By Season ---'),
    ('PPG', 'Points Per Game'),
    ('RPG', 'Rebs Per Game'),
    ('APG', 'Assists Per Game'),
    ('BLKPG', 'Blocks Per Game'),
    ('STLPG', 'Steals Per Game'),
    ('FGA', 'Field Goal Attempts'),
    ('FG_PCT', 'Field Goal %'),
    ('FG3A', 'Three-Point Attempts'),
    ('FG3_PCT', '3 Point %'),
    ('FT_PCT', 'Free Throw %'),
)

GRAPH_OPTIONS = (
    ('--- View Stat Graphs ---', '--- View Stat Graphs ---'),
    ('PPG', 'Points'),
    ('RPG', 'Rebounds'),
    ('APG', 'Assists'),
    ('BLKPG', 'Blocks'),
    ('STLPG', 'Steals'),
    ('FG_PCT', 'Field Goal %'),
    ('FG3_PCT', '3 Point %'),
    ('FT_PCT', 'Free Throw %'),
)


# form for searching a player
class PlayerSearchForm(forms.Form):
    player_name = forms.CharField(
        label='',
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Search a player',
                'class': 'form-control',
                'aria-label': 'Player Name'
            }
        ),
        error_messages={
            'required': 'Please enter a player name.',
            'max_length': 'Player name cannot exceed 100 characters.'
        }
    )


class TeamSearchForm(forms.Form):
    team_name = forms.CharField(
        label='',
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter a team',
                'class': 'form-control',
                'aria-label': 'Team Name'
            }
        ),
        error_messages={
            'required': 'Please enter the name or city of a NBA team.',
            'max_length': 'Team name cannot exceed 100 characters.'
        }
    )


# form for getting more stats
class StatsDropdownForm(forms.Form):
    option = forms.ChoiceField(choices=STAT_OPTIONS, label="Season Type", required=True, error_messages={'required':'Please select an option'})

# form for stats comparison


class StatsCompForm(forms.Form):
    option = forms.ChoiceField(choices=COMP_OPTIONS, label="", required=True, error_messages={'required':'Please select an option'})

    # this method will allow me to get the selected option's readable value to use for the graph's title
    def get_graph_title(self, selected_option):
        for dict_value, reader_value in COMP_OPTIONS:
            if dict_value == selected_option:
                title = reader_value

        return title



class PlayerCompareForm(forms.Form):
    player1 = forms.CharField(
        validators=[validators.MaxLengthValidator(50), validators.MinLengthValidator(1)],
        widget=forms.TextInput(attrs={'placeholder': 'Enter Player 1', 'style': 'width:300px'}))

    player2 = forms.CharField(
        validators=[validators.MaxLengthValidator(50), validators.MinLengthValidator(1)],
        widget=forms.TextInput(attrs={'placeholder': 'Enter Player 2', 'style': 'width:300px'}))


class PlayerGraphForm(forms.Form):
    career_category = forms.ChoiceField(label='Season Type', choices=STAT_OPTIONS, required=True, error_messages={'required':'Please select a category'})
    stat_option = forms.ChoiceField(choices=GRAPH_OPTIONS, label="Stat Category", required=True, error_messages={'required':'Please select a stat option'})

    # this method will allow me to get the selected option's readable value to use for the graph's title
    def get_graph_title(self, selected_option):
        for dict_value, reader_value in GRAPH_OPTIONS:
            if dict_value == selected_option:
                title = reader_value

        return title
    

class PlayerRegularGameLogForm(forms.Form):
    season = forms.ChoiceField(label='Regular Season', required=True, error_messages={'required':'Please select a season'})

    # To dynamically populate the season choices in the PlayerGameLogForm, we set the choices in the form's 
    # __init__ method. This allows us to pass the relevant player stats (or any data needed to 
    # determine the seasons) when instantiating the form.
    def __init__(self, *args, player_stats=None, **kwargs):
        super().__init__(*args, **kwargs)
        if player_stats is not None:
            seasons = self.get_player_seasons(player_stats)
            self.fields['season'].choices = [(s, s) for s in seasons]
        else:
           self.fields['season'].choices = [('No Regular Season Stats to display ☹️', 'No Regular Season Stats to display ☹️')]

    def get_player_seasons(self, player_stats):
        # Call the function to get the player's seasons
        seasons = get_years_played(player_stats)
        return seasons

class PlayerPlayoffsGameLogsForm(forms.Form):
    season = forms.ChoiceField(label='Playoff Season', required=True, error_messages={'required':'Please select a season'})

    # To dynamically populate the season choices in the PlayerPlayoffsGameLogsForm, we set the choices in the form's
    # __init__ method. This allows us to pass the relevant player stats (or any data needed to
    # determine the seasons) when instantiating the form.
    def __init__(self, *args, player_stats=None, **kwargs):
        super().__init__(*args, **kwargs)
        if player_stats is not None:
            seasons = self.get_player_seasons(player_stats)
            self.fields['season'].choices = [(s, s) for s in seasons]
        else:
           self.fields['season'].choices = [('No Playoff Stats to display ☹️', 'No Playoff Stats to display ☹️')]

    def get_player_seasons(self, player_stats):
        # Call the function to get the player's seasons
        seasons = get_years_played(player_stats)
        return seasons

class PlayerRegShotChartForm(forms.Form):
    season = forms.ChoiceField(label='Season', required=True, error_messages={'required':'Please select a season'})
    context_measure = forms.ChoiceField(label='Shot Category', choices=[('PTS', 'Points'), ('FGA', 'Field Goal Attempts'), ('FGM', 'Field Goals Made'), ('FG3M', '3 Point Makes'), ('FG3A', '3 Point Attempts'), ('TS_PCT', 'True Shooting Percentage'), ('PTS_OFF_TOV', 'Points off Turnovers'), ('PTS_2ND_CHANCE', '2nd Chance Points')], required=True, error_messages={'required':'Please select a context measure'})

    def __init__(self, *args, player_stats=None, **kwargs):
        super().__init__(*args, **kwargs)
        if player_stats is not None:
            seasons = self.get_player_seasons(player_stats)
            self.fields['season'].choices = [(s, s) for s in seasons]
        else:
           self.fields['season'].choices = [('None', 'Nothing to display')]

    def get_player_seasons(self, player_stats):
        # Call the function to get the player's seasons played
        seasons = get_years_played(player_stats)
        return seasons
