# Generated by Django 3.0.6 on 2020-06-04 06:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0003_auto_20200530_1756'),
        ('audits', '0004_auto_20200604_0615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audit',
            name='board',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='boards.Board'),
        ),
    ]