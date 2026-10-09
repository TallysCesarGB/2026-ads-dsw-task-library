from django.contrib import admin
from .models import Author, Book, Category


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_authors', 'publication_year', 'is_available')
    list_filter = ('is_available', 'category')
    search_fields = ('title', 'authors__name')
    filter_horizontal = ('authors', 'category')

    @admin.display(description='Autores')
    def display_authors(self, obj):
        return ", ".join(a.name for a in obj.authors.all())


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'birth_year', 'nationality')
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    list_filter = ('code',)
    search_fields = ('name', 'code')