"""
urls.py

Что сделал:  
1. подключил маршруты для пользователей:  
   - `/profile/<username>/` — страница профиля.  
   - `/edit_profile/` — редактирование профиля.  
2. публикации:  
   - `/posts/create/` — создание нового поста.  
   - `/posts/<int:pk>/edit/` — редактирование поста.  
   - `/posts/<int:pk>/delete/` — удаление поста.  
3. комментарии:  
   - `/posts/<int:pk>/comment/` — добавить комментарий.  
   - `/posts/<int:post_id>/edit_comment/<int:comment_id>/` — редактировать комментарий.  
   - `/posts/<int:post_id>/delete_comment/<int:comment_id>/` — удалить комментарий.  
4. пагинация: категории и главная страница (`/category/<slug:category_slug>/` и `/`).

Что важно:  
- удобные имена маршрутов (`name`). Это помогает вызывать URL через `reverse`, не вспоминая детали.  
- всё аккуратно разделено: маршруты для постов, комментариев, профиля. Логика в них полностью соответствует требованиям.  
- маршруты для комментариев (`edit_comment`, `delete_comment`) уже завязаны на проверки прав через миксины в представлениях.

"""


from django.urls import path

from . import views



app_name = 'blog'
urlpatterns = [
    # для использования cbv вместо fbv используем метод as_view()
    # Главная страница со всеми постами
    path('', views.PostListView.as_view(), name='index'),
    
    # Детальная страница поста
    path('posts/<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    
    # Посты по категориям
    path('category/<slug:category_slug>/', views.CategoryPostsView.as_view(), name='category_posts'),
    
    # Создание нового поста
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    
    # Профиль пользователя
    path('profile/<slug:user_name>/', views.profile, name='profile'),
    
    # Редактирование профиля
    path('edit_profile/', views.UserUpdateView.as_view(), name='edit_profile'),
    
    # Редактирование поста
    path('posts/<int:post_id>/edit/', views.PostUpdateView.as_view(), name='edit_post'),
    
    # Удаление поста
    path('posts/<int:post_id>/delete/', views.PostDeleteView.as_view(), name='delete_post'),
    
    # Добавление комментария
    path('posts/<int:comment_id>/comment/', views.CommentCreateView.as_view(), name='add_comment'),
    
    # Редактирование комментария
    path('posts/<int:post_id>/edit_comment/<int:comment_id>/', views.CommentUpdateView.as_view(), name='edit_comment'),
    
    # Удаление комментария
    path('posts/<int:post_id>/delete_comment/<int:comment_id>/', views.CommentDeleteView.as_view(), name='delete_comment'),
]
