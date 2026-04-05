from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()

def create_system_user(username: str, password: str, role: str) -> User:
    """Service function to isolate business logic from HTTP mechanics."""
    if User.objects.filter(username=username).exists():
        raise ValidationError({"username": "This username is already taken."})
        
    user = User(username=username, role=role)
    user.set_password(password)
    user.save()
    return user

def toggle_user_status(user_id: str, is_active: bool, request_user) -> User:
    """Toggles active status, protecting admins from locking themselves out."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValidationError({"detail": "User not found."})
        
    if str(user.id) == str(request_user.id) and not is_active:
        raise ValidationError({"detail": "Admins cannot disable their own accounts."})
        
    user.is_active = is_active
    user.save(update_fields=['is_active'])
    return user
