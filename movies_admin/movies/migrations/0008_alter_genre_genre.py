# Generated by Django 3.2 on 2021-04-27 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0007_auto_20210426_2313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='genre',
            name='genre',
            field=models.CharField(max_length=255, unique=True, verbose_name='жанр'),
        ),
    ]
