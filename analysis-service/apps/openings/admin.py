from django.contrib import admin
from .models import Opening


@admin.register(Opening)
class OpeningAdmin(admin.ModelAdmin):
    list_display = ["eco", "name", "popularity"]
    list_filter = ["eco"]
    search_fields = ["name", "eco"]
