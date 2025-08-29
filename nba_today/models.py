# from django.db import models


# # This class will store team logos in the database
# class TeamLogo(models.Model):
#     team_id = models.CharField(unique=True, max_length=50)
#     team_name = models.CharField(max_length=50)
#     team_full_name = models.CharField(max_length=50, default="N/A")
#     team_city = models.CharField(max_length=50, default="N/A")
#     logo_url = models.URLField()
#     team_colour = models.CharField(unique=False, max_length=50, default="#7E354D")
#
#     def __str__(self):
#         return f'{self.team_name}'
