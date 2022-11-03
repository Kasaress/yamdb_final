from django.contrib import admin

from .models import Category, Comment, Genre, Review, Title


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'text', 'score')
    search_fields = ('title',)
    list_filter = ('score',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('review', 'text')
    search_fields = ('review',)


class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


class TabularInlineGenre(admin.TabularInline):
    model = Genre.titles.through


class TitleAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'year', 'description', 'get_genres')
    search_fields = ('name', 'category', 'year')
    list_filter = ('category', 'genre')
    inlines = (TabularInlineGenre, )

    def get_genres(self, title):
        return ', '.join(genre.name for genre in title.genre.all())

    get_genres.short_description = 'Жанры'


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)


admin.site.register(Review, ReviewAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Title, TitleAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Category, CategoryAdmin)
