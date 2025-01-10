import asyncio
import os
import time
import json
import re
import pyautogui
import pyperclip
import webbrowser
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from app.models.food_brand_model import FoodBrand, BrandName
from app.models.food_product_model import FoodProduct
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bson import ObjectId
from datetime import datetime

class FoodService:
    @staticmethod
    async def getKababjeesFriedData():
        # Step 1: Save or get Kababjees Fried Chicken brand in the database
        brand_name = "Kababjees Fried Chicken"
        brand = await FoodBrand.find_one({"brand_name": brand_name})

        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        brand_id = brand.id

        async def save_html_content():
            url = "https://www.kababjeesfriedchicken.com/"
            webbrowser.open(url)
            time.sleep(8)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(5)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(3)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(2)

            js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(2.5)

            html_content = pyperclip.paste()
            file_name = "Kababjees_Fried_Chicken.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            pyautogui.hotkey('ctrl', 'w')
            return file_name

        html_file = await save_html_content()

        async def parse_products(input_html):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all('div', class_='p-0 mb-3 mb-md-0 large_icons_menu_2-item undefined undefined undefined col-6 col-sm-6 col-md-4 col-lg-4')
            products = []

            for div in divs:
                product = {}
                datacatid = div.get('datacatid', '')
                dataitemid = div.get('dataitemid', '')

                if datacatid and dataitemid:
                    product['product_url'] = f"https://www.kababjeesfriedchicken.com/?item_id={dataitemid}%7C{datacatid}"

                    if datacatid == '419981':
                        product['food_category'] = "Deal"
                    elif datacatid == '416671':
                        product['food_category'] = "Deal"
                    elif datacatid == '414069':
                        product['food_category'] = "Wing"
                    elif datacatid == '415886':
                        product['food_category'] = "Chicken Bites"
                    elif datacatid == '415892':
                        product['food_category'] = "Starter"
                    elif datacatid == '407639':
                        product['food_category'] = "Deal"
                    elif datacatid == '407640':
                        product['food_category'] = "Deal"
                    elif datacatid == '407641':
                        product['food_category'] = "Burger"
                    elif datacatid == '416904':
                        product['food_category'] = "Kid"
                    elif datacatid == '407642':
                        product['food_category'] = "Add Ons"
                    elif datacatid == '407643':
                        product['food_category'] = "Beverage"
                    else:
                        product['food_category'] = "Uncategorized"

                    title_tag = div.find('h2', style='color: rgb(33, 37, 41);')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)

                    description_tag = div.find('p', style='color: rgb(113, 128, 150);')
                    product['description'] = description_tag.get_text(strip=True) if description_tag else ""

                    price_wrapper = div.find('div', class_='price-wrapper')
                    if price_wrapper:
                        # Save price as original_price and set discount_price to None
                        price_tag = price_wrapper.find('span')
                        if price_tag:
                            product['original_price'] = price_tag.get_text(strip=True).replace('Rs.', '').strip()
                            product['discount_price'] = None

                    img_tag = div.find('img', class_='rounded-0')
                    if img_tag and img_tag.get('src'):
                        product['image_url'] = "https://www.kababjeesfriedchicken.com" + img_tag['src']

                    product['brand_id'] = ObjectId(brand_id)
                    products.append(product)

            return products

        products = await parse_products(html_file)

        for product in products:
            required_fields = ["title", "original_price", "image_url", "product_url", "brand_id", "food_category"]

            if not all(product.get(field) for field in required_fields):
                print(f"Skipping product due to missing fields: {product}")
                continue

            # existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            # if not existing_product:
            #     new_product = FoodProduct(**product)
            #     await new_product.save()
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product["original_price"] or
                    existing_product.discount_price != product["discount_price"]
                )

                if price_changed:
                    # Update prices and the `updatedAt` timestamp
                    existing_product.original_price = product["original_price"]
                    existing_product.discount_price = product["discount_price"]
                    existing_product.updatedAt = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = FoodProduct(**product)
                await new_product.save()

        print("Kababjees Fried Chicken data scraping and saving completed!")
        os.remove(html_file)
    @staticmethod
    async def getAngeethiData():
        # Step 1: Save or get Angeethi brand in the database
        brand_name = "Angeethi"
        brand = await FoodBrand.find_one({"brand_name": brand_name})

        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        brand_id = brand.id

        async def save_html_content():
            url = "https://angeethipk.com/"
            webbrowser.open(url)
            time.sleep(20)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(3)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(3)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(2)

            js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(1.5)

            html_content = pyperclip.paste()
            file_name = "Angeethi.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            pyautogui.hotkey('ctrl', 'w')
            return file_name

        html_file = await save_html_content()

        async def parse_products(input_html):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all(
                'div',
                class_='p-0 mb-3 mb-md-0 large_icons_menu-item undefined undefined undefined col-12 col-sm-12 col-md-4 col-lg-3'
            )
            products = []

            for div in divs:
                product = {}
                datacatid = div.get('datacatid', '')
                dataitemid = div.get('dataitemid', '')

                if datacatid and dataitemid:
                    product['product_url'] = f"https://angeethipk.com/?item_id={dataitemid}%7C{datacatid}"

                    if datacatid == '400334':
                        product['food_category'] = "Fast Food"
                    elif datacatid == '407777':
                        product['food_category'] = "Deal"
                    elif datacatid == '407764':
                        product['food_category'] = "Deal"
                    elif datacatid == '401234':
                        product['food_category'] = "Desi"
                    elif datacatid == '400183':
                        product['food_category'] = "Desi"
                    elif datacatid == '400045':
                        product['food_category'] = "Handi"
                    elif datacatid == '400043':
                        product['food_category'] = "BBQ"
                    elif datacatid == '400042':
                        product['food_category'] = "Starter"
                    elif datacatid == '400047':
                        product['food_category'] = "Roll"
                    elif datacatid == '400048':
                        product['food_category'] = "Beverage"
                    elif datacatid == '400046':
                        product['food_category'] = "Naan"
                    elif datacatid == '400049':
                        product['food_category'] = "Add Ons"
                    else:
                        product['food_category'] = "Uncategorized"

                    title_tag = div.find('h2', style='color: rgb(33, 37, 41);')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)

                    description_tag = div.find('p', class_='truncated trancated-3')
                    product['description'] = description_tag.get_text(strip=True) if description_tag else ""

                    price_wrapper = div.find('div', class_='price-wrapper')
                    if price_wrapper:
                        original_price_tag = price_wrapper.find('span', style='text-decoration-line: line-through;')
                        if original_price_tag:
                            product['original_price'] = original_price_tag.get_text(strip=True).replace('Rs.', '').strip()

                        discount_price_tag = price_wrapper.find('span', class_='normal-price has-discount')
                        if discount_price_tag:
                            product['discount_price'] = discount_price_tag.get_text(strip=True).replace('Rs.', '').strip()
                        else:
                            price_tag = price_wrapper.find('span', class_='normal-price')
                            if price_tag:
                                product['original_price'] = price_tag.get_text(strip=True).replace('Rs.', '').strip()
                                product['discount_price'] = None

                    img_tag = div.find('img', class_='rounded-0')
                    if img_tag and img_tag.get('src'):
                        product['image_url'] = "https://angeethipk.com" + img_tag['src']

                    product['brand_id'] = ObjectId(brand_id)
                    products.append(product)

            return products

        products = await parse_products(html_file)

        for product in products:
            required_fields = [
                "title", "original_price", "image_url", "product_url", "brand_id", "food_category"
            ]

            if not all(product.get(field) for field in required_fields):
                print(f"Skipping product due to missing fields: {product}")
                continue

            # existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            # if not existing_product:
            #     new_product = FoodProduct(**product)
            #     await new_product.save()
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product["original_price"] or
                    existing_product.discount_price != product["discount_price"]
                )

                if price_changed:
                    # Update prices and the `updatedAt` timestamp
                    existing_product.original_price = product["original_price"]
                    existing_product.discount_price = product["discount_price"]
                    existing_product.updatedAt = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = FoodProduct(**product)
                await new_product.save()

        print("Angeethi data scraping and saving completed!")
        os.remove(html_file)
    @staticmethod
    async def getDeliziaData():
        # Step 1: Save or get Delizia brand in the database
        brand_name = "Delizia"
        brand = await FoodBrand.find_one({"brand_name": brand_name})

        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        brand_id = brand.id

        async def save_html_content():
            url = "https://www.delizia.pk/"
            webbrowser.open(url)
            time.sleep(5)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(2)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(2)

            js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(1.5)

            html_content = pyperclip.paste()
            file_name = "Delizia.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            pyautogui.hotkey('ctrl', 'w')
            return file_name

        html_file = await save_html_content()

        async def parse_products(input_html):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all('div', class_='p-0 mb-3 mb-md-0 large_icons_menu-item undefined undefined undefined col-12 col-sm-12 col-md-4 col-lg-3')
            products = []

            for div in divs:
                product = {}
                datacatid = div.get('datacatid', '')
                dataitemid = div.get('dataitemid', '')

                if datacatid and dataitemid:
                    product['product_url'] = f"https://www.delizia.pk/?item_id={dataitemid}%7C{datacatid}"

                    # Map product categories based on datacatid
                    if datacatid == '404128':
                        product['food_category'] = "Cake"
                    elif datacatid == '404129':
                        product['food_category'] = "Donut"
                    elif datacatid == '404130':
                        product['food_category'] = "Cupcake"
                    elif datacatid == '404131':
                        product['food_category'] = "Brownie"
                    elif datacatid == '404132':
                        product['food_category'] = "Dessert"
                    else:
                        product['food_category'] = "Uncategorized"

                    title_tag = div.find('h2', style='color: rgb(33, 37, 41);')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)

                    description_tag = div.find('p', class_='truncated trancated-3')
                    product['description'] = description_tag.get_text(strip=True) if description_tag else ""

                    price_wrapper = div.find('div', class_='price-wrapper')
                    if price_wrapper:
                        original_price_tag = price_wrapper.find('span', style='text-decoration-line: line-through;')

                        # Safely access original_price_tag
                        if original_price_tag and original_price_tag.get_text(strip=True):
                            product['original_price'] = original_price_tag.get_text(strip=True).replace('Rs.', '').replace('from', '').strip()

                        # Handling discount price
                        discount_price_tag = price_wrapper.find('span', class_='normal-price.has-discount')
                        if discount_price_tag and discount_price_tag.get_text(strip=True):
                            product['discount_price'] = discount_price_tag.get_text(strip=True).replace('Rs.', '').strip()
                        else:
                            price_tag = price_wrapper.find('span', class_='normal-price')
                            if price_tag and price_tag.get_text(strip=True):
                                product['original_price'] = price_tag.get_text(strip=True).replace('Rs.', '').replace('from', '').strip()

                    img_tag = div.find('img', class_='rounded-0')
                    if img_tag and img_tag.get('src'):
                        product['image_url'] = "https://www.delizia.pk" + img_tag['src']

                    product['brand_id'] = ObjectId(brand_id)
                    products.append(product)

            return products

        products = await parse_products(html_file)

        for product in products:
            required_fields = [
                "title", "original_price", "image_url", "product_url", "brand_id", "food_category"
            ]

            if not all(product.get(field) for field in required_fields):
                print(f"Skipping product due to missing fields: {product}")
                continue

            # existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            # if not existing_product:
            #     new_product = FoodProduct(**product)
            #     await new_product.save()
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product["original_price"] or
                    existing_product.discount_price != product["discount_price"]
                )

                if price_changed:
                    # Update prices and the `updatedAt` timestamp
                    existing_product.original_price = product["original_price"]
                    existing_product.discount_price = product["discount_price"]
                    existing_product.updatedAt = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = FoodProduct(**product)
                await new_product.save()

        print("Delizia data scraping and saving completed!")
        os.remove(html_file)
    @staticmethod
    async def getFoodsinnData():
    # Step 1: Save or get Foods Inn brand in the database
        brand_name = "Foods Inn"
        brand = await FoodBrand.find_one({"brand_name": brand_name})

        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        brand_id = brand.id

        async def save_html_content():
            url = "https://foodsinn.co/"
            webbrowser.open(url)
            time.sleep(5)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(2)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(2)

            js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(1.5)

            html_content = pyperclip.paste()

            parsed_url = urlparse(url)
            domain_name = parsed_url.netloc.split('.')[0]
            file_name = f"{domain_name}.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"HTML content has been saved to {os.path.abspath(file_name)}")
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(1.3)

            return file_name

        html_file = await save_html_content()

        async def parse_products(input_html):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all('div', class_='p-0 mb-md-0 m-0 mb-3 col-12 col-md-6')
            products = []

            for div in divs:
                product = {}

                datacatid = div.get('datacatid', '')
                dataitemid = div.get('dataitemid', '')

                if datacatid and dataitemid:
                    product['product_url'] = f"https://foodsinn.co/?item_id={dataitemid}%7C{datacatid}"

                    if datacatid == '8376':
                        product['food_category'] = "Deal"
                    elif datacatid == '7319':
                        product['food_category'] = "Deal"
                    elif datacatid == '7306':
                        product['food_category'] = "Starter"
                    elif datacatid == '7308':
                        product['food_category'] = "Burger"
                    elif datacatid == '403363':
                        product['food_category'] = "Sandwich"
                    elif datacatid == '7310':
                        product['food_category'] = "Broast"
                    elif datacatid == '7328':
                        product['food_category'] = "Steak"
                    elif datacatid == '7311':
                        product['food_category'] = "Pasta"
                    elif datacatid == '7312':
                        product['food_category'] = "Chinese"
                    elif datacatid == '7313':
                        product['food_category'] = "Chinese"
                    elif datacatid == '7314':
                        product['food_category'] = "BBQ"
                    elif datacatid == '7315':
                        product['food_category'] = "Chicken Karahi"
                    elif datacatid == '7329':
                        product['food_category'] = "Mutton Karahi"
                    elif datacatid == '7316':
                        product['food_category'] = "Handi"
                    elif datacatid == '7320':
                        product['food_category'] = "Platter"
                    elif datacatid == '7338':
                        product['food_category'] = "Roll"
                    elif datacatid == '402916':
                        product['food_category'] = "Kid"
                    elif datacatid == '7321':
                        product['food_category'] = "Naan"
                    elif datacatid == '7318':
                        product['food_category'] = "Dessert"
                    elif datacatid == '7317':
                        product['food_category'] = "Mocktail or Shake"
                    elif datacatid == '7322':
                        product['food_category'] = "Beverage"
                    elif datacatid == '403522':
                        product['food_category'] = "Hot Beverage"
                    elif datacatid == '7323':
                        product['food_category'] = "Add Ons"

                    title_tag = div.find('p', class_='truncated trancated-3')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)

                    description_tag = div.find('p', class_='truncated trancated-3')
                    if description_tag:
                        product['description'] = description_tag.get_text(strip=True)

                    price_wrapper = div.find('div', class_='price-wrapper')
                    if price_wrapper:
                        price_tag = price_wrapper.find('span', class_='normal-price')
                        if price_tag:
                            product['original_price'] = price_tag.get_text(strip=True).replace('Rs.', '').strip()
                            product['discount_price'] = None

                    img_tag = div.find('img', class_='img-fluid rounded-2')
                    if img_tag and img_tag.get('src'):
                        product['image_url'] = "https://foodsinn.co" + img_tag['src']

                    product['brand_id'] = ObjectId(brand_id)
                    products.append(product)

            return products

        products = await parse_products(html_file)

        for product in products:
            required_fields = [
                "title", "original_price",
                "image_url", "product_url", "brand_id", "food_category"
            ]

            if not all(product.get(field) for field in required_fields):
                print(f"Skipping product due to missing fields: {product}")
                continue

            # existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            # if not existing_product:
            #     new_product = FoodProduct(**product)
            #     await new_product.save()
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product["original_price"] or
                    existing_product.discount_price != product["discount_price"]
                )

                if price_changed:
                    # Update prices and the `updatedAt` timestamp
                    existing_product.original_price = product["original_price"]
                    existing_product.discount_price = product["discount_price"]
                    existing_product.updatedAt = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = FoodProduct(**product)
                await new_product.save()

        print("Foods Inn data scraping and saving completed!")
        os.remove(html_file)
    @staticmethod
    async def getGinsoyData():
        # Step 1: Save or get the Ginsoy brand in the database
        brand_name = "Ginsoy"
        brand = await FoodBrand.find_one({"brand_name": brand_name})

        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        brand_id = brand.id

        async def save_html_content():
            url = "https://order.ginsoy.com/"
            webbrowser.open(url)
            time.sleep(14)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(2)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(2)

            js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(1.5)

            html_content = pyperclip.paste()

            parsed_url = urlparse(url)
            domain_name = parsed_url.netloc.split('.')[0]
            file_name = f"{domain_name}.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"HTML content has been saved to {os.path.abspath(file_name)}")
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(1.3)

            return file_name

        html_file = await save_html_content()

        async def parse_products(input_html):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all('div', class_='p-0 mb-3 mb-md-0 large_icons_menu-item undefined undefined undefined col-12 col-sm-12 col-md-4 col-lg-3')
            products = []

            for div in divs:
                product = {}

                datacatid = div.get('datacatid', '')
                dataitemid = div.get('dataitemid', '')

                if datacatid and dataitemid:
                    product['product_url'] = f"https://order.ginsoy.com/?item_id={dataitemid}%7C{datacatid}"

                    # Determine the food category
                    if datacatid == '415331':
                        product['food_category'] = "Starter"
                    elif datacatid == '415329':
                        product['food_category'] = "Soup"
                    elif datacatid == '415336':
                        product['food_category'] = "Chinese"
                    elif datacatid == '415531':
                        product['food_category'] = "Soup"
                    elif datacatid == '415532':
                        product['food_category'] = "Chinese"
                    elif datacatid == '415334':
                        product['food_category'] = "Sea Food"
                    elif datacatid == '415563':
                        product['food_category'] = "Noodle"
                    elif datacatid == '415337':
                        product['food_category'] = "Rice"
                    elif datacatid == '415338':
                        product['food_category'] = "Kid"
                    elif datacatid == '415339':
                        product['food_category'] = "Mocktail or Shake"
                    elif datacatid == '415342':
                        product['food_category'] = "Beverage"

                    title_tag = div.find('h2', style='color: rgb(33, 37, 41);')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)

                    description_tag = div.find('p', class_='truncated trancated-3')
                    if description_tag:
                        product['description'] = description_tag.get_text(strip=True)

                    price_wrapper = div.find('div', class_='price-wrapper')
                    if price_wrapper:
                        original_price_tag = price_wrapper.find('span', style='text-decoration-line: line-through;')
                        if original_price_tag:
                            original_price = original_price_tag.get_text(strip=True).replace('Rs.', '').strip()
                            if original_price:
                                product['original_price'] = original_price

                        discount_price_tag = price_wrapper.find('span', class_='normal-price has-discount')
                        if discount_price_tag:
                            discount_price = discount_price_tag.get_text(strip=True).replace('Rs.', '').strip()
                            if discount_price:
                                product['discount_price'] = discount_price

                        if 'original_price' not in product:
                            price_tag = price_wrapper.find('span', class_='normal-price')
                            if price_tag:
                                price = price_tag.get_text(strip=True).replace('Rs.', '').strip()
                                if price:
                                    product['product_price'] = price

                    img_tag = div.find('img', class_='rounded-0')
                    if img_tag and img_tag.get('src'):
                        product['image_url'] = "https://order.ginsoy.com" + img_tag['src']

                    product['brand_id'] = ObjectId(brand_id)
                    products.append(product)

            return products

        products = await parse_products(html_file)

        for product in products:
            required_fields = [
                "title", "original_price",
                "image_url", "product_url", "brand_id", "food_category"
            ]

            if not all(product.get(field) for field in required_fields):
                print(f"Skipping product due to missing fields: {product}")
                continue

            # existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            # if not existing_product:
            #     new_product = FoodProduct(**product)
            #     await new_product.save()
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product["original_price"] or
                    existing_product.discount_price != product["discount_price"]
                )

                if price_changed:
                    # Update prices and the `updatedAt` timestamp
                    existing_product.original_price = product["original_price"]
                    existing_product.discount_price = product["discount_price"]
                    existing_product.updatedAt = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = FoodProduct(**product)
                await new_product.save()

        print("Ginsoy data scraping and saving completed!")
        os.remove(html_file)
    
    @staticmethod
    async def getPizzaPointData():
        # Step 1: Save or get Pizza Point brand in the database
        brand_name = "Pizza Point"
        brand = await FoodBrand.find_one({"brand_name": brand_name})

        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        brand_id = brand.id

        async def save_html_content():
            url = "https://www.pizzapoint.com.pk/"
            webbrowser.open(url)
            time.sleep(20)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(3)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(3)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(2)

            js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(1.5)

            html_content = pyperclip.paste()
            file_name = "PizzaPoint.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            pyautogui.hotkey('ctrl', 'w')
            return file_name

        html_file = await save_html_content()

        async def parse_products(input_html):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all(
                'div',
                class_='p-0 mb-3 mb-md-0 large_icons_menu-item undefined undefined undefined col-12 col-sm-12 col-md-4 col-lg-3'
            )
            products = []

            for div in divs:
                product = {}
                datacatid = div.get('datacatid', '')
                dataitemid = div.get('dataitemid', '')

                if datacatid and dataitemid:
                    product['product_url'] = f"https://www.pizzapoint.com.pk/?item_id={dataitemid}%7C{datacatid}"

                    if datacatid == '420153' or datacatid == '418318' or datacatid == '418320':
                        product['food_category'] = "Deal"
                    elif datacatid == '5833':
                        product['food_category'] = "Starter"
                    elif datacatid in ['418322', '418323', '418324']:
                        product['food_category'] = "Pizza"
                    elif datacatid == '418325':
                        product['food_category'] = "Sandwich"
                    elif datacatid == '418326':
                        product['food_category'] = "Pasta"
                    elif datacatid == '418327':
                        product['food_category'] = "Fries"
                    elif datacatid == '418333':
                        product['food_category'] = "Add Ons"
                    elif datacatid == '5835':
                        product['food_category'] = "Beverage"
                    else:
                        product['food_category'] = "Uncategorized"

                    title_tag = div.find('h2', style='color: rgb(33, 37, 41);')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)

                    description_tag = div.find('p', class_='truncated trancated-3')
                    product['description'] = description_tag.get_text(strip=True) if description_tag else ""

                    price_wrapper = div.find('div', class_='price-wrapper')
                    if price_wrapper:
                        original_price_tag = price_wrapper.find('span', style='text-decoration-line: line-through;')
                        if original_price_tag:
                            product['original_price'] = original_price_tag.get_text(strip=True).replace('Rs.', '').strip()

                        discount_price_tag = price_wrapper.find('span', class_='normal-price has-discount')
                        if discount_price_tag:
                            product['discount_price'] = discount_price_tag.get_text(strip=True).replace('Rs.', '').strip()
                        else:
                            price_tag = price_wrapper.find('span', class_='normal-price')
                            if price_tag:
                                product['original_price'] = price_tag.get_text(strip=True).replace('Rs.', '').strip()
                                product['discount_price'] = None

                    img_tag = div.find('img', class_='rounded-0')
                    if img_tag and img_tag.get('src'):
                        product['image_url'] = "https://www.pizzapoint.com.pk" + img_tag['src']

                    product['brand_id'] = ObjectId(brand_id)
                    products.append(product)

            return products

        products = await parse_products(html_file)

        for product in products:
            required_fields = [
                "title", "original_price", "image_url", "product_url", "brand_id", "food_category"
            ]

            if not all(product.get(field) for field in required_fields):
                print(f"Skipping product due to missing fields: {product}")
                continue

            # existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            # if not existing_product:
            #     new_product = FoodProduct(**product)
            #     await new_product.save()
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product["original_price"] or
                    existing_product.discount_price != product["discount_price"]
                )

                if price_changed:
                    # Update prices and the `updatedAt` timestamp
                    existing_product.original_price = product["original_price"]
                    existing_product.discount_price = product["discount_price"]
                    existing_product.updatedAt = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = FoodProduct(**product)
                await new_product.save()

        print("Pizza Point data scraping and saving completed!")
        os.remove(html_file)

    @staticmethod
    async def getHotNSpicyData():
        # Step 1: Save or get Hot n Spicy brand in the database
        brand_name = "Hot n Spicy"
        brand = await FoodBrand.find_one({"brand_name": brand_name})

        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        brand_id = brand.id

        async def save_html_content():
            url = "https://hot-nspicy.com/"
            webbrowser.open(url)
            time.sleep(20)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(3)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(3)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(2)

            js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(1.5)
            pyautogui.press('enter')
            time.sleep(1.5)

            html_content = pyperclip.paste()
            file_name = "HotnSpicy.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            pyautogui.hotkey('ctrl', 'w')
            return file_name

        html_file = await save_html_content()

        async def parse_products(input_html):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all('div', class_='p-0 mb-md-0 m-0 mb-0 col-12 col-md-6')
            products = []

            for div in divs:
                product = {}
                datacatid = div.get('datacatid', '')
                dataitemid = div.get('dataitemid', '')

                if datacatid and dataitemid:
                    product['product_url'] = f"https://hot-nspicy.com/?item_id={dataitemid}%7C{datacatid}"

                    # Assign categories based on `datacatid`
                    category_map = {
                        '411681': "Platter",
                        '408834': "Soup",
                        '408835': "Roll",
                        '408836': "BBQ",
                        '408837': "Naan",
                        '408838': "Chinese",
                        '408839': "Starter",
                        '408840': "Chicken Karahi",
                        '408841': "Mutton Karahi",
                        '408842': "Handi",
                        '408843': "Rice",
                        '408845': "Fast Food",
                        '408846': "Dessert",
                        '408848': "Mocktail or Shake",
                        '408849': "Beverage",
                        '408851': "Add Ons",
                        '400707': "Desi",
                        '408856': "Juice",
                        '402198': "Hot Beverage",
                    }
                    product['food_category'] = category_map.get(datacatid, "Uncategorized")

                    title_tag = div.find('h2', style='color: rgb(33, 37, 41);')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)

                    description_tag = div.find('p', class_='truncated trancated-3')
                    product['description'] = description_tag.get_text(strip=True) if description_tag else ""

                    price_wrapper = div.find('div', class_='price-wrapper')
                    if price_wrapper:
                        original_price_tag = price_wrapper.find('span', style='text-decoration-line: line-through;')
                        if original_price_tag:
                            product['original_price'] = original_price_tag.get_text(strip=True).replace('Rs.', '').strip()

                        discount_price_tag = price_wrapper.find('span', class_='normal-price has-discount')
                        if discount_price_tag:
                            product['discount_price'] = discount_price_tag.get_text(strip=True).replace('Rs.', '').strip()
                        else:
                            price_tag = price_wrapper.find('span', class_='normal-price')
                            if price_tag:
                                product['original_price'] = price_tag.get_text(strip=True).replace('Rs.', '').strip()
                                product['discount_price'] = None

                    img_tag = div.find('img', class_='img-fluid rounded-2')
                    if img_tag and img_tag.get('src'):
                        product['image_url'] = "https://hot-nspicy.com/" + img_tag['src']

                    product['brand_id'] = ObjectId(brand_id)
                    products.append(product)

            return products

        products = await parse_products(html_file)

        for product in products:
            required_fields = [
                "title", "original_price", "image_url", "product_url", "brand_id", "food_category"
            ]

            if not all(product.get(field) for field in required_fields):
                print(f"Skipping product due to missing fields: {product}")
                continue

            # existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            # if not existing_product:
            #     new_product = FoodProduct(**product)
            #     await new_product.save()
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})

            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product["original_price"] or
                    existing_product.discount_price != product["discount_price"]
                )

                if price_changed:
                    # Update prices and the `updatedAt` timestamp
                    existing_product.original_price = product["original_price"]
                    existing_product.discount_price = product["discount_price"]
                    existing_product.updatedAt = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = FoodProduct(**product)
                await new_product.save()

        print("Hot n Spicy data scraping and saving completed!")
        os.remove(html_file)

    @staticmethod
    async def getAllBrandsBanner():
        # Mapping of domain names to brand names
        brand_name_mapping = {
            "angeethipk.com": "Angeethi",
            "delizia.pk": "Delizia",
            "foodsinn.co": "Foods Inn",
            "ginsoy.com": "Ginsoy",
            "hot-nspicy.com": "Hot n Spicy",
            "kababjeesfriedchicken.com": "Kababjees Fried Chicken",
            "karachibroast.co": "Karachi Broast",
            "kaybees.com.pk": "Kaybees",
            "pizzapoint.com.pk": "Pizza Point",
            "jhr.tooso.pk": "Tooso"
        }
        
        urls = [
            "https://angeethipk.com/",
            "https://www.delizia.pk/",
            "https://foodsinn.co/",
            "https://www.ginsoy.com/",
            "https://hot-nspicy.com/",
            "https://www.kababjeesfriedchicken.com/",
            "https://www.karachibroast.co/",
            "https://www.kaybees.com.pk/",
            "https://www.pizzapoint.com.pk/",
            "https://jhr.tooso.pk/"
        ]
        
        async def save_banners_content(url):
            webbrowser.open(url)
            time.sleep(8)

            pyautogui.hotkey('ctrl', 'shift', 'c')
            time.sleep(3)
            pyautogui.hotkey('ctrl', ']')
            time.sleep(3)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(5)

            js_command = 'copy(document.getElementsByClassName("carousel slide")[0].outerHTML);'
            pyautogui.write(js_command)
            time.sleep(2.5)
            pyautogui.press('enter')
            time.sleep(1.5)

            html_content = pyperclip.paste()
            file_name = f"{urlparse(url).netloc}.html"

            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"HTML content for {url} has been saved to {os.path.abspath(file_name)}")
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(1.3)
            return file_name

        async def extract_food_menu(input_html, url):
            with open(input_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            divs = soup.find_all('div', class_='position-relative w-100 carousel-img-container')
            images = []

            # Get the first image URL for each website
            if divs:
                img_tag = divs[0].find('img', class_='')
                if img_tag and img_tag.get('src'):
                    img_url = img_tag['src']
                    full_img_url = f"{url}{img_url}"
                    images.append(full_img_url)

            if images:
                domain_name = urlparse(url).netloc  # Get the domain name
                brand_name = brand_name_mapping.get(domain_name)  # Map to the brand name
                
                if brand_name:
                    brand = await FoodBrand.find_one({"brand_name": brand_name})

                    if brand:
                        # If the brand exists, update the banner image
                        brand.banner_image = images[0]
                        brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                        await brand.save()
                        print(f"Updated {brand_name} brand banner image URL: {images[0]}")
                    else:
                        # If the brand doesn't exist, create a new brand and save it
                        brand = FoodBrand(brand_name=brand_name, banner_image=images[0])
                        await brand.save()
                        print(f"Created new {brand_name} brand and saved banner image URL: {images[0]}")
                else:
                    print(f"Brand name for domain {domain_name} not found in mapping.")

            os.remove(input_html)
            print(f"Temporary file {input_html} has been removed.")
        
        # Process each URL
        for url in urls:
            html_file = await save_banners_content(url)
            await extract_food_menu(html_file, url)

        print("All brand banners have been processed!")


def schedule_food_scraping():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(FoodService.getKababjeesFriedData, "interval", minutes=11111)
    scheduler.add_job(FoodService.getAngeethiData, "interval", minutes=10000)
    scheduler.add_job(FoodService.getDeliziaData, "interval", minutes=10000)
    scheduler.add_job(FoodService.getFoodsinnData, "interval", minutes=10000)
    scheduler.add_job(FoodService.getGinsoyData, "interval", minutes=10000)
    scheduler.add_job(FoodService.getPizzaPointData, "interval", minutes=10000)
    scheduler.add_job(FoodService.getHotNSpicyData, "interval", minutes=10000)
    scheduler.add_job(FoodService.getAllBrandsBanner, "interval", minutes=10001)
    scheduler.start()
    print("Food Scheduler Started!")

