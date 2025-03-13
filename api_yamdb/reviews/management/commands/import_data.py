import os
import csv

from django.conf import settings
from django.core.management import BaseCommand

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User


class Command(BaseCommand):
    """Команда для импорта данных из csv."""

    def handle(self, *args, **kwargs):
        self.import_data(Genre, 'genre')
        self.import_data(Category, 'category')
        self.import_data(User, 'users')
        self.import_data(Title, 'titles')
        self.import_data(Review, 'review')
        self.import_data(Comment, 'comments')
        self.import_genre_title('genre_title')

    @staticmethod
    def read_file(file_name):
        """Чтение данных из csv файла для последующего импорта."""
        file_path = os.path.join(
            settings.BASE_DIR, 'static/data/', f'{file_name}.csv'
        )
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)

    def get_new_data(self, cur_model, file_name):
        """Загружаем только те данные, которых нет в БД."""
        reader = self.read_file(file_name)
        db_data = list(cur_model.objects.all().values(*reader[0].keys()))
        for record in db_data:
            for key in record.keys():
                record[key] = str(record[key])
        db_data_set = {tuple(d.items()) for d in db_data}
        new_data = [
            row for row in reader if tuple(row.items()) not in db_data_set
        ]
        return new_data

    def import_data(self, cur_model, file_name):
        """Импорт данных в БД."""
        reader = self.get_new_data(cur_model, file_name)
        for row in reader:
            if cur_model == Title:
                category_id = row.pop('category', None)
                row['category'] = Category.objects.get(id=category_id)
            elif cur_model in (Review, Comment):
                author_id = row.pop('author', None)
                row['author'] = User.objects.get(id=author_id)
            model, created = cur_model.objects.get_or_create(**row)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Добавлена запись: {model}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Запись уже существует: {model}')
                )

    def import_genre_title(self, file_name):
        """Импорт данных в БД для связи многие ко многим."""
        reader = self.read_file(file_name)
        for row in reader:
            # Проверяем существование title и genre перед созданием связи
            try:
                title = Title.objects.get(id=row['title_id'])
                genre = Genre.objects.get(id=row['genre_id'])
                title.genre.add(genre)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Связь между произведением ID "{title.id}"'
                        + f'и жанром ID "{genre.id}" создана.'
                    )
                )
            except Title.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Произведение с ID "{row["title_id"]}" не существует.'
                    )
                )
            except Genre.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Жанр с ID "{row["genre_id"]}" не существует.'
                    )
                )
