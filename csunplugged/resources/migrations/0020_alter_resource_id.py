# Generated by Django 3.2.7 on 2021-09-29 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0019_auto_20210215_0343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
