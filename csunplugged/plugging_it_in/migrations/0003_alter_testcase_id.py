# Generated by Django 3.2.7 on 2021-09-29 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugging_it_in', '0002_auto_20200511_0227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
