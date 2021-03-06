# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-14 23:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0009_auto_20180109_0335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='msid',
            field=models.BigIntegerField(help_text='article identifier from beginning of submission process right through to end of publication.', unique=True),
        ),
        migrations.AlterField(
            model_name='articlejson',
            name='msid',
            field=models.BigIntegerField(),
        ),
    ]
