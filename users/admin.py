from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from authemail.admin import EmailUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import UserProfile

CustomUser = get_user_model()


class UserProfileInline(admin.StackedInline):
    """UserProfile-ի inline ադմին՝ User ադմինում պրոֆիլի տվյալները ցույց տալու համար"""

    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Պրոֆիլ')
    fields = (
        'avatar_preview',
        'phone_number',
        'address',
        'city',
        'country',
        'postal_code',

    )
    readonly_fields = ('avatar_preview',)

    def avatar_preview(self, instance):
        """Ավատարի նախադիտում"""
        if instance.avatar:
            return format_html('<img src="{}" width="150" height="150" style="object-fit: cover;"/>',
                               instance.avatar.url)
        return _("Ավատար չկա")

    avatar_preview.short_description = _('Ավատարի նախադիտում')


class CustomUserAdmin(EmailUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Անձնական տվյալներ'), {'fields': ('first_name', 'last_name', 'date_of_birth')}),
        (_('Անվանարգեր'), {'fields': ('is_active', 'is_staff',
                                      'is_superuser', 'is_verified',
                                      'groups', 'user_permissions')}),
        (_('Կարևոր ամսաթվեր'), {'fields': ('last_login', 'date_joined')}),
    )

    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_verified', 'is_staff', 'profile_completeness')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_verified', )

    def profile_completeness(self, obj):
        """Ստուգում է պրոֆիլի լրիվ լինելը"""
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.is_complete_profile()
        return False

    profile_completeness.boolean = True
    profile_completeness.short_description = _('Ամբողջական պրոֆիլ')



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """UserProfile մոդելի հատուկ ադմին"""

    list_display = ('user', 'phone_number',  'avatar_thumbnail', 'profile_completeness', 'created_at')
    list_filter = ('country', 'city', 'created_at')
    search_fields = ('user__email', 'phone_number', 'address', 'postal_code', 'user__first_name', 'user__last_name')
    readonly_fields = ('avatar_thumbnail', 'created_at', 'updated_at')

    fieldsets = (
        (_('Օգտատիրոջ տվյալներ'), {
            'fields': ('user', 'avatar', 'avatar_thumbnail', 'birth_date')
        }),
        (_('Կոնտակտային տվյալներ'), {
            'fields': ('phone_number',)
        }),
        (_('Հասցե'), {
            'fields': ('address', 'city', 'country', 'postal_code')
        }),
        (_('Մետատվյալներ'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def avatar_thumbnail(self, obj):
        """Ավատարի փոքր նկար"""
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;"/>', obj.avatar.url)
        return _("Ավատար չկա")

    avatar_thumbnail.short_description = _('Ավատար')

    def profile_completeness(self, obj):
        """Պրոֆիլի լրիվ լինելու ստուգում"""
        return obj.is_complete_profile()

    profile_completeness.boolean = True
    profile_completeness.short_description = _('Ամբողջական պրոֆիլ')

    def get_queryset(self, request):
        """Հարցում՝ ներառելով with_phone մեթոդը"""
        qs = super().get_queryset(request)
        if hasattr(qs, 'with_phone'):
            return qs.select_related('user').with_phone()
        return qs.select_related('user')


# Գրանցում և վերագրանցում CustomUser-ի համար
admin.site.unregister(CustomUser)
admin.site.register(CustomUser, CustomUserAdmin)
