# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-07 07:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0012_auto_20180122_0528'),
    ]

    operations = [
        migrations.CreateModel(
            name='PressPackage',
            fields=[
                ('id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('idstr', models.CharField(help_text='original stringified hex id of press package', max_length=8, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('published', models.DateTimeField()),
                ('updated', models.DateTimeField()),
                ('subjects', models.ManyToManyField(blank=True, help_text='subjects this press package mentions directly', to='observer.Subject')),
            ],
        ),
        migrations.AlterField(
            model_name='articlejson',
            name='ajson_type',
            field=models.CharField(choices=[('lax-ajson', 'lax article json'), ('elife-metrics-summary', 'elife-metrics summary data'), ('presspackage-id', 'presspackage summary data')], max_length=25),
        ),
    ]