# Generated by Django 5.1.7 on 2025-04-12 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxy_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='size',
            field=models.IntegerField(default=40),
        ),
        migrations.AddField(
            model_name='player',
            name='x',
            field=models.IntegerField(default=400),
        ),
        migrations.AddField(
            model_name='player',
            name='y',
            field=models.IntegerField(default=300),
        ),
        migrations.AlterField(
            model_name='player',
            name='speed',
            field=models.IntegerField(default=150),
        ),
    ]
