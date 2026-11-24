from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import ApprovalRequest, AuditLog


class Command(BaseCommand):
    help = 'Escalate overdue pending approval requests'

    def handle(self, *args, **options):
        now = timezone.now()

        approvals = ApprovalRequest.objects.filter(
            status='PENDING',
            is_escalated=False,
            approval_rule__isnull=False
        ).select_related('invoice', 'approval_rule')

        escalated_count = 0

        for approval in approvals:
            rule = approval.approval_rule
            deadline = approval.created_at + timedelta(
                hours=rule.escalation_after_hours
            )

            if now >= deadline:
                old_role = approval.approver_role
                new_role = rule.escalation_role or 'MANAGER'

                approval.original_approver_role = old_role
                approval.approver_role = new_role
                approval.is_escalated = True
                approval.escalated_at = now

                approval.save(update_fields=[
                    'original_approver_role',
                    'approver_role',
                    'is_escalated',
                    'escalated_at',
                    'updated_at'
                ])

                AuditLog.objects.create(
                    invoice=approval.invoice,
                    action='Approval Escalated',
                    description=(
                        f'Approval {approval.id} escalated '
                        f'from {old_role} to {new_role}.'
                    ),
                    performed_by='SYSTEM'
                )

                escalated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Escalation completed. {escalated_count} approval(s) escalated.'
            )
        )
