# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-10-18 04:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0007_auto_20170428_0258'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='subject1',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='subject2',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='subject3',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
