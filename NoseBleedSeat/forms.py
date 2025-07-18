from django import forms


class PlayerOneForm(forms.Form):
    player1_name = forms.CharField(
        label='',
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Search player 1',
                'class': 'form-control',
                'aria-label': 'Player Name'
            }
        ),
        error_messages={
            'required': 'Please enter a player name.',
            'max_length': 'Player name cannot exceed 100 characters.'
        }
    )

class PlayerTwoForm(forms.Form):
    player2_name = forms.CharField(
        label='',
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Search player 2',
                'class': 'form-control',
                'aria-label': 'Player Name'
            }
        ),
        error_messages={
            'required': 'Please enter a player name.',
            'max_length': 'Player name cannot exceed 100 characters.'
        }
    )
