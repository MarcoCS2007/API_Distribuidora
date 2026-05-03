# Generated manually: campo `ativo` em UsuarioBase para alinhar soft-delete aos demais modelos

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuariobase',
            name='ativo',
            field=models.BooleanField(default=True),
        ),
    ]
