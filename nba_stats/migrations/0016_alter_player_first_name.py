# Fix negative substring length for single-name players (e.g. "Nene").
# StrIndex returns 0 when there is no space, making the old expression
# produce length -1, which PostgreSQL rejects.
# Django does not support AlterField on GeneratedFields, so we remove and re-add.

import django.db.models.expressions
import django.db.models.functions.comparison
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nba_stats", "0015_alter_playerbio_position"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="player",
            name="first_name",
        ),
        migrations.AddField(
            model_name="player",
            name="first_name",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    django.db.models.functions.comparison.NullIf(
                        django.db.models.functions.text.Substr(
                            "full_name",
                            1,
                            django.db.models.functions.comparison.Greatest(
                                django.db.models.expressions.CombinedExpression(
                                    django.db.models.functions.text.StrIndex(
                                        "full_name", models.Value(" ")
                                    ),
                                    "-",
                                    models.Value(1),
                                ),
                                models.Value(0),
                            ),
                        ),
                        models.Value(""),
                    ),
                    django.db.models.expressions.F("full_name"),
                    output_field=models.CharField(max_length=100),
                ),
                output_field=models.CharField(max_length=100),
            ),
        ),
    ]
