# Matthew Taylor

# Running spider with IDE:
# https://docs.scrapy.org/en/latest/topics/practices.htm
#
# Reading a string in with regex
# https://www.w3schools.com/python/python_regex.asp
#
# Sorting the order in which my files will be read
# https://www.geeksforgeeks.org/python-sorted-function/
#
# Extra work:
# In this webscraper three kinds of url are being scrapped: product pages and manufacturer pages.
# Each kind of page is scrapped and the info is stored in three respective files.
#
# From the manufacturer pages, I have scraped a list of all products each manufacturer has made.
# The list among other attributes can be found in www.pluginboutique.com-manufacturers.jsonl
# The names of these products are searched for in www.pluginboutique.com-products.jsonl.
# From those files, many attributes are stored in the 'products' array in www.pluginboutique.com-manufacturers.json
#
# From the products array, the ratings and review counts of each product are used to calculate an overall manufacturer
# rating.


from pathlib import Path

import numpy as np
from scrapy.utils.conf import closest_scrapy_cfg
import scrapy
import json

product_data = []

# sets the sort priority of my urls. Intended for start_urls
def sort_priority(url):
    if 'www.pluginboutique.com/products/' in url:
        return 1
    elif 'www.pluginboutique.com/manufacturers/' in url:
        return 2
    else:
        return 3


