# Generated by Django 2.2 on 2020-08-01 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0007_book_book_seller_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='user_image',
            field=models.ImageField(default='', upload_to='images/'),
        ),
    ]
