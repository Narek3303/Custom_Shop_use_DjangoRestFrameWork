from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from authemail.admin import EmailUserAdmin




CustomUser = get_user_model()


class CustomUserAdmin(EmailUserAdmin):
        fieldsets = (
            (None, {'fields': ('email', 'password')}),
            ('Personal Info', {'fields': ('first_name', 'last_name')}),
            ('Permissions', {'fields': ('is_active', 'is_staff',
                                        'is_superuser', 'is_verified',
                                        'groups', 'user_permissions')}),
            ('Important dates', {'fields': ('last_login', 'date_joined')}),
            ('Custom info', {'fields': ('date_of_birth',)}),
        )

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), CustomUserAdmin)