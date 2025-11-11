from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_feedback_questions(apps, schema_editor):
    FeedbackQuestion = apps.get_model('hotel_app', 'FeedbackQuestion')
    defaults = [
        (0, 'How was the room cleanliness during your stay?', 'rating'),
        (1, 'How would you rate our service quality?', 'rating'),
        (2, 'Do you have any additional comments or suggestions?', 'text'),
    ]
    for order, prompt, qtype in defaults:
        FeedbackQuestion.objects.get_or_create(
            prompt=prompt,
            defaults={
                'order': order,
                'question_type': qtype,
                'is_active': True,
            },
        )


def remove_seeded_feedback_questions(apps, schema_editor):
    FeedbackQuestion = apps.get_model('hotel_app', 'FeedbackQuestion')
    prompts = [
        'How was the room cleanliness during your stay?',
        'How would you rate our service quality?',
        'Do you have any additional comments or suggestions?',
    ]
    FeedbackQuestion.objects.filter(prompt__in=prompts).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hotel_app', '0007_remove_department_lead_alter_department_table'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='requesttype',
            name='default_department',
            field=models.ForeignKey(blank=True, help_text='Department that typically handles this request type.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default_request_types', to='hotel_app.department'),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='guest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='service_requests', to='hotel_app.guest'),
        ),
        migrations.AddField(
            model_name='servicerequest',
            name='source',
            field=models.CharField(choices=[('web', 'Web'), ('dashboard', 'Dashboard'), ('whatsapp', 'WhatsApp'), ('email', 'Email'), ('other', 'Other')], default='web', max_length=20),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='FeedbackQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField()),
                ('question_type', models.CharField(choices=[('rating', 'Rating (1-5)'), ('text', 'Free Text'), ('boolean', 'Yes / No')], default='text', max_length=20)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['order', 'id'],
                'db_table': 'feedback_question',
            },
        ),
        migrations.CreateModel(
            name='RequestKeyword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=100, unique=True)),
                ('weight', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('request_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='keywords', to='hotel_app.requesttype')),
            ],
            options={
                'ordering': ['keyword'],
                'db_table': 'request_keyword',
            },
        ),
        migrations.CreateModel(
            name='WhatsAppConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=32, unique=True)),
                ('current_state', models.CharField(choices=[('idle', 'Idle'), ('awaiting_menu_selection', 'Awaiting Menu Selection'), ('awaiting_request_description', 'Awaiting Request Description'), ('feedback_invited', 'Feedback Invited'), ('collecting_feedback', 'Collecting Feedback')], default='idle', max_length=48)),
                ('last_known_guest_status', models.CharField(choices=[('unknown', 'Unknown'), ('pre_checkin', 'Pre Check-in'), ('checked_in', 'Checked In'), ('checked_out', 'Checked Out')], default='unknown', max_length=32)),
                ('context', models.JSONField(blank=True, default=dict)),
                ('last_guest_message_at', models.DateTimeField(blank=True, null=True)),
                ('last_system_message_at', models.DateTimeField(blank=True, null=True)),
                ('menu_presented_at', models.DateTimeField(blank=True, null=True)),
                ('welcome_sent_at', models.DateTimeField(blank=True, null=True)),
                ('feedback_prompt_sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='whatsapp_conversations', to='hotel_app.guest')),
                ('voucher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='whatsapp_conversations', to='hotel_app.voucher')),
            ],
            options={
                'ordering': ['-updated_at'],
                'db_table': 'whatsapp_conversation',
            },
        ),
        migrations.CreateModel(
            name='FeedbackSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=16)),
                ('current_question_index', models.PositiveIntegerField(default=0)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feedback_sessions', to='hotel_app.booking')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback_sessions', to='hotel_app.whatsappconversation')),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feedback_sessions', to='hotel_app.guest')),
            ],
            options={
                'ordering': ['-created_at'],
                'db_table': 'feedback_session',
            },
        ),
        migrations.CreateModel(
            name='WhatsAppMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_sid', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('direction', models.CharField(choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')], max_length=16)),
                ('body', models.TextField(blank=True, null=True)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(blank=True, max_length=32, null=True)),
                ('sent_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('error', models.TextField(blank=True, null=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='hotel_app.whatsappconversation')),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='whatsapp_messages', to='hotel_app.guest')),
            ],
            options={
                'ordering': ['-sent_at'],
                'db_table': 'whatsapp_message',
            },
        ),
        migrations.CreateModel(
            name='UnmatchedRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=32)),
                ('message_body', models.TextField()),
                ('received_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('resolved', 'Resolved'), ('ignored', 'Ignored')], default='pending', max_length=16)),
                ('notes', models.TextField(blank=True, null=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('keywords', models.JSONField(blank=True, default=list)),
                ('source', models.CharField(default='whatsapp', max_length=32)),
                ('context', models.JSONField(blank=True, default=dict)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unmatched_requests', to='hotel_app.whatsappconversation')),
                ('created_ticket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='from_unmatched_requests', to='hotel_app.servicerequest')),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unmatched_requests', to='hotel_app.department')),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unmatched_requests', to='hotel_app.guest')),
                ('request_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unmatched_requests', to='hotel_app.requesttype')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_unmatched_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-received_at'],
                'db_table': 'unmatched_request',
            },
        ),
        migrations.CreateModel(
            name='FeedbackResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('received_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='hotel_app.feedbackquestion')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='hotel_app.feedbacksession')),
            ],
            options={
                'ordering': ['received_at'],
                'db_table': 'feedback_response',
            },
        ),
        migrations.AlterUniqueTogether(
            name='feedbackresponse',
            unique_together={('session', 'question')},
        ),
        migrations.RunPython(seed_feedback_questions, remove_seeded_feedback_questions),
    ]

