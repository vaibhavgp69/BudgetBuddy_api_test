# Generated by Django 4.2.9 on 2024-02-03 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_transaction_t_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="phonenumber",
            field=models.CharField(max_length=13, unique=True),
        ),
    ]