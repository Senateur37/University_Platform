# accounts/decorators.py
from django.core.exceptions import PermissionDenied

def user_type_required(*allowed_types):
    def decorator(view_func):
        def _wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.user_type not in allowed_types:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapper
    return decorator