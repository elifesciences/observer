# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-28 02:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0006_auto_20170425_0146'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='articlejson',
            options={'ordering': ('-msid', 'version')},
        ),
    ]
