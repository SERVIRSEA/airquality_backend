# Generated by Django 5.0.1 on 2024-06-18 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_alter_citypm25_forecast_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='citypm25',
            name='forecast_time',
            field=models.CharField(default=False),
        ),
        migrations.AlterField(
            model_name='citypm25',
            name='init_date',
            field=models.DateField(default=False),
        ),
    ]
