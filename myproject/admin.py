"""
Customize Django admin site to use UnfoldAdmin for built-in models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin

# Unregister default admins
admin.site.unregister(User)
admin.site.unregister(Group)

# Register with UnfoldAdmin
@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    pass

@admin.register(Group)
class GroupAdmin(ModelAdmin, BaseGroupAdmin):
    pass

