import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

X_WBAAS_TOKEN = os.getenv('X_WBAAS_TOKEN')

def get_basket():
    """Получаем актуальные границы basket’ов"""

    lst_basket = []

    url = "https://cdn.wbbasket.ru/api/v3/upstreams"
    response = requests.get(url)

    data = response.json()
    servers = data['origin']['mediabasket_route_map'][0]['hosts']

    for serv in servers:
        lst_basket.append(serv['host'])

    return lst_basket


def get_sku(search_tag):
    """Получаем список всех id товаров по запросу"""

    url = "https://www.wildberries.ru/__internal/search/exactmatch/ru/common/v18/search"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Cookie": f"x_wbaas_token={X_WBAAS_TOKEN}",
        "Referer": "https://www.wildberries.ru/"
        }
    
    params = {
        "query": search_tag,
        "resultset": "catalog",
        "dest": -1257786,
        "limit": 20,
        "appType": 1,
        "curr": "rub",
        "lang": "ru",
        "spp": 30,
        "sort": "popular"
    }
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None


def get_product_info(sku):
    """Получаем информацию о продуках по их id"""

    lst_basket = get_basket()

    vol_part = sku // 100000
    part = sku // 1000

    for basket in lst_basket:
        url = f"https://{basket}/vol{vol_part}/part{part}/{sku}/info/ru/card.json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            
        except requests.RequestException:
            continue 


def get_all_info(search_tag):
    """Получаем информацию о продуках по их id"""
    products = []

    sku_info = get_sku(search_tag)

    for sku in sku_info['products']:
        product_info = get_product_info(sku['id'])

        link = f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"

        article = sku['id']

        name = product_info.get('imt_name', '')

        price_basic = sku['sizes'][0].get('price').get('basic') / 100
        price_sale = sku['sizes'][0].get('price').get('product') / 100

        description = product_info.get('description', '')

        photo_count = product_info['media'].get('photo_count', 0)

        name_brand = product_info['selling'].get('brand_name', '')
        brand_id = product_info['selling'].get('supplier_id', '')

        link_brand = f"https://www.wildberries.ru/seller/{brand_id}"

        sizes_lst = []
        if 'sizes_table' in product_info and 'values' in product_info['sizes_table']:
            for size in product_info['sizes_table']['values']:
                sizes_lst.append(str(size['tech_size']))

        sizes = ', '.join(sizes_lst) if sizes_lst else "Размеры не указаны"

        rating = sku['rating']

        count_products = sku['feedbacks']

        for option in product_info['options']:
            if option.get('name') == 'Страна производства':
                country =  option.get('value', '')

        product_data = {
            'Ссылка на товар': link,
            'Артикул': article,
            'Название': name,
            'Цена': price_basic,
            'Цена со скидкой': price_sale,
            'Описание': description,
            'Ссылки на изображения через запятую': photo_count,
            'Название селлера': name_brand,
            'Ссылка на селлера': link_brand,
            'Размеры товара через запятую': sizes,
            'Рейтинг': rating,
            'Количество отзывов': count_products,
            'Страна производства': country
        }

        products.append(product_data)
    return products


def save_to_excel(products):
    """Сохраняет в эксель результат парсинга вб"""

    res = pd.DataFrame(products)
    res.to_excel("Result_parsing_wb_1.xlsx")
    return res


def selection_to_excel(res):
    """Сохраняет в эксель выборку"""

    filter_df = res[(res['Рейтинг'] >= 4.5) & (res['Цена со скидкой'] <= 10000) & (res['Страна производства'].str.contains('Россия', case=False, na=False))]
    filter_df.to_excel("Result_parsing_wb_2.xlsx")
    return res

if __name__ == "__main__":

    search_tag = "пальто из натуральной шерсти"

    parse_wb = get_all_info(search_tag)
    save_res = save_to_excel(parse_wb)
    select_res = selection_to_excel(save_res)

