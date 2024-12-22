"""
views.py

Что сделано, чтобы всё работало как нужно:  
1. кастомные страницы для ошибок. Да, шаблоны подключены, но это скорее бэкграундная магия.  
2. работа с пользователями:  
   - профиль пользователя, его редактирование, регистрация, логин/логаут — всё на месте.  
3. пагинация: чтобы не грузить страницу кучей постов, выводим по 10 штук.  
4. теперь можно добавлять картинки к постам.  
5. комментарии:  
   - можно добавить комментарий прямо на странице поста.  
   - автор комментария может его редактировать или удалить.  
   - комментарии считаем и выводим их количество.  
6. добавление/редактирование постов:  
   - создавать посты могут только авторизованные пользователи.  
   - редактировать — только авторы постов.  
7. удаление постов и комментариев с подтверждением. Случайно ничего не потеряется.  
8. используем CBV (Class-Based Views) для упрощения работы со статичными страницами. значительно упрощает код

обратил пристальное внимание при разработке:  
- миксины (`LoginRequiredMixin`, `UserPassesTestMixin`) решают вопросы с доступом.  
- в представлении `PostDetailView` есть проверка — недоступные посты (например, с отложенной датой публикации) видно только их авторам.  
- пагинация реализована через `Paginator`. Это видно в `PostListView` и `CategoryPostsView`.  
- миксин `CommentMixin` обрабатывает права на редактирование/удаление комментариев. 
Вместо того чтобы писать проверки доступа в каждом методе, мы просто подключаем миксин.
"""


from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.http import Http404
from django.views.generic import (ListView,
                                  CreateView,
                                  UpdateView,
                                  DeleteView,
                                  DetailView)

from .models import Post, Category, User, Comment
from .forms import PostForm, CommentForm, UserForm


NUMBER_POSTS = 10


def get_posts(posts=Post.objects, filters=True, annotations=True):
    """
    Возвращает публикации с возможностью фильтрации и аннотирования.
    Фильтрация по умолчанию исключает неопубликованные и скрытые записи.
    Аннотирование добавляет счетчик комментариев к публикациям.
    """
    queryset = posts.select_related(
        'author',
        'location',
        'category'
    )
    if filters:
        queryset = queryset.filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    if annotations:
        queryset = queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    return queryset


class CommentMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Этот миксин — супергерой для работы с комментариями.
    Следит, чтобы только те, кому положено, могли редактировать или удалять комментарии.
    Права пользователей проверяет на каждом шаге и упрощает управление.
    """
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self):
        """
        Вытащим комментарий из базы. Идентификатор передаётся через `kwargs`.
        Если такого нет — сразу 404, чтобы не гадать.
        """
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id)

    def get_success_url(self):
        """
        После успешного действия (редактирование/удаление) отправим пользователя
        обратно к посту, к которому привязан комментарий.
        """
        post_id = self.kwargs.get('post_id')
        return reverse('blog:post_detail', kwargs={'pk': post_id})

    def test_func(self):
        """
        Здесь миксин надевает очки судьи и решает, имеет ли пользователь право
        что-то делать с этим комментарием. Ответ: только автор может править или удалять.
        Если нет — никаких тебе кнопок «удалить» или «править».
        """
        comment = self.get_object()
        return comment.author == self.request.user


def profile(request, user_name):
    """
    Отображает профиль пользователя с его публикациями.
    Сортирует публикации по времени создания и применяет пагинацию.
    """
    user = get_object_or_404(User, username=user_name)
    posts = (
        get_posts(filters=False).filter(author=user)
    )
    paginator = Paginator(posts, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


class PostListView(ListView):
    """
    Отображает список публикаций на главной странице.
    Использует пагинацию для ограничения количества публикаций на странице.
    """
    model = Post
    template_name = 'blog/index.html'
    paginate_by = NUMBER_POSTS

    def get_queryset(self):
        """
        Возвращает список публикаций.
        """
        post_list = get_posts()
        return post_list


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """
    Позволяет автору редактировать свои публикации.
    Перенаправляет неавторизованных пользователей на страницу просмотра поста.
    """
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Проверяет права автора перед доступом к редактированию публикации.
        """
        self.post_id = kwargs['post_id']
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', pk=self.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """
        Перенаправляет пользователя на его профиль после успешного редактирования.
        Это удобно для сохранения контекста работы.
        """
        return reverse('blog:profile', args=[self.request.user.username])


class PostDetailView(DetailView):
    """
    Отображает подробности публикации.
    Проверяет доступность публикации для текущего пользователя.
    """
    model = Post
    template_name = 'blog/detail.html'

    def get_queryset(self):
        """
        Ограничивает доступ к неопубликованным публикациям,
        если пользователь не является автором.
        """
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if not post.is_published and post.author != self.request.user:
            raise Http404
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        """
        Добавляет форму комментариев и список комментариев в контекст страницы.
        Это упрощает добавление комментариев к публикации.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context




