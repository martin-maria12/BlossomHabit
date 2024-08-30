from .models import Avatar
# adauga avatarul tuturor template-urilor 
def avatar(request):
    if request.user.is_authenticated:
        avatar = Avatar.objects.filter(user=request.user).first()
        return {'avatar': avatar}
    return {}
