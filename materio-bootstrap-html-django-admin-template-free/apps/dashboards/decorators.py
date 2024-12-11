from django.contrib.auth.decorators import login_required

def login_required_custom(func):
    @login_required
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
