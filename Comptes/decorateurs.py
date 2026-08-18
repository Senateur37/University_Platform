# accounts/decorators.py
from django.core.exceptions import PermissionDenied

def user_type_required(*allowed_types):
    def decorator(view_func):
        def _wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.is_superuser or request.user.is_staff or request.user.user_type in allowed_types:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapper
    return decorator