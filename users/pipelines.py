def verify_email(backend, user, response, *args, **kwargs):
    """
    Եթե user-ը social login-ով է գրանցվել, ապա նրան հաստատված ենք համարում։
    """
    if user and not user.is_verified:
        user.is_verified = True
        user.save()