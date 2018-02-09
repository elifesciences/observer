# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-09 03:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0014_auto_20180209_0154'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='presspackage',
            name='idstr',
        ),
        migrations.AlterField(
            model_name='articlejson',
            name='msid',
            field=models.CharField(max_length=25),
        ),
        migrations.AlterField(
            model_name='presspackage',
            name='id',
            field=models.CharField(max_length=8, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='profile',
            name='orcid',
            field=models.CharField(blank=True, max_length=19, null=True),
        ),
    ]