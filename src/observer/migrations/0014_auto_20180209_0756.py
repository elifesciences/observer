# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-09 07:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0013_auto_20180209_0611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlejson',
            name='ajson_type',
            field=models.CharField(choices=[('lax-ajson', 'lax article json'), ('elife-metrics-summary', 'elife-metrics summary data'), ('press-packages-id', 'presspackage summary data'), ('profiles-id', 'profiles')], max_length=25),
        ),
        migrations.AlterField(
            model_name='presspackage',
            name='updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
