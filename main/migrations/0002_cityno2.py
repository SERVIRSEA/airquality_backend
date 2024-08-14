# Generated by Django 5.0.1 on 2024-08-09 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CityNO2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idc', models.IntegerField(default=False)),
                ('no2', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('init_date', models.DateField(default=False)),
                ('time', models.CharField(default=False)),
            ],
        ),
    ]
