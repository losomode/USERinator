from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_userprofile_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='marked_for_deletion',
            field=models.BooleanField(
                default=False,
                help_text='User has been flagged for permanent deletion by a manager/admin. Platform admins review and delete.',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='marked_for_deletion_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When the user was marked for deletion.',
            ),
        ),
    ]
