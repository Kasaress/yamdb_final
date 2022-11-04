from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from reviews.validators import validate_slug, validate_year
from users.models import CustomUser as User


class GenreCategory(models.Model):
    name = models.CharField(
        max_length=settings.NAME_LENGTH,
    )
    slug = models.SlugField(
        max_length=settings.SLUG_LENGTH,
        unique=True,
        validators=[validate_slug, ]
    )

    class Meta:
        abstract = True
        ordering = ['-id']

    def __str__(self):
        return self.name


class Genre(GenreCategory):
    """Жанры произведений."""
    class Meta(GenreCategory.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Category(GenreCategory):
    """Категории произведение."""
    class Meta(GenreCategory.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Title(models.Model):
    """Произведения."""
    name = models.CharField(
        max_length=settings.NAME_LENGTH,
        verbose_name='Название'
    )
    year = models.PositiveIntegerField(
        validators=[validate_year],
        verbose_name='Год выпуска',
        db_index=True
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
        blank=True,
        null=True,
        help_text='Выберите категорию',
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        verbose_name='Жанры',
        help_text='Выберите жанр'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('name',)
        default_related_name = 'titles'

    def __str__(self):
        return self.name


class GenreTitle(models.Model):
    """Произведения-Жанры."""
    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        blank=True,
        null=True)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.genre}{self.title}'


class ParentingModel(models.Model):
    text = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:settings.SHORT_TEXT_LENGTH]


class Review(ParentingModel):
    """Отзывы."""
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(settings.MIN_SCORE),
                    MaxValueValidator(settings.MAX_SCORE)],
        error_messages={
            'validators': f'Поставьте оценку от '
                          f'{settings.MIN_SCORE} до {settings.MAX_SCORE}'
        },
        default=(
            (settings.MAX_SCORE - settings.MIN_SCORE) // 2 + settings.MIN_SCORE
        )
    )

    class Meta(ParentingModel.Meta):
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        default_related_name = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=('title', 'author',),
                name='unique review'
            )]


class Comment(ParentingModel):
    """Комментарии."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
    )

    class Meta(ParentingModel.Meta):
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'
