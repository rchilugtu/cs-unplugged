# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-28 05:20
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topics', '0057_auto_20170528_0519'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='learningoutcome',
            options={'ordering': ['curriculum_areas__number', 'text']},
        ),
    ]
