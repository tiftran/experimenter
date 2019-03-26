# Generated by Django 2.1.7 on 2019-03-26 20:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("experiments", "0039_auto_20190326_2008")]

    operations = [
        migrations.AlterField(
            model_name="experiment",
            name="type",
            field=models.CharField(
                choices=[("pref", "Pref-Flip"), ("addon", "Add-On")],
                default="pref",
                max_length=255,
            ),
        )
    ]
