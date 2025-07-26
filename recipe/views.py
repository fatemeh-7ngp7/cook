from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Recipe, Category, RecipeLike
import json


def home(request):
    """صفحه اصلی وب‌سایت"""
    # نمایش 6 دستور پخت جدید و محبوب
    featured_recipes = Recipe.objects.filter(
        is_published=True,
        is_featured=True
    ).order_by('-created_at')[:6]

    # اگر دستور پخت ویژه کمتر از 6 تا باشد، بقیه را از جدیدترین‌ها بگیر
    if featured_recipes.count() < 6:
        remaining_count = 6 - featured_recipes.count()
        other_recipes = Recipe.objects.filter(
            is_published=True
        ).exclude(
            id__in=featured_recipes.values_list('id', flat=True)
        ).order_by('-created_at')[:remaining_count]

        # ترکیب دو QuerySet
        recent_recipes = list(featured_recipes) + list(other_recipes)
    else:
        recent_recipes = featured_recipes

    context = {
        'recent_recipes': recent_recipes,
    }
    return render(request, 'recipe/home.html', context)


def food_list(request):
    """صفحه لیست غذاها"""
    # دریافت پارامترهای فیلتر از URL
    category_filter = request.GET.get('category', 'all')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'newest')

    # شروع با تمام دستور پخت‌های منتشر شده
    recipes = Recipe.objects.filter(is_published=True)

    # فیلتر بر اساس دسته‌بندی
    if category_filter != 'all':
        recipes = recipes.filter(category__name=category_filter)

    # فیلتر بر اساس جستجو
    if search_query:
        recipes = recipes.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(ingredients__name__icontains=search_query)
        ).distinct()

    # مرتب‌سازی
    if sort_by == 'newest':
        recipes = recipes.order_by('-created_at')
    elif sort_by == 'oldest':
        recipes = recipes.order_by('created_at')
    elif sort_by == 'popular':
        # مرتب‌سازی بر اساس تعداد لایک
        recipes = recipes.order_by('-id')  # فعلاً بر اساس ID، بعداً می‌توان بر اساس لایک مرتب کرد
    elif sort_by == 'time_asc':
        recipes = recipes.order_by('prep_time', 'cook_time')
    elif sort_by == 'time_desc':
        recipes = recipes.order_by('-prep_time', '-cook_time')

    # صفحه‌بندی
    paginator = Paginator(recipes, 12)  # 12 دستور پخت در هر صفحه
    page_number = request.GET.get('page')
    page_recipes = paginator.get_page(page_number)

    # دریافت تمام دسته‌بندی‌ها برای فیلتر
    categories = Category.objects.all().order_by('display_name')

    context = {
        'recipes': page_recipes,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
        'current_sort': sort_by,
    }
    return render(request, 'recipe/food_list.html', context)


def food_recipe(request, slug):
    """صفحه نمایش جزئیات یک دستور پخت"""
    recipe = get_object_or_404(Recipe, slug=slug, is_published=True)

    # دریافت مواد اولیه مرتب شده
    ingredients = recipe.ingredients.all().order_by('order')

    # دریافت مراحل طرز تهیه مرتب شده
    steps = recipe.steps.all().order_by('step_number')

    # دریافت اطلاعات تغذیه‌ای
    nutrition_info = getattr(recipe, 'nutrition', None)

    # دستور پخت‌های مشابه (از همان دسته‌بندی)
    related_recipes = Recipe.objects.filter(
        category=recipe.category,
        is_published=True
    ).exclude(id=recipe.id)[:4]

    # بررسی اینکه آیا کاربر قبلاً امتیاز داده یا نه
    user_ip = get_client_ip(request)
    user_vote = None
    try:
        user_like = RecipeLike.objects.get(recipe=recipe, user_ip=user_ip)
        user_vote = 'like' if user_like.is_like else 'dislike'
    except RecipeLike.DoesNotExist:
        pass

    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'steps': steps,
        'nutrition_info': nutrition_info,
        'related_recipes': related_recipes,
        'user_vote': user_vote,
    }
    return render(request, 'recipe/food_recipe.html', context)


@csrf_exempt
def toggle_like(request):
    """API برای لایک/دیسلایک کردن دستور پخت"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recipe_id = data.get('recipe_id')
            action = data.get('action')  # 'like' or 'dislike'

            recipe = get_object_or_404(Recipe, id=recipe_id, is_published=True)
            user_ip = get_client_ip(request)

            # بررسی اینکه آیا کاربر قبلاً امتیاز داده
            try:
                existing_like = RecipeLike.objects.get(recipe=recipe, user_ip=user_ip)

                # اگر همان امتیاز را دوباره کلیک کرد، امتیاز را حذف کن
                if (existing_like.is_like and action == 'like') or (not existing_like.is_like and action == 'dislike'):
                    existing_like.delete()
                    removed = True
                else:
                    # تغییر امتیاز
                    existing_like.is_like = (action == 'like')
                    existing_like.save()
                    removed = False

            except RecipeLike.DoesNotExist:
                # ایجاد امتیاز جدید
                RecipeLike.objects.create(
                    recipe=recipe,
                    user_ip=user_ip,
                    is_like=(action == 'like')
                )
                removed = False

            # بازگرداندن تعداد جدید لایک و دیسلایک
            total_likes = recipe.total_likes
            total_dislikes = recipe.total_dislikes

            return JsonResponse({
                'success': True,
                'likes': total_likes,
                'dislikes': total_dislikes,
                'removed': removed
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_client_ip(request):
    """دریافت IP کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def search_recipes(request):
    """API جستجوی دستور پخت‌ها"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'recipes': []})

    recipes = Recipe.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query),
        is_published=True
    )[:10]

    results = []
    for recipe in recipes:
        results.append({
            'id': recipe.id,
            'title': recipe.title,
            'slug': recipe.slug,
            'image_url': recipe.image.url if recipe.image else '',
            'category': recipe.category.display_name,
            'prep_time': recipe.total_time,
            'servings': recipe.servings,
        })

    return JsonResponse({'recipes': results})


def filter_recipes(request):
    """API فیلتر کردن دستور پخت‌ها"""
    category = request.GET.get('category', 'all')
    difficulty = request.GET.get('difficulty', 'all')
    max_time = request.GET.get('max_time', '')

    recipes = Recipe.objects.filter(is_published=True)

    if category != 'all':
        recipes = recipes.filter(category__name=category)

    if difficulty != 'all':
        recipes = recipes.filter(difficulty=difficulty)

    if max_time:
        try:
            max_time = int(max_time)
            recipes = recipes.extra(
                where=["prep_time + cook_time <= %s"],
                params=[max_time]
            )
        except ValueError:
            pass

    recipes_data = []
    for recipe in recipes[:20]:  # محدود به 20 نتیجه
        recipes_data.append({
            'id': recipe.id,
            'title': recipe.title,
            'slug': recipe.slug,
            'image_url': recipe.image.url if recipe.image else '',
            'category': recipe.category.display_name,
            'difficulty': recipe.get_difficulty_display(),
            'prep_time': recipe.total_time,
            'servings': recipe.servings,
            'calories': recipe.calories_per_serving,
            'likes': recipe.total_likes,
            'dislikes': recipe.total_dislikes,
        })

    return JsonResponse({'recipes': recipes_data})