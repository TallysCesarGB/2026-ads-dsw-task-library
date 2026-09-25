from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publication_year', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('title', 'author')