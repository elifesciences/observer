# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-24 02:56
from __future__ import unicode_literals

import annoying.fields
import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('observer', '0002_auto_20170421_0935'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleJSON',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveSmallIntegerField()),
                ('ajson', annoying.fields.JSONField()),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='datetime_record_created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2017, 4, 24, 2, 56, 47, 243639)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='article',
            name='datetime_record_updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='articlejson',
            name='msid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='observer.Article', to_field='msid'),
        ),
        migrations.AlterUniqueTogether(
            name='articlejson',
            unique_together=set([('msid', 'version')]),
        ),
    ]
