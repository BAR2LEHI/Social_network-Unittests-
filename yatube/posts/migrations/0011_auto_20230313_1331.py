# Generated by Django 2.2.16 on 2023-03-13 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20230311_1426'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='Подписка один раз'),
        ),
    ]
