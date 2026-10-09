from django.contrib import admin
from .models import Author, Book, Category


class BookInline(admin.TabularInline):
    model = Book
    extra = 1
    fields = ('title', 'publication_year', 'is_available', 'category')
    show_change_link = True


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'birth_year', 'nationality')
    search_fields = ('name',)
    inlines = [BookInline]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publication_year', 'is_available')
    list_filter = ('is_available', 'category')
    search_fields = ('title', 'author__name')
    filter_horizontal = ('category',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    list_filter = ('code',)
    search_fields = ('name', 'code')