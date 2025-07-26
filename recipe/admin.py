from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Recipe, Ingredient, RecipeStep, RecipeLike, NutritionInfo


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['display_name', 'name']
    ordering = ['display_name']


class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 5
    fields = ['name', 'amount', 'unit', 'notes', 'order']
    ordering = ['order']


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 3
    fields = ['step_number', 'instruction', 'image']
    ordering = ['step_number']


class NutritionInfoInline(admin.StackedInline):
    model = NutritionInfo
    max_num = 1
    fields = [
        ('calories', 'protein'),
        ('carbs', 'fat'),
        ('fiber', 'sugar'),
        'sodium'
    ]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'difficulty',
        'total_time_display',
        'servings',
        'image_preview',
        'is_featured',
        'is_published',
        'likes_count',
        'created_at'
    ]
    list_filter = [
        'category',
        'difficulty',
        'is_featured',
        'is_published',
        'created_at'
    ]
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_featured', 'is_published']
    readonly_fields = ['created_at', 'updated_at', 'likes_count', 'dislikes_count']
    ordering = ['-created_at']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'slug', 'description', 'image', 'category')
        }),
        ('اطلاعات پخت', {
            'fields': (
                ('prep_time', 'cook_time'),
                ('servings', 'calories_per_serving'),
                'difficulty'
            )
        }),
        ('محتوا', {
            'fields': ('instructions',)
        }),
        ('تنظیمات', {
            'fields': ('is_featured', 'is_published')
        }),
        ('آمار', {
            'fields': ('likes_count', 'dislikes_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    inlines = [IngredientInline, RecipeStepInline, NutritionInfoInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return "بدون تصویر"

    image_preview.short_description = 'تصویر'

    def total_time_display(self, obj):
        total = obj.total_time
        hours = total // 60
        minutes = total % 60
        if hours > 0:
            return f"{hours} ساعت و {minutes} دقیقه"
        return f"{minutes} دقیقه"

    total_time_display.short_description = 'زمان کل'

    def likes_count(self, obj):
        return obj.total_likes

    likes_count.short_description = 'تعداد لایک'

    def dislikes_count(self, obj):
        return obj.total_dislikes

    dislikes_count.short_description = 'تعداد دیسلایک'

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'recipe', 'amount', 'unit', 'order']
    list_filter = ['recipe__category', 'unit']
    search_fields = ['name', 'recipe__title']
    ordering = ['recipe', 'order']

    autocomplete_fields = ['recipe']


@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'step_number', 'instruction_preview', 'has_image']
    list_filter = ['recipe__category']
    search_fields = ['recipe__title', 'instruction']
    ordering = ['recipe', 'step_number']

    def instruction_preview(self, obj):
        if len(obj.instruction) > 50:
            return obj.instruction[:50] + '...'
        return obj.instruction

    instruction_preview.short_description = 'توضیحات'

    def has_image(self, obj):
        return '✅' if obj.image else '❌'

    has_image.short_description = 'تصویر'


@admin.register(RecipeLike)
class RecipeLikeAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'user_ip', 'is_like_display', 'created_at']
    list_filter = ['is_like', 'created_at', 'recipe__category']
    search_fields = ['recipe__title', 'user_ip']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def is_like_display(self, obj):
        if obj.is_like:
            return format_html('<span style="color: green;">👍 لایک</span>')
        else:
            return format_html('<span style="color: red;">👎 دیسلایک</span>')

    is_like_display.short_description = 'نوع امتیاز'


@admin.register(NutritionInfo)
class NutritionInfoAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'calories', 'protein', 'carbs', 'fat']
    search_fields = ['recipe__title']
    ordering = ['recipe']


# تنظیمات کلی پنل ادمین
admin.site.site_header = "پنل مدیریت آشپزی سالم"
admin.site.site_title = "آشپزی سالم"
admin.site.index_title = "مدیریت محتوای وب‌سایت"