class PluginSpider(scrapy.Spider):
    name = "plugins"
    plugin_urls = open("www.pluginboutique.com.urls.txt", "r", encoding="utf-8")
    start_urls = []
    for url in plugin_urls:
        product = 'www.pluginboutique.com/products/' in url
        manufacturer = 'www.pluginboutique.com/manufacturers/' in url
        if product or manufacturer:
            start_urls.append(url)
    start_urls = sorted(start_urls, key=sort_priority)


    def parse(self, response):
        product = 'www.pluginboutique.com/products/' in response.url
        manufacturer = 'www.pluginboutique.com/manufacturers/' in response.url
        if product:
            attrs = self.scrape_product_page(response)
            product_data.append(attrs)
            with open('www.pluginboutique.com-products.jsonl', 'a', encoding='utf-8') as fp:
                fp.write(json.dumps(attrs, ensure_ascii=False) + '\n')
            with open('www.pluginboutique.com-products-vis.jsonl', 'a', encoding='utf-8') as fp:
                fp.write(json.dumps(attrs, ensure_ascii=False, indent=4) + '\n')
        elif manufacturer:
            attrs = self.scrape_manufacturer_page(response)
            # with open('www.pluginboutique.com-manufacturers.json', 'w') as fp:
            #     json.dump(manufacturers, fp, indent=4)
            with open('www.pluginboutique.com-manufacturers.jsonl', 'a', encoding='utf-8') as fp:
                fp.write(json.dumps(attrs, ensure_ascii=False) + '\n')
            with open('www.pluginboutique.com-manufacturers-vis.jsonl', 'a', encoding='utf-8') as fp:
                fp.write(json.dumps(attrs, ensure_ascii=False, indent=4) + '\n')
            pass

    def get_product_info(self, response):
        nosto_product = response.css('div.nosto_product')
        try:
            data_react_props_str = response.css('div[data-react-class="BuyBox"]::attr(data-react-props)').get()
            data_react_props = json.loads(data_react_props_str)
            sell_price = data_react_props['sell_price']
            sell_price = float(sell_price.replace('$', '').replace(',', '').split('.')[0])
            list_price = data_react_props['regular_price']
            list_price = float(list_price.replace('$', '').replace(',', '').split('.')[0])
            on_sale = data_react_props['on_sale']
            savings = list_price - sell_price
            discount = 100 - 100 * (sell_price/list_price)

        except:
            sell_price = float(nosto_product.css('span.price::text').get())
            sell_price /= .789
            sell_price = format(sell_price, '.2f')
            list_price = sell_price
            on_sale = False
            savings = 0.00
            discount = 0.0

        product_id = nosto_product.css('span.product_id::text').get()
        image_url = nosto_product.css('span.image_url::text').get()
        availability = nosto_product.css('span.availability::text').get()
        brand = nosto_product.css('span.brand::text').get()
        description = nosto_product.css('span.description::text').get()
        categories = nosto_product.css('span.category::text').getall()[1]
        rating = float(nosto_product.css('span.rating_value::text').get())
        review_count = int(nosto_product.css('span.review_count::text').get())
        return {
            'product_id': product_id,
            'image_url': image_url,
            'availability': availability,
            'on_sale': on_sale,
            'sell_price': sell_price,
            'list_price': list_price,
            'savings': savings,
            'discount': discount,
            'brand': brand,
            'description': description,
            'category': categories,
            'rating': int(rating),
            'review_count': review_count
        }


    def get_manufacturer_info(self, response):
        category = response.css("div.nosto_category::text").get()
        manufacturer = category.strip("/Manufacturers/")
        logo_src = response.css('.page-manufacturer-logo::attr(src)').get()
        logo_url = 'https://www.pluginboutique.com' + logo_src
        about = response.css("div.page-manufacturer-about::text").get()
        products = self.get_manufacturer_products(manufacturer, product_data)
        rating = self.get_manufacturer_rating(products)
        product_count = len(products)
        review_count = 0
        for product in products:
            attrs = product['attributes']
            if attrs:
                rc = float(attrs['review_count'])
                review_count += rc
        return {
            'manufacturer': manufacturer,
            'about': about,
            'logo_image_url': logo_url,
            'products': products,
            'product_count': product_count,
            'rating': rating,
            'review_count': review_count
        }


    def get_manufacturer_rating(self, products):
        sum_reviews = 0
        sum_ratings = 0
        for product in products:
            attrs = product['attributes']
            if attrs:
                review_count = float(attrs['review_count'])
                sum_reviews += review_count
                sum_ratings += float(attrs['rating']) * review_count
        try:
            ret = sum_ratings/sum_reviews
        except ZeroDivisionError:
            return 0
        return ret


    def get_manufacturer_products(self, manufacturer, products_data):
        product_arr = []
        for json_prod in products_data: # search for in products
            if manufacturer == json_prod['manufacturer']:
                _id = json_prod['id']
                sell_price = json_prod['sell_price($)']
                list_price = json_prod['list_price($)']
                categories = json_prod['categories']
                on_sale = json_prod['on_sale']
                rating = json_prod['rating']
                review_count = json_prod['review_count']
                attributes = {
                    'id': _id,
                    'categories': categories,
                    'sell_price($)': sell_price,
                    'list_price($)': list_price,
                    'on_sale': on_sale,
                    'review_count': review_count,
                    'rating': rating,
                }
                if len(attributes) != 0:
                    product = {
                        "name": json_prod['name'],
                        "attributes": attributes,
                    }
                    product_arr.append(product)
        return product_arr


    def scrape_product_page(self, response):
        product_info = self.get_product_info(response)
        attributes = {
            'id': product_info['product_id'],
            'url': response.url,
            'title': response.css('title::text').get(),
            'name': response.css('h1::text').get(),
            'manufacturer': product_info['brand'],
            'categories': product_info['category'],
            'description': product_info['description'],
            'on_sale': product_info['on_sale'],
            'sell_price($)': product_info['sell_price'],
            'list_price($)': product_info['list_price'],
            'savings($)': product_info['savings'],
            'discount': product_info['discount'],
            'availability': product_info['availability'],
            'rating': product_info['rating'],
            'review_count': product_info['review_count'],
            'image_url': product_info['image_url'],
        }
        return attributes

    def scrape_manufacturer_page(self, response):
        manufacturer_info = self.get_manufacturer_info(response)
        attributes = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'manufacturer': manufacturer_info['manufacturer'],
            'about': manufacturer_info['about'],
            'rating': manufacturer_info['rating'],
            'review_count': manufacturer_info['review_count'],
            'reliability': manufacturer_info['review_count'] * np.power(manufacturer_info['rating'], 2),
            'product_count': manufacturer_info['product_count'],
            'products': manufacturer_info['products'],
            'logo_image_url': manufacturer_info['logo_image_url'],
        }
        return attributes
