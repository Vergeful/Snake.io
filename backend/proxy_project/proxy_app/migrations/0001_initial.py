# Generated by Django 5.1.6 on 2025-03-24 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('color', models.CharField(max_length=100)),
                ('speed', models.IntegerField(default=200)),
                ('score', models.IntegerField(default=0)),
            ],
        ),
    ]
