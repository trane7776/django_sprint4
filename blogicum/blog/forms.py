"""
forms.py

Зачем нужен этот файл:  
Здесь мы описали формы для работы с нашими моделями. Это ключевой элемент для взаимодействия пользователей с данными в проекте.
Этот файл — связующее звено между моделями и пользовательскими формами.  
Идея в том, чтобы дать пользователю удобный способ вводить данные, которые сразу проверяются и сохраняются в базу.
 
1. Форма пользователя (`UserForm`): 
   
2. Форма публикации (`PostForm`):
3. Форма комментария (`CommentForm`):

- все формы напрямую  связаны с моделями через `ModelForm`, чтобы не писать вручную обработку данных. Это упрощает код и снижает вероятность ошибок.  
- используем только нужные поля, чтобы избежать проблем с безопасностью и лишними данными.

"""


from .models import Post, User, Comment

from django import forms
from django.forms.widgets import DateTimeInput


class UserForm(forms.ModelForm):
    """Форма для редактирования данных пользователя."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования постов."""
    pub_date = forms.DateTimeField(
        widget=DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Дата и время публикации',
        required=True,
        help_text=(
            'Если установить дату и время в будущем — можно делать отложенные '
            'публикации.'
        )
    )


    class Meta:
        model = Post
        exclude = ('author', 'created_at')


class CommentForm(forms.ModelForm):
    """Форма для добавления комментария."""
    class Meta:
        model = Comment
        fields = ('text',)
