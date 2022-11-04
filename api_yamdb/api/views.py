from api.filters import TitlesFilter
from api.permissions import (IsAdminOrModeratorOrAuthor, IsAdminOrReadOnly,
                             IsAdminOrSuperUser)
from api.serializers import (AuthorSerializer, CategorySerializer,
                             CommentSerializer, GenreSerializer,
                             ReviewSerializer, SignUpSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             TokenSerializer, UserSerializer)
from api.utils import generate_confirmation_code, send_confirmation_code
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title
from users.models import CustomUser as User


class RegisterView(APIView):
    """Регистирирует пользователя и отправляет
       ему код подтверждения на email."""
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')
        confirmation_code = generate_confirmation_code()
        try:
            user, _ = User.objects.get_or_create(
                email=email, username=username)
        except IntegrityError:
            message = (
                settings.DUPLICATE_EMAIL_MESSAGE
                if User.objects.filter(email=email).exists()
                else settings.DUPLICATE_USERNAME_MESSAGE
            )
            return Response(
                message,
                status=status.HTTP_400_BAD_REQUEST)
        user.confirmation_code = generate_confirmation_code()
        user.save()
        send_confirmation_code(email, confirmation_code)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenView(APIView):
    """Проверяет код подтверждения и отправляет токен."""
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        confirmation_code = serializer.validated_data.get('confirmation_code')
        user = get_object_or_404(
            User,
            username=username,
        )
        if (confirmation_code != user.confirmation_code
                or confirmation_code == ' '):
            return Response(
                'Confirmation code is invalid',
                status=status.HTTP_400_BAD_REQUEST)
        user.confirmation_code = ' '
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {'access_token': str(refresh.access_token)},
            status=status.HTTP_200_OK
        )


class UserViewSet(viewsets.ModelViewSet):
    """Админ получает список пользователей или создает нового"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrSuperUser, ]
    lookup_field = 'username'
    search_fields = ('username', )

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me')
    def user_info(self, request):
        if request.method == 'GET':
            serializer = AuthorSerializer(request.user)
        else:
            serializer = AuthorSerializer(
                request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CLDMixinSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = PageNumberPagination
    search_fields = ('name',)
    filter_backends = [filters.SearchFilter]
    lookup_field = 'slug'


class GenreViewSet(CLDMixinSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class CategoryViewSet(CLDMixinSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score'))
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TitlesFilter
    ordering_fields = ('name',)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrModeratorOrAuthor]
    pagination_class = PageNumberPagination
    serializer_class = ReviewSerializer

    def title_query(self):
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.title_query().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.title_query())


class CommentViewSet(ReviewViewSet):
    serializer_class = CommentSerializer

    def review_query(self):
        return get_object_or_404(Review, id=self.kwargs.get('review_id'))

    def get_queryset(self):
        return self.review_query().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.review_query())