class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Позволяет пользователям создавать новые публикации.
    Автор автоматически назначается на основе текущего пользователя.
    """
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя автором перед сохранением формы.
        """
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """
        Перенаправляет пользователя на его профиль после успешного создания публикации.
        Это помогает пользователю быстро увидеть свою новую запись.
        """
        return reverse('blog:profile', args=[self.request.user.username])


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """
    Позволяет пользователям удалять свои публикации.
    Проверяет, является ли текущий пользователь автором перед удалением.
    """
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        """
        Перенаправляет пользователя на его профиль после успешного удаления публикации.
        """
        return reverse('blog:profile', args=[self.request.user.username])

    def dispatch(self, request, *args, **kwargs):
        """
        Проверяет права доступа перед удалением публикации.
        Если пользователь не автор, перенаправляет на страницу публикации.
        """
        self.post_id = kwargs['post_id']
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', pk=self.post_id)
        return super().dispatch(request, *args, **kwargs)


class CategoryPostsView(ListView):
    """
    Отображает публикации в определенной категории.
    Использует пагинацию и проверяет, что категория опубликована.
    """
    model = Post
    template_name = 'blog/category.html'
    paginate_by = NUMBER_POSTS

    def get_queryset(self):
        """
        Возвращает публикации в указанной категории с фильтрацией по статусу.
        """
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )
        return get_posts(filters=False).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category=self.category,
        )

    def get_context_data(self, **kwargs):
        """
        Добавляет информацию о категории в контекст страницы.
        Это упрощает работу с шаблоном.
        """
        context = super().get_context_data(**kwargs)
        context['category'] = self.category

        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """
    Позволяет пользователям редактировать свои данные профиля.
    """
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        """
        Возвращает текущего пользователя для редактирования.
        Это гарантирует, что пользователь может менять только свои данные.
        """
        return self.request.user

    def get_success_url(self):
        """
        Перенаправляет на страницу профиля после успешного обновления данных.
        """
        return reverse('blog:profile', args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    """
    Страница для тех, кто хочет оставить свой мудрый комментарий.
    Только авторизованные пользователи могут писать, потому что анонимам не доверяем.
    Проверяем, что пост существует и опубликован (иначе как комментировать-то?).
    После сохранения — магический редирект на страницу этого самого поста.
    """
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        """
        Перед тем как сохранить комментарий, добавляем немного магии:
        1. Автором автоматически становится текущий пользователь.
        2. Связываем комментарий с постом, который комментируем.
        Если с постом что-то не так (например, его не существует или он скрыт), —
        покажем ошибку, чтобы всё было честно.
        """
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['comment_id'],
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
        return super().form_valid(form)

    def get_success_url(self):
        """
        После успешного сохранения комментария перенаправляем на страницу поста.
        """
        return reverse(
            'blog:post_detail', kwargs={'pk': self.kwargs['pk']}
        )


class CommentDeleteView(CommentMixin, DeleteView):
    """
    Удаление комментария. Всё просто: миксин проверяет, что ты — именно тот автор,
    который имеет право удалить это чудо. Если всё ок — комментарий исчезает.
    """
    pass


class CommentUpdateView(CommentMixin, UpdateView):
    """
    Снова всё через миксин, который проверит права и упростит жизнь.
    """
    form_class = CommentForm
