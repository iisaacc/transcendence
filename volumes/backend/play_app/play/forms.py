# from django import forms
# from django.core.exceptions import ValidationError
# from .models import Player
# import logging
# logger = logging.getLogger(__name__)

# class TournamentForm(forms.ModelForm):
#     player1_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
      
#     class Meta:
#         model = Tournament
#         fields = ['player1', 'player2', 'player3', 'player4']
#         widgets = {
#             'player1': forms.TextInput(attrs={
#                 'class': 'form-control', 'id': 'namePlayer1'
#             }),
#             'player2': forms.TextInput(attrs={
#                 'class': 'form-control', 'id': 'namePlayer2'
#             }),
#             'player3': forms.TextInput(attrs={
#                 'class': 'form-control', 'id': 'namePlayer3'
#             }),
#             'player4': forms.TextInput(attrs={
#                 'class': 'form-control', 'id': 'namePlayer4'
#             }),
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         logger.debug(f"TournamentForm > Cleaned data: {cleaned_data}")
#         player1_id = cleaned_data.get('player1_id')
#         player1_name = cleaned_data.get("player1")
#         player2_name = cleaned_data.get("player2")
#         player3_name = cleaned_data.get("player3")
#         player4_name = cleaned_data.get("player4")

#         players = [player1_name, player2_name, player3_name, player4_name]
#         logger.debug(f"TournamentForm > Players: {players}")
#         if len(players) != len(set(players)):
#             raise ValidationError("Player names must be unique.")

#         # Only Player1 can be registered for now
#         if player1_id:
#             player1 = Player.objects.create(user_id=player1_id, displayName=player1_name)
#         else:
#             player1 = Player.objects.create(displayName=player1_name)
#         player2 = Player.objects.create(displayName=player2_name)
#         player3 = Player.objects.create(displayName=player3_name)
#         player4 = Player.objects.create(displayName=player4_name)

#         cleaned_data['player1'] = player1
#         cleaned_data['player2'] = player2
#         cleaned_data['player3'] = player3
#         cleaned_data['player4'] = player4

#         return cleaned_data
