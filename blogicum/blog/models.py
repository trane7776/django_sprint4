"""

по требованиям:  
1.   мы добавили общий функционал для всех моделей:  
   - Поле `is_published` — чтобы можно было легко скрыть любую запись.  
   - Поле `created_at` — фиксирует дату создания.  
   Это позволяет избежать дублирования кода.

2.  
   - поле `pub_date` позволяет публиковать посты с отложенной датой.  
   - возможность прикреплять изображения через поле `image`.  
   - привязка к автору, категории и местоположению:  
     - автор (связь с пользователем).  
     - категория — нужна для структурирования контента.  
     - местоположение — добавляет интерактивности, особенно если нужно привязать контент к какому-то месту.

3.модель категории*  
  каждая категория может быть легко найдена через уникальный `slug`.  

4.модель местоположения:**  
   Нужна для привязки постов к конкретным географическим местам.

5. модель комментариев**  
   - сортируются по времени создания.  
   - комментарии привязываются к посту и автору, что упрощает их отображение.

Почему это сделано:  
- наследуем базовую модель Это позволило убрать повторяющийся код и сделать структуру чище. Например, поля `is_published` и `created_at` теперь автоматически есть в каждой модели, которая от `BaseModel` наследуется.  
- **Гибкость управления данными:**  
  - Админы могут скрывать посты, категории и местоположения, не удаляя их.  
  - Отложенная публикация через `pub_date` делает систему удобной для авторов.  
  - Публикации и комментарии связаны через `related_name`, что упрощает доступ к данным в шаблонах.
- Поле `slug`должно быть уникальное.  
- Если публикация не опубликована (`is_published=False`), она не должна быть доступна пользователям.  
- У комментариев сортировка идёт «от старых к новым», чтобы лента была логичной.

Эта структура легко расширяется. Если  добавить, например, теги или оценки к постам, это можно сделать быстро и без хаоса в коде.  
"""

from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()



class BaseModel(models.Model):
    """База всех баз: публикация, создание, всё в одном."""

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.',
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    def __str__(self):
        """Возвращаем строковое представление объекта — тут это заголовок."""

        return self.title

    class Meta:
        abstract = True


class Post(BaseModel):
    """Публикация: тексты, картинки, и всё, что любят люди."""
    title = models.CharField('Заголовок', max_length=256)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — можно делать отложенные'
            ' публикации.'
        ),
    )
    image = models.ImageField('Фото', upload_to='post_images', blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts',
    )
    location = models.ForeignKey(
        'Location',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Местоположение',
        related_name='posts',
    )
    category = models.ForeignKey(
        'Category',
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
        related_name='posts',
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ("-pub_date",)


class Category(BaseModel):
    """Категории для постов, чтобы всё было по полочкам."""
    title = models.CharField('Заголовок', max_length=256)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; разрешены символы латиницы,'
            ' цифры, дефис и подчёркивание.'
        ),
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Location(BaseModel):
    """Местоположение."""
    name = models.CharField('Название места', max_length=256)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'


class Comment(models.Model):
    """Комментарии — всё, что люди пишут под постами."""
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
