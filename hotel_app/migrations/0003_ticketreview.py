# Generated manually to create the ticket_review table
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('hotel_app', '0002_servicerequest_add_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guest_name', models.CharField(blank=True, max_length=120, null=True)),
                ('room_no', models.CharField(blank=True, max_length=50, null=True)),
                ('phone_number', models.CharField(db_index=True, max_length=50)),
                ('request_text', models.TextField(blank=True, null=True)),
                ('priority', models.CharField(default='normal', max_length=20)),
                ('match_confidence', models.FloatField(default=0.0)),
                ('is_matched', models.BooleanField(default=False)),
                ('review_status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    default='pending',
                    max_length=20
                )),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('moved_to_ticket', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('matched_department', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='hotel_app.department'
                )),
                ('matched_request_type', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='hotel_app.requesttype'
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL
                )),
                ('voucher', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='hotel_app.voucher'
                )),
            ],
            options={
                'db_table': 'ticket_review',
                'ordering': ['-created_at'],
            },
        ),
    ]
