# Generated by Django 2.1.7 on 2019-03-26 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("experiments", "0038_experiment_risk_internal_only")]

    operations = [
        migrations.AlterField(
            model_name="experiment",
            name="analysis",
            field=models.TextField(
                blank=True,
                default="What is the main effect you are looking for and what data will\nyou use to make these decisions? What metrics are you using to measure success\n\nDo you plan on surveying users at the end of the experiment? Yes/No.\nStrategy and Insights can help create surveys if needed\n    ",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="objectives",
            field=models.TextField(
                blank=True,
                default="What is the objective of this experiment?  Explain in detail.",
                null=True,
            ),
        ),
    ]
