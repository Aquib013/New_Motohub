from django.contrib import admin


class ServiceAdmin(admin.ModelAdmin):
    list_display = ["job", "service_type", "description"]
    search_fields = ["job", "description"]
