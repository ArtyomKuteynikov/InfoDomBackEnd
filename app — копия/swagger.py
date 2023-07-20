from marshmallow import Schema, fields
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin


def get_apispec(app):
    """ Формируем объект APISpec.

    :param app: объект Flask приложения
    """
    spec = APISpec(
        title="Info Dom",
        version="1.0.0",
        openapi_version="3.0.3",
        plugins=[FlaskPlugin(), MarshmallowPlugin()],
    )

    # spec.components.schema("Input", schema=InputAuthSchema)
    # spec.components.schema("Output", schema=OutputAuthSchema)
    # spec.components.schema("Error", schema=ErrorSchema)

    create_tags(spec)

    load_docstrings(spec, app)

    return spec


class InputAuthSchema(Schema):
    phone_number = fields.String(description="Номер телефона", required=True, example="+79151290127")


class OutputAuthSchema(Schema):
    result = fields.String(description="Результат", required=True, example="Hello, Artem!")


class ErrorSchema(Schema):
    error = fields.String(description="Ошибка", required=True, example='Описание ошибки')


def create_tags(spec):
    """ Создаем теги.
    :param spec: объект APISpec для сохранения тегов
    """
    tags = [
        {'name': 'auth', 'description': 'Авторизация и все действия с базой бзеров'},
        {'name': 'news', 'description': 'Новости'},
        {'name': 'promotions', 'description': 'Объявления'},
        {'name': 'complaints', 'description': 'Жалоба'},
        {'name': 'chats', 'description': 'Все что не вошло в остальные'},
    ]

    for tag in tags:
        print(f"Добавляем тег: {tag['name']}")
        spec.tag(tag)


def load_docstrings(spec, app):
    """ Загружаем описание API.

    :param spec: объект APISpec, куда загружаем описание функций
    :param app: экземпляр Flask приложения, откуда берем описание функций
    """
    for fn_name in app.view_functions:
        if fn_name == 'static':
            continue
        print(f'Загружаем описание для функции: {fn_name}')
        view_fn = app.view_functions[fn_name]
        spec.path(view=view_fn)
