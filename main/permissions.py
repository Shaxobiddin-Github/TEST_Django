from rest_framework import permissions

# Admin uchun ruxsat
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

# O‘qituvchi uchun ruxsat
class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'

# Controller uchun ruxsat
class IsController(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'controller'

# Talaba uchun ruxsat
class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'
    

# Yangi: Bir nechta rollarni tekshirish
class HasMultipleRoles(permissions.BasePermission):
    def __init__(self, allowed_roles=None):
        self.allowed_roles = allowed_roles or []

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in self.allowed_roles