from django.shortcuts import render, redirect
from requests import RequestException

from .forms import ArticleForm
from .models import Product
import requests
from decimal import Decimal

def fetch_product_data(article):
    url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&ab_testing=false&nm={article}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and "products" in data["data"]:
            product_data = data["data"]["products"][0]
            # Извлекаем необходимые данные
            name = product_data.get("name", "Неизвестно")

            # Пытаемся получить информацию о ценах из первого элемента в "sizes"
            if "sizes" in product_data and len(product_data["sizes"]) > 0:
                price_info = product_data["sizes"][0].get("price", {})
                current_price = price_info.get("total", 0) / 100  # Цена со скидкой, используем и для добавления, и для обновления
            else:
                current_price = 0

            return {
                "name": name,
                "current_price": Decimal(current_price),
            }

    # Если запрос не успешен или данные не найдены
    return None

def get_image_url(nm_id):
    # Перебираем возможные варианты серверов от basket-01 до basket-20 для тестирования
    for i in range(1, 21):
        server_number = f"{i:02d}"  # Форматируем числа от 1 до 9 как 01, 02 и т.д.
        # Обновляем домен на wbbasket.ru
        domain = f"basket-{server_number}.wbbasket.ru"
        # Добавим отладочный вывод, чтобы проверить, что серверы действительно перебираются
        print(f"DEBUG: Проверяем сервер {domain}")

        # Перебираем варианты с 4 и 3 цифрами после /vol
        for vol_size in [4, 3]:
            vol_part = nm_id[:vol_size]  # Извлекаем нужное количество символов для vol
            # Перебираем варианты с 5, 6 и 7 цифрами после /part
            for part_size in [5, 6, 7]:
                part_part = nm_id[:part_size]  # Извлекаем нужное количество символов для part
                url = f"https://{domain}/vol{vol_part}/part{part_part}/{nm_id}/images/big/1.webp"

                print(f"DEBUG: Пытаемся найти изображение по URL: {url}")

                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code == 200:
                        print(f"DEBUG: Найдено изображение по URL: {url}")
                        return url
                except RequestException as e:
                    # Выводим информацию об ошибке для отладки
                    print(f"DEBUG: Ошибка при попытке доступа к URL {url} - {str(e)}")
                    # Продолжаем пытаться с другими комбинациями серверов

    print(f"DEBUG: Изображение для артикула {nm_id} не найдено")
    return None


def product_list(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.cleaned_data['article']
            # Проверяем, существует ли продукт уже в базе данных
            if not Product.objects.filter(article=article).exists():
                product_info = fetch_product_data(article)
                if product_info:
                    # Получаем URL изображения
                    image_url = get_image_url(article)
                    if not image_url:
                        image_url = ''  # Или установите URL изображения по умолчанию
                    # Сохраняем продукт в базе данных с ценой на момент добавления
                    Product.objects.create(
                        article=article,
                        name=product_info['name'],
                        initial_price=product_info['current_price'],
                        image_url=image_url,
                    )
                    return redirect('product_list')
                else:
                    form.add_error('article', 'Продукт не найден.')
            else:
                form.add_error('article', 'Продукт уже добавлен.')
    else:
        form = ArticleForm()

    products = Product.objects.all()
    # Обновляем текущие цены и вычисляем изменения
    product_cards = []
    for product in products:
        product_data = fetch_product_data(product.article)
        if product_data:
            current_price = product_data['current_price']
            price_change = current_price - product.initial_price
            if product.initial_price != 0:
                price_change_percent = (price_change / product.initial_price) * 100
            else:
                price_change_percent = 0
            product_cards.append({
                'product': product,
                'current_price': current_price,
                'price_change': price_change,
                'price_change_percent': price_change_percent,
            })
        else:
            # Если не удалось получить данные о продукте
            product_cards.append({
                'product': product,
                'current_price': 'Недоступно',
                'price_change': 'Недоступно',
                'price_change_percent': 'Недоступно',
            })
    context = {
        'form': form,
        'product_cards': product_cards,
    }
    return render(request, 'products/product_list.html', context)

def delete_product(request, article):
    Product.objects.filter(article=article).delete()
    return redirect('product_list')

