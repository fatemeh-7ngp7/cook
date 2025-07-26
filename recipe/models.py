from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Category(models.Model):
    """دسته‌بندی دستور پخت‌ها"""
    CATEGORY_CHOICES = [
        ('main', 'غذاهای اصلی'),
        ('dessert', 'دسرها'),
        ('appetizer', 'پیش غذا'),
        ('drink', 'نوشیدنی‌ها'),
        ('soup', 'سوپ و آش'),
        ('salad', 'سالاد'),
    ]

    name = models.CharField('نام دسته‌بندی', max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField('نام نمایشی', max_length=100)
    description = models.TextField('توضیحات', blank=True, null=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['display_name']

    def __str__(self):
        return self.display_name


class Recipe(models.Model):
    """مدل اصلی دستور پخت"""
    DIFFICULTY_CHOICES = [
        ('easy', 'آسان'),
        ('medium', 'متوسط'),
        ('hard', 'سخت'),
    ]

    title = models.CharField('عنوان دستور پخت', max_length=200)
    slug = models.SlugField('نامک', max_length=200, unique=True, allow_unicode=True)
    description = models.TextField('توضیح کوتاه', max_length=500)
    image = models.ImageField('تصویر اصلی', upload_to='recipes/images/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='دسته‌بندی')

    # اطلاعات پخت
    prep_time = models.PositiveIntegerField('زمان آماده‌سازی (دقیقه)')
    cook_time = models.PositiveIntegerField('زمان پخت (دقیقه)')
    servings = models.PositiveIntegerField('تعداد نفرات')
    calories_per_serving = models.PositiveIntegerField('کالری به ازای هر نفر')
    difficulty = models.CharField('سطح سختی', max_length=10, choices=DIFFICULTY_CHOICES)

    # محتوای دستور پخت
    instructions = models.TextField('طرز تهیه')

    # تنظیمات
    is_featured = models.BooleanField('پیشنهاد ویژه', default=False)
    is_published = models.BooleanField('منتشر شده', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)

    class Meta:
        verbose_name = 'دستور پخت'
        verbose_name_plural = 'دستور پخت‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('food_recipe', kwargs={'slug': self.slug})

    @property
    def total_time(self):
        """زمان کل پخت"""
        return self.prep_time + self.cook_time

    @property
    def total_likes(self):
        """تعداد کل لایک‌ها"""
        return self.likes.filter(is_like=True).count()

    @property
    def total_dislikes(self):
        """تعداد کل دیسلایک‌ها"""
        return self.likes.filter(is_like=False).count()


class Ingredient(models.Model):
    """مواد اولیه مورد نیاز برای دستور پخت"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients', verbose_name='دستور پخت')
    name = models.CharField('نام ماده اولیه', max_length=100)
    amount = models.CharField('مقدار', max_length=50)
    unit = models.CharField('واحد', max_length=20, blank=True)
    notes = models.CharField('یادداشت', max_length=200, blank=True)
    order = models.PositiveIntegerField('ترتیب', default=1)

    class Meta:
        verbose_name = 'ماده اولیه'
        verbose_name_plural = 'مواد اولیه'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.recipe.title} - {self.name}"


class RecipeStep(models.Model):
    """مراحل طرز تهیه"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps', verbose_name='دستور پخت')
    step_number = models.PositiveIntegerField('شماره مرحله')
    instruction = models.TextField('توضیحات مرحله')
    image = models.ImageField('تصویر مرحله', upload_to='recipes/steps/', blank=True, null=True)

    class Meta:
        verbose_name = 'مرحله طرز تهیه'
        verbose_name_plural = 'مراحل طرز تهیه'
        ordering = ['step_number']
        unique_together = ['recipe', 'step_number']

    def __str__(self):
        return f"{self.recipe.title} - مرحله {self.step_number}"


class RecipeLike(models.Model):
    """لایک و دیسلایک دستور پخت‌ها"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='likes', verbose_name='دستور پخت')
    user_ip = models.GenericIPAddressField('آی‌پی کاربر')
    is_like = models.BooleanField('لایک است')  # True برای لایک، False برای دیسلایک
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'امتیاز دستور پخت'
        verbose_name_plural = 'امتیازات دستور پخت‌ها'
        unique_together = ['recipe', 'user_ip']  # هر IP فقط یک بار می‌تواند امتیاز دهد

    def __str__(self):
        action = 'لایک' if self.is_like else 'دیسلایک'
        return f"{self.recipe.title} - {action}"


class NutritionInfo(models.Model):
    """اطلاعات تغذیه‌ای دستور پخت"""
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE, related_name='nutrition', verbose_name='دستور پخت')
    calories = models.PositiveIntegerField('کالری', default=0)
    protein = models.FloatField('پروتئین (گرم)', default=0)
    carbs = models.FloatField('کربوهیدرات (گرم)', default=0)
    fat = models.FloatField('چربی (گرم)', default=0)
    fiber = models.FloatField('فیبر (گرم)', default=0)
    sugar = models.FloatField('قند (گرم)', default=0)
    sodium = models.FloatField('سدیم (میلی‌گرم)', default=0)

    class Meta:
        verbose_name = 'اطلاعات تغذیه‌ای'
        verbose_name_plural = 'اطلاعات تغذیه‌ای'

    def __str__(self):
        return f"اطلاعات تغذیه‌ای {self.recipe.title}"