# Generated by Django 3.1 on 2021-04-26 18:29

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0005_auto_20210425_2013'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filmwork',
            options={'verbose_name': 'кинопроизведение', 'verbose_name_plural': 'кинопроизведения'},
        ),
        migrations.AddField(
            model_name='genre',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='описание'),
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='creation_date',
            field=models.DateField(blank=True, null=True, verbose_name='дата выхода'),
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='описание'),
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='film_rating',
            field=models.CharField(blank=True, help_text='suitability for different age audience', max_length=32, null=True, verbose_name='возрастной рейтинг'),
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='film_type',
            field=models.CharField(blank=True, choices=[('tv_show', 'шоу'), ('movie', 'фильм'), ('series', 'сериал')], max_length=32, null=True, verbose_name='тип'),
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='imdb_rating',
            field=models.FloatField(blank=True, help_text='user ratings from IMDb', null=True, verbose_name='IMDb рейтинг'),
        ),
        migrations.AlterField(
            model_name='filmwork',
            name='title',
            field=models.CharField(max_length=255, verbose_name='название'),
        ),
        migrations.AlterField(
            model_name='filmworkgenre',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='genre',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='person',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='person',
            name='name',
            field=models.TextField(verbose_name='имя'),
        ),
    ]
