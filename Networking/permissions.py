from rest_framework.permissions import BasePermission

class IsReadOnly(BasePermission):
    """
    Allows access only to users with 'read' or higher roles.
    """
    def has_permission(self, request, view):
        return request.user.role in ['read', 'write', 'admin']

class IsWriter(BasePermission):
    """
    Allows access only to users with 'write' or 'admin' roles.
    """
    def has_permission(self, request, view):
        return request.user.role in ['write', 'admin']

class IsAdmin(BasePermission):
    """
    Allows access only to users with 'admin' role.
    """
    def has_permission(self, request, view):
        return request.user.role == 'admin'
