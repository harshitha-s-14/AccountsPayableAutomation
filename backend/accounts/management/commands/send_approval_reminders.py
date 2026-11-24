from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import ApprovalRequest, AuditLog


class Command(BaseCommand):
    help = 'Generate reminders for pending approvals'

    def handle(self, *args, **options):
        now = timezone.now()
        reminder_count = 0

        approvals = ApprovalRequest.objects.filter(
            status='PENDING'
        ).select_related('invoice')

        for approval in approvals:
            if now - approval.created_at < timedelta(hours=24):
                continue

            already_reminded = AuditLog.objects.filter(
                invoice=approval.invoice,
                action='Approval Reminder',
                description__contains=f'Approval {approval.id}'
            ).exists()

            if already_reminded:
                continue

            AuditLog.objects.create(
                invoice=approval.invoice,
                action='Approval Reminder',
                description=(
                    f'Reminder generated for pending approval '
                    f'{approval.id}, assigned to {approval.approver_role}.'
                ),
                performed_by='SYSTEM'
            )

            reminder_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{reminder_count} approval reminder(s) generated.'
            )
        )
