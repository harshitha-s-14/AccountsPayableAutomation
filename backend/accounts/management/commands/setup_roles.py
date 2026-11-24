from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create the standard Accounts Payable application roles.'

    def handle(self, *args, **options):
        roles = ['AP_Clerk', 'Approver', 'Finance', 'Vendor_Manager', 'MANAGER']
        for role in roles:
            Group.objects.get_or_create(name=role)
        self.stdout.write(self.style.SUCCESS('Standard AP roles are ready.'))
