from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    """
    Base permission class for Accounts Payable application roles.
    """

    allowed_roles = []

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Superuser has complete access.
        if user.is_superuser:
            return True

        # Check the user's assigned Django groups.
        return user.groups.filter(
            name__in=self.allowed_roles
        ).exists()


class IsAdmin(RolePermission):
    allowed_roles = []


class IsAPClerk(RolePermission):
    allowed_roles = ['AP_Clerk']


class IsApprover(RolePermission):
    allowed_roles = ['Approver']


class IsFinance(RolePermission):
    allowed_roles = ['Finance']


class IsVendorManager(RolePermission):
    allowed_roles = ['Vendor_Manager']


class IsAPClerkOrApprover(RolePermission):
    allowed_roles = ['AP_Clerk', 'Approver']


class IsAPClerkOrFinance(RolePermission):
    allowed_roles = ['AP_Clerk', 'Finance']


class IsAllEmployees(RolePermission):
    allowed_roles = [
        'AP_Clerk',
        'Approver',
        'Finance',
        'Vendor_Manager',
        'MANAGER'
    ]
class IsManager(RolePermission):
    allowed_roles = ['MANAGER']