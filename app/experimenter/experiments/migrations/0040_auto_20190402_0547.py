# Generated by Django 2.1.7 on 2019-04-02 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("experiments", "0039_auto_20190327_1816")]

    operations = [
        migrations.AddField(
            model_name="experiment",
            name="public_description",
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name="experiment",
            name="public_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]