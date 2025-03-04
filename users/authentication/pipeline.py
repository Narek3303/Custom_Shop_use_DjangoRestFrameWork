# from django.contrib.auth import get_user_model
#
# User = get_user_model()
#
# def verify_user(backend, user, response, *args, **kwargs):
#     """
#     Automatically set `is_verified=True` for users registering via social authentication.
#     """
#     if user and not user.is_verified:
#         user.is_verified = True
#         user.save()