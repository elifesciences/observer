# Generated by Django 2.2.16 on 2020-10-20 01:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0017_auto_20201020_0110'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rawjson',
            old_name='ajson',
            new_name='json',
        ),
        migrations.RenameField(
            model_name='rawjson',
            old_name='ajson_type',
            new_name='json_type',
        ),
    ]
