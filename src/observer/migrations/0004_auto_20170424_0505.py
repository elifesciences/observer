# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-24 05:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0003_auto_20170424_0256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlejson',
            name='msid',
            field=models.PositiveSmallIntegerField(),
        ),
    ]
