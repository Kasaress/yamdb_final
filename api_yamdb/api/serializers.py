import datetime as dt

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from reviews import validators
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import CustomUser as User


class SignUpSerializer(serializers.Serializer, validators.UserValidatorMixin):
    """Сериалайзер для регистрации."""
    email = serializers.EmailField(
        max_length=settings.EMAIL_LENGTH, required=True,
    )
    username = serializers.CharField(
        required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'username')


class TokenSerializer(serializers.Serializer, validators.UserValidatorMixin):
    """Сериалайзер для получения токена."""

    username = serializers.CharField(
        required=True)
    confirmation_code = serializers.CharField(
        required=True)

    class Meta:
        model = User
        fields = (
            'username',
            'confirmation_code')


class UserSerializer(
    serializers.ModelSerializer, validators.UserValidatorMixin
):
    """Сериализатор для кастомной модели пользователя"""
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = (
            'username', 'email',
            'first_name', 'last_name',
            'bio', 'role',)


class AuthorSerializer(UserSerializer):
    """Сериализатор для изменения профиля автором"""
    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий."""
    slug = serializers.SlugField(
        max_length=settings.SLUG_LENGTH,
        allow_blank=False,
        validators=[validators.validate_slug])

    class Meta:
        model = Category
        fields = ('name', 'slug',)
        lookup_field = 'slug'

    def validate_slug(self, value):
        if Category.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                'Категория с таким slug уже существует!')
        return value


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров."""
    slug = serializers.SlugField(
        max_length=settings.SLUG_LENGTH,
        allow_blank=False,
        validators=[validators.validate_slug])

    class Meta:
        model = Genre
        fields = ('name', 'slug',)
        lookup_field = 'slug'

    def validate_slug(self, value):
        if Genre.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                'Жанр с таким slug уже существует!')
        return value


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра произведений."""
    category = CategorySerializer(many=False, read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = '__all__'
        read_only_fields = (
            'id',
            'name',
            'year',
            'description',
            'category',
            'genre')


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения произведений."""
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        queryset=Genre.objects.all(),
        validators=[MinValueValidator(0), MaxValueValidator(50)],)
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),)
    year = serializers.IntegerField()

    class Meta:
        model = Title
        fields = '__all__'

    def to_representation(self, value):
        return TitleReadSerializer(self.instance).data

    def validate_year(self, value):
        if value > dt.datetime.now().year:
            raise serializers.ValidationError(
                'Значение года не может быть больше текущего')
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Сериалайзер для отзывов. Валидирует оценку и уникальность."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    score = serializers.IntegerField(
        validators=(MinValueValidator(settings.MIN_SCORE),
                    MaxValueValidator(settings.MAX_SCORE)))

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('title', 'author')

    def validate(self, data):
        request = self.context['request']
        if request.method == 'POST':
            author = request.user
            title_id = self.context.get('view').kwargs.get('title_id')
            title = get_object_or_404(Title, pk=title_id)
            if Review.objects.filter(title=title, author=author).exists():
                raise ValidationError(
                    'Больше одного отзыва на title писать нельзя'
                )
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериалайзер для комментариев."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        fields = '__all__'
        model = Comment
        read_only_fields = ('review',)
