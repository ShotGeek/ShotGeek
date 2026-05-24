web: python manage.py runserver 0.0.0.0:$PORT
release: python manage.py migrate && python manage.py populate_nba_data && python manage.py populate_player_data && python manage.py import_box_scores
