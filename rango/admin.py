from django.contrib import admin

from rango.models import Category, Page


# Register your models here.
class PageInline(admin.TabularInline):
    model = Page
    extra = 3

class CategoryAdmin(admin.ModelAdmin):
    list_display=('name', 'views', 'likes')
    list_filter = ['views']
    inlines = [PageInline]

admin.site.register(Category, CategoryAdmin)
admin.site.register(Page)