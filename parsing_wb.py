from csv import excel
import time
import pandas as pd
from bs4 import BeautifulSoup
from curl_cffi import requests
from selenium import webdriver
from openpyxl.workbook import Workbook

def get_webdriver():
    """Заходим под видом не пользователя"""

    webdri = webdriver.Chrome()
    return webdri


def scrlldown(webdri, deep):
    """Скроллить сайт"""

    for _ in range(deep):
        webdri.execute_script('window.scrollBy(0, 1000)')
        time.sleep(2)


def test_wildbrs(url_wildbrs, webdri):
    """Парсинг ВБ"""

    #TODO не хватает ссылки на продавца, размеры товаров, остатка товара (надо заходить на сам товар)
    #TODO не перелистывает страницы из-за ленивой загрузки, мб редактированием скроллинга

    webdri.get(url_wildbrs)
    scrlldown(webdri, 20)
    soup_page = BeautifulSoup(webdri.page_source, 'html.parser')

    content_wb = soup_page.find('div', {"class": "main__container"})
    content_wb_with_article = content_wb.find_all('article', {'data-nm-id': True})

    products = []
    for item in content_wb_with_article:

        link = item.find('a', {'class': 'product-card__link j-card-link j-open-full-product-card'})
        if link is not None:
            link = link['href']

        article = item.get('data-nm-id')
        name = item.find('span', {'class': 'product-card__name'}).text.strip().replace('/', '')
        
        price_element = item.find('ins', {'class': lambda x: x and 'price__lower-price' in x})
        if price_element:
            price = price_element.text.strip()
            price = float(price.replace('₽', '').replace(' ', '').replace('\xa0', ''))
        else:
            price = None
            
        link_img = item.find('img', {'class': 'j-thumbnail'})
        if link_img is not None:
            link_img = link_img['src']

        count_products = item.find('span', {'class': 'product-card__count'})
        if count_products is not None:
            count_products = count_products.text.strip()

        rating = item.find('span', {'class': 'address-rate-mini address-rate-mini--sm'})
        if rating is not None:
            rating = rating.text.strip()
            rating = float(rating.replace(',', '.'))

        name_brand = item.find('span', {'class': 'product-card__brand-container'})
        if name_brand is not None:
            name_brand = name_brand.text.strip()

        product_data = {
                'Ссылка на товар': link,
                'Артикул': article,
                'Название': name,
                'Цена, Р': price,
                'Название селлера': name_brand,
                'Ссылки на изображения': link_img,
                'Количество отзывов': count_products,
                'Рейтинг': rating,
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

    filter_df = res[(res['Рейтинг'] >= 4.5) & (res['Цена, Р'] <= 10000)]
    filter_df.to_excel("Result_parsing_wb_2.xlsx")
    return res


if __name__ == "__main__":  

    webdri = get_webdriver()

    search_tag = "пальто+из+натуральной+шерсти"
    url_search = f"https://global.wildberries.ru/catalog?search={search_tag}"

    res_pasr = test_wildbrs(url_search, webdri)
    save_res = save_to_excel(res_pasr)
    select_res = selection_to_excel(save_res)

    webdri.quit()
