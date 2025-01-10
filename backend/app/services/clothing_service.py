import requests
from bs4 import BeautifulSoup
import json
import os
from app.models.clothing_brand_model import ClothingBrand
from app.models.clothing_product_model import ClothingProduct
from apscheduler.schedulers.background import BackgroundScheduler
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import re
from datetime import datetime

class ClothingService:
    @staticmethod
    async def getKhaadiData():
        # Step 1: Scrape Khaadi sales data
        url = "https://pk.khaadi.com/sale/?start=0&sz=1109"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Error fetching data:", e)
            return

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        filtered_divs = soup.find_all("div", class_="tile col-6 col-md-4 col-lg-3")

        # Step 2: Save or get the Khaadi brand in the database
        brand_name = "Khaadi"
        brand = await ClothingBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = ClothingBrand(brand_name=brand_name)
            await brand.save()
        brand_id = brand.id

        # Step 3: Extract and save product data
        for div in filtered_divs:
            product_info = {
                "brand_id": brand_id,
                "title": None,
                "product_page": None,
                "image_url": None,
                "original_price": None,
                "sale_price": None,
            }

            # Extract product details
            image_tag = div.find("img", class_="tile-image")
            if image_tag:
                product_info["image_url"] = image_tag.get("src")

            anchor_tag = div.find("a", class_="plp-tap-mobile plpRedirectPdp")
            if anchor_tag:
                product_info["product_page"] = "https://pk.khaadi.com" + anchor_tag.get("href")

            product = div.find("div", class_="product")
            if product:
                gtm_data = product.get("data-gtmdata")
                if gtm_data:
                    gtm_json = json.loads(gtm_data)
                    product_info["title"] = gtm_json.get("name")

            sales_price_span = div.find("span", class_="sales reduced-price d-inline-block")
            if sales_price_span:
                sale_price_value = sales_price_span.find("span", class_="value cc-price")
                if sale_price_value:
                    product_info["sale_price"] = sale_price_value.get("content")

            original_price_span = div.find("span", class_="strike-through list")
            if original_price_span:
                original_price_value = original_price_span.find("span", class_="value cc-price")
                if original_price_value:
                    product_info["original_price"] = original_price_value.get("content")

            # Validation: Skip saving if any field is missing
            if not all(product_info.values()):  # Check if any field in product_info is None or empty
                print(f"Skipping product due to missing fields: {product_info}")
                continue

            # existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
            # if not existing_product:
            #     # If the product does not exist, insert it into the database
            #     product = ClothingProduct(**product_info)
            #     await product.save()
            existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
            if existing_product:
                # Check for changes in prices
                price_changed = (
                    existing_product.original_price != product_info["original_price"] or
                    existing_product.sale_price != product_info["sale_price"]
                )

                if price_changed:
                    # Update prices and updated_at timestamp
                    existing_product.original_price = product_info["original_price"]
                    existing_product.sale_price = product_info["sale_price"]
                    existing_product.updated_at = datetime.utcnow()
                    await existing_product.save()
                    print(f"Updated product: {existing_product.title}")
                else:
                    print(f"No changes for product: {existing_product.title}")
            else:
                # Insert new product
                new_product = ClothingProduct(**product_info)
                await new_product.save()

        print("Khaadi data scraping and saving completed!")

    @staticmethod
    async def getDhanakData():
        base_url = "https://dhanak.com.pk/collections/sale?page="
        num_pages = 5  # Number of pages to scrape

        # Step 1: Save or get the Dhanak brand in the database
        brand_name = "Dhanak"
        brand = await ClothingBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = ClothingBrand(brand_name=brand_name)
            await brand.save()
        brand_id = brand.id

        # Step 2: Scrape Dhanak sales data
        for page in range(1, num_pages + 1):
            url = f"{base_url}{page}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            products = soup.find_all("li", class_="product")

            for product in products:
                product_info = {
                    "brand_id": ObjectId(brand_id),
                    "title": None,
                    "product_page": None,
                    "image_url": None,
                    "original_price": None,
                    "sale_price": None,
                }

                # Extract product details
                title_tag = product.find("a", class_="card-title link-underline card-title-ellipsis")
                if title_tag:
                    product_info["title"] = title_tag.find("span", class_="text").get_text(strip=True)
                    product_info["product_page"] = "https://dhanak.com.pk" + title_tag["href"]

                card_media_div = product.find(
                    "div", class_="card-media card-media--adapt media--hover-effect media--loading-effect"
                )
                if card_media_div:
                    image_tag = card_media_div.find("img", alt=True)
                    if image_tag and "data-srcset" in image_tag.attrs:
                        data_srcset = image_tag["data-srcset"].split(", ")
                        product_info["image_url"] = ClothingService.get_last_url(data_srcset)

                price_sale_div = product.find("div", class_="price__sale")
                if price_sale_div:
                    original_price_tag = price_sale_div.find("s", class_="price-item--regular")
                    sale_price_tag = price_sale_div.find("span", class_="price-item--sale")
                    if original_price_tag:
                        product_info["original_price"] = ClothingService.format_price(
                            original_price_tag.get_text(strip=True).replace("Rs.", "").strip()
                        )
                    if sale_price_tag:
                        product_info["sale_price"] = ClothingService.format_price(
                            sale_price_tag.get_text(strip=True).replace("Rs.", "").strip()
                        )

                # Validation: Skip saving if any field is missing
                if not all(product_info.values()):
                    print(f"Skipping product due to missing fields: {product_info}")
                    continue

                # Check if the product already exists
                # existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                # if not existing_product:
                #     # If the product does not exist, insert it into the database
                #     product = ClothingProduct(**product_info)
                #     await product.save()
                #     print(f"Saved product: {product_info}")
                existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                if existing_product:
                    # Check for changes in prices
                    price_changed = (
                        existing_product.original_price != product_info["original_price"] or
                        existing_product.sale_price != product_info["sale_price"]
                    )

                    if price_changed:
                        # Update prices and updated_at timestamp
                        existing_product.original_price = product_info["original_price"]
                        existing_product.sale_price = product_info["sale_price"]
                        existing_product.updated_at = datetime.utcnow()
                        await existing_product.save()
                        print(f"Updated product: {existing_product.title}")
                    else:
                        print(f"No changes for product: {existing_product.title}")
                else:
                    # Insert new product
                    new_product = ClothingProduct(**product_info)
                    await new_product.save()


        print("Dhanak data scraping and saving completed!")

    @staticmethod
    async def getAlkaramData():
        base_url = "https://www.alkaramstudio.com/collections/sale?page="
        num_pages = 147  # Number of pages to scrape

        # Step 1: Save or get the Alkaram brand in the database
        brand_name = "Alkaram"
        brand = await ClothingBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = ClothingBrand(brand_name=brand_name)
            await brand.save()
        brand_id = brand.id

        # Step 2: Scrape Alkaram sales data
        for page in range(1, num_pages + 1):
            url = f"{base_url}{page}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            products = soup.find_all("div", class_="t4s-product")

            for product in products:
                product_info = {
                    "brand_id": ObjectId(brand_id),
                    "title": None,
                    "product_page": None,
                    "image_url": None,
                    "original_price": None,
                    "sale_price": None,
                }

                # Extract product details
                title_tag = product.find("h3", class_="t4s-product-title")
                if title_tag and title_tag.find("a"):
                    product_info["title"] = title_tag.get_text(strip=True)
                    href = title_tag.find("a")["href"]
                    product_info["product_page"] = f"https://www.alkaramstudio.com{href}"

                price_div = product.find("div", class_="t4s-product-price")
                if price_div:
                    original_price_tag = price_div.find("del")
                    sale_price_tag = price_div.find("ins")

                    if original_price_tag:
                        product_info["original_price"] = original_price_tag.get_text(strip=True)

                    if sale_price_tag:
                        product_info["sale_price"] = sale_price_tag.get_text(strip=True)

                image_tag = product.find("noscript")
                if image_tag and image_tag.find("img"):
                    img_src = image_tag.find("img")['src']
                    product_info["image_url"] = f"https:{img_src}"

                if not all(product_info.values()):
                    print(f"Skipping product due to missing fields: {product_info}")
                    continue

                # Save product directly to database without validation
                # existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                # if not existing_product:
                #     product = ClothingProduct(**product_info)
                #     await product.save()
                existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                if existing_product:
                    # Check for changes in prices
                    price_changed = (
                        existing_product.original_price != product_info["original_price"] or
                        existing_product.sale_price != product_info["sale_price"]
                    )

                    if price_changed:
                        # Update prices and updated_at timestamp
                        existing_product.original_price = product_info["original_price"]
                        existing_product.sale_price = product_info["sale_price"]
                        existing_product.updated_at = datetime.utcnow()
                        await existing_product.save()
                        print(f"Updated product: {existing_product.title}")
                    else:
                        print(f"No changes for product: {existing_product.title}")
                else:
                    # Insert new product
                    new_product = ClothingProduct(**product_info)
                    await new_product.save()

        print("Alkaram data scraping and saving completed!")

    @staticmethod
    async def getJjData():
        # Step 1: Save or get the J. brand in the database
        brand_name = "J."
        brand = await ClothingBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = ClothingBrand(brand_name=brand_name)
            await brand.save()
        brand_id = brand.id

        # Step 2: Scrape Junaid Jamshed sales data
        base_url = "https://www.junaidjamshed.com/sale.html?p="
        num_pages = 6  # Adjust as per the number of pages to scrape

        for page in range(1, num_pages + 1):
            url = f"{base_url}{page}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            product_items = soup.find_all("div", class_="product-item-info hover-animation-none")

            for item in product_items:
                product_info = {
                    "brand_id": ObjectId(brand_id),
                    "title": None,
                    "product_page": None,
                    "image_url": None,
                    "original_price": None,
                    "sale_price": None,
                }

                # Extract product details
                image_tag = item.find("img", class_="product-image-photo")
                if image_tag:
                    product_info["image_url"] = image_tag.get("data-original")

                link_tag = item.find("a", class_="product-item-link")
                if link_tag:
                    product_info["product_page"] = link_tag.get("href")
                    product_info["title"] = link_tag.get_text(strip=True)

                price_box = item.find("div", class_="price-box price-final_price")
                if price_box:
                    special_price_tag = price_box.find("span", {"data-price-type": "finalPrice"})
                    if special_price_tag:
                        product_info["sale_price"] = special_price_tag.get_text(strip=True)

                    old_price_tag = price_box.find("span", {"data-price-type": "oldPrice"})
                    if old_price_tag:
                        product_info["original_price"] = old_price_tag.get_text(strip=True)

                # Validation: Skip saving if any field is missing
                if not all(product_info.values()):
                    print(f"Skipping product due to missing fields: {product_info}")
                    continue

                # Check if the product already exists
                # existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                # if not existing_product:
                #     # If the product does not exist, insert it into the database
                #     product = ClothingProduct(**product_info)
                #     await product.save()
                #     print(f"Saved product: {product_info}")
                existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                if existing_product:
                    # Check for changes in prices
                    price_changed = (
                        existing_product.original_price != product_info["original_price"] or
                        existing_product.sale_price != product_info["sale_price"]
                    )

                    if price_changed:
                        # Update prices and updated_at timestamp
                        existing_product.original_price = product_info["original_price"]
                        existing_product.sale_price = product_info["sale_price"]
                        existing_product.updated_at = datetime.utcnow()
                        await existing_product.save()
                        print(f"Updated product: {existing_product.title}")
                    else:
                        print(f"No changes for product: {existing_product.title}")
                else:
                    # Insert new product
                    new_product = ClothingProduct(**product_info)
                    await new_product.save()

        print("Junaid Jamshed data scraping and saving completed!")
    
    @staticmethod
    async def getOutfittersData():
        base_url = "https://outfitters.com.pk/collections/men-end-of-season-sale?page="
        num_pages = 37  # Number of pages to scrape

        # Step 1: Save or get the Outfitters brand in the database
        brand_name = "Outfitters"
        brand = await ClothingBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = ClothingBrand(brand_name=brand_name)
            await brand.save()
        brand_id = brand.id

        # Step 2: Scrape Outfitters sales data
        for page in range(1, num_pages + 1):
            url = f"{base_url}{page}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            sale_items = soup.find_all("li", class_="grid__item grid-item-list")

            for item in sale_items:
                product_info = {
                    "brand_id": ObjectId(brand_id),
                    "title": None,
                    "product_page": None,
                    "image_url": None,
                    "original_price": None,
                    "sale_price": None,
                }

                # Extract product details
                title_tag = item.find("h3", class_="card__heading h5")
                if title_tag:
                    link_tag = title_tag.find("a", class_="product-link-main")
                    if link_tag:
                        product_info["title"] = link_tag.get_text(strip=True)
                        product_info["product_page"] = "https://outfitters.com.pk" + link_tag.get("href")

                image_container = item.find("div", class_="media media--transparent media--hover-effect swiper-slide")
                if image_container:
                    image_tag = image_container.find("img", class_="motion-reduce image-second")
                    if image_tag and image_tag.get("srcset"):
                        product_info["image_url"] = ClothingService.get_last_url(image_tag.get("srcset"))

                price_div = item.find("div", class_="price__sale")
                if price_div:
                    original_price_tag = price_div.find("s", class_="price-item price-item--regular")
                    if original_price_tag:
                        money_tag = original_price_tag.find("span", class_="money")
                        if money_tag:
                            product_info["original_price"] = money_tag.get_text(strip=True)

                    sale_price_tag = price_div.find("span", class_="price-item--sale")
                    if sale_price_tag:
                        sales_price_value = sale_price_tag.get_text(strip=True)
                        clean_price = sales_price_value.split('-')[0]
                        product_info["sale_price"] = clean_price

                # Validation: Skip saving if any field is missing
                if not all(product_info.values()):
                    print(f"Skipping product due to missing fields: {product_info}")
                    continue

                # Check if the product already exists
                # existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                # if not existing_product:
                #     # If the product does not exist, insert it into the database
                #     product = ClothingProduct(**product_info)
                #     await product.save()
                #     print(f"Saved product: {product_info}")
                existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                if existing_product:
                    # Check for changes in prices
                    price_changed = (
                        existing_product.original_price != product_info["original_price"] or
                        existing_product.sale_price != product_info["sale_price"]
                    )

                    if price_changed:
                        # Update prices and updated_at timestamp
                        existing_product.original_price = product_info["original_price"]
                        existing_product.sale_price = product_info["sale_price"]
                        existing_product.updated_at = datetime.utcnow()
                        await existing_product.save()
                        print(f"Updated product: {existing_product.title}")
                    else:
                        print(f"No changes for product: {existing_product.title}")
                else:
                    # Insert new product
                    new_product = ClothingProduct(**product_info)
                    await new_product.save()

        print("Outfitters data scraping and saving completed!")

    @staticmethod
    async def getSayaData():
        base_url = "https://saya.pk/collections/summer-season-end-sale-upto-50-off-on-stitched-unstitched-printed-embroidered-lawn-cotton-jacqaurd-cambric-chiffon-all-fabric?page="
        num_pages = 164  # Total pages to scrape

        # Step 1: Save or get the Saya brand in the database
        brand_name = "Saya"
        brand = await ClothingBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = ClothingBrand(brand_name=brand_name)
            await brand.save()
        brand_id = brand.id

        # Step 2: Scrape Saya sales data
        for page in range(1, num_pages + 1):
            url = f"{base_url}{page}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            sale_items = soup.find_all("div", class_="t4s-product-wrapper")

            for item in sale_items:
                product_info = {
                    "brand_id": ObjectId(brand_id),
                    "title": None,
                    "product_page": None,
                    "image_url": None,
                    "original_price": None,
                    "sale_price": None,
                }

                # Extract product details
                title_tag = item.find("h3", class_="t4s-product-title")
                if title_tag:
                    link_tag = title_tag.find("a")
                    if link_tag:
                        product_info["title"] = link_tag.get_text(strip=True)
                        product_info["product_page"] = link_tag.get("href")
                        if product_info["product_page"]:
                            product_info["product_page"] = (
                                "https://saya.pk" + product_info["product_page"]
                            )

                image_tag = item.find("noscript")
                if image_tag:
                    img_tag = image_tag.find("img", class_="t4s-product-main-img")
                    if img_tag:
                        image_url = img_tag.get("src")
                        if image_url.startswith("//"):
                            image_url = "https:" + image_url
                        product_info["image_url"] = image_url

                price_div = item.find("div", class_="t4s-product-price")
                if price_div:
                    price_spans = price_div.find_all("span", class_="money")
                    if len(price_spans) > 1:
                        product_info["sale_price"] = price_spans[0].get_text(strip=True)
                        product_info["original_price"] = price_spans[1].get_text(strip=True)

                # Validation: Skip saving if any field is missing
                if not all(product_info.values()):
                    print(f"Skipping product due to missing fields: {product_info}")
                    continue

                # Check if the product already exists
                # existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                # if not existing_product:
                #     # If the product does not exist, insert it into the database
                #     product = ClothingProduct(**product_info)
                #     await product.save()
                #     print(f"Saved product: {product_info}")
                existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                if existing_product:
                    # Check for changes in prices
                    price_changed = (
                        existing_product.original_price != product_info["original_price"] or
                        existing_product.sale_price != product_info["sale_price"]
                    )

                    if price_changed:
                        # Update prices and updated_at timestamp
                        existing_product.original_price = product_info["original_price"]
                        existing_product.sale_price = product_info["sale_price"]
                        existing_product.updated_at = datetime.utcnow()
                        await existing_product.save()
                        print(f"Updated product: {existing_product.title}")
                    else:
                        print(f"No changes for product: {existing_product.title}")
                else:
                    # Insert new product
                    new_product = ClothingProduct(**product_info)
                    await new_product.save()

        print("Saya data scraping and saving completed!")

    @staticmethod
    async def getZeenData():
        base_url = "https://zeenwoman.com/collections/sale?page="
        num_pages = 9  # Number of pages to scrape

        # Step 1: Save or get the Zeen brand in the database
        brand_name = "Zeen"
        brand = await ClothingBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = ClothingBrand(brand_name=brand_name)
            await brand.save()
        brand_id = brand.id

        # Step 2: Scrape Zeen sales data
        for page in range(1, num_pages + 1):
            url = f"{base_url}{page}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            sale_items = soup.find_all("div", class_="t4s-product")

            for item in sale_items:
                product_info = {
                    "brand_id": ObjectId(brand_id),
                    "title": None,
                    "product_page": None,
                    "image_url": None,
                    "original_price": None,
                    "sale_price": None,
                }

                # Extract product details
                title_tag = item.find("h3", class_="t4s-product-title")
                if title_tag:
                    link_tag = title_tag.find("a")
                    if link_tag:
                        product_info["title"] = title_tag.get_text(strip=True)
                        product_info["product_page"] = "https://zeenwoman.com" + link_tag.get("href")

                image_tag = item.find("noscript")
                if image_tag:
                    img = image_tag.find("img", class_="t4s-product-main-img")
                    if img:
                        image_url = img.get("src")
                        if image_url.startswith("//"):  # Fix relative URL
                            image_url = "https:" + image_url
                        product_info["image_url"] = image_url

                price_div = item.find("div", class_="t4s-product-price")
                if price_div:
                    original_price_tag = price_div.find("del")
                    if original_price_tag:
                        product_info["original_price"] = original_price_tag.get_text(strip=True)

                    sale_price_tag = price_div.find("ins")
                    if sale_price_tag:
                        product_info["sale_price"] = sale_price_tag.get_text(strip=True)

                # Validation: Skip saving if any field is missing
                if not all(product_info.values()):
                    print(f"Skipping product due to missing fields: {product_info}")
                    continue

                # Check if the product already exists
                # existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                # if not existing_product:
                #     # If the product does not exist, insert it into the database
                #     product = ClothingProduct(**product_info)
                #     await product.save()
                existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
                if existing_product:
                    # Check for changes in prices
                    price_changed = (
                        existing_product.original_price != product_info["original_price"] or
                        existing_product.sale_price != product_info["sale_price"]
                    )

                    if price_changed:
                        # Update prices and updated_at timestamp
                        existing_product.original_price = product_info["original_price"]
                        existing_product.sale_price = product_info["sale_price"]
                        existing_product.updated_at = datetime.utcnow()
                        await existing_product.save()
                        print(f"Updated product: {existing_product.title}")
                    else:
                        print(f"No changes for product: {existing_product.title}")
                else:
                    # Insert new product
                    new_product = ClothingProduct(**product_info)
                    await new_product.save()

        print("Zeen data scraping and saving completed!")

    @staticmethod
    def get_last_url(image_urls):
        """Helper method to get the last URL from the srcset."""
        if isinstance(image_urls, list):
            url_string = image_urls[0]
        else:
            url_string = image_urls

        urls = url_string.split(',')
        last_url = urls[-1].strip()

        if last_url.startswith("//"):
            last_url = "https:" + last_url

        return last_url

    @staticmethod
    def format_price(price):
        """Helper method to format prices."""
        if price and re.match(r"\d{1,3}(,\d{3})*", price):
            return price.replace(",", "")
        return None
    
    @staticmethod
    async def getKhaadiBanner():
        # Scrape Khaadi banner data
        url = "https://pk.khaadi.com/"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find the hero banner section
            hero_banner = soup.find("div", class_="hero-banner")
            if hero_banner:
                picture_tag = hero_banner.find("picture", class_="hero-picture")
                if picture_tag:
                    img_tag = picture_tag.find("img", class_="img-fluid focuspoint")
                    if img_tag:
                        # Extract the banner image URL
                        banner_image_url = img_tag.get("src")

                        # Save the banner image URL to the Khaadi brand in the database
                        brand_name = "Khaadi"
                        brand = await ClothingBrand.find_one({"brand_name": brand_name})

                        if brand:
                            # If the brand is found, check if the banner image has changed
                            if brand.banner_image != banner_image_url:
                                brand.banner_image = banner_image_url
                                brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                                await brand.save()
                                print(f"Updated Khaadi brand banner image URL: {banner_image_url}")
                            else:
                                print("Banner image has not changed.")
                        else:
                            # If the brand is not found, create a new brand
                            brand = ClothingBrand(brand_name=brand_name, banner_image=banner_image_url)
                            await brand.save()
                            print(f"Created new Khaadi brand and saved banner image URL: {banner_image_url}")
                    else:
                        print("Banner image not found.")
                else:
                    print("Picture tag not found.")
            else:
                print("Hero banner not found.")
        except requests.exceptions.RequestException as e:
            print("An error occurred while scraping the hero banner:", e)

    @staticmethod
    async def getDhanakBanner():
        # Scrape Dhanak banner data
        url = "https://dhanak.com.pk/"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Locate the banner section
            banner_div = soup.find("div", class_="adaptive_height slide-pc")
            if banner_div:
                img_tag = banner_div.find("img")
                if img_tag and "srcset" in img_tag.attrs:
                    # Extract the largest resolution URL from the srcset
                    srcset_urls = img_tag["srcset"].split(", ")
                    largest_url = srcset_urls[-1].split(" ")[0]

                    # Ensure the URL is complete
                    if largest_url.startswith("//"):
                        largest_url = "https:" + largest_url

                    # Save the banner image URL to the Dhanak brand in the database
                    brand_name = "Dhanak"
                    brand = await ClothingBrand.find_one({"brand_name": brand_name})

                    if brand:
                        # If the brand is found, check if the banner image has changed
                        if brand.banner_image != largest_url:
                            brand.banner_image = largest_url
                            brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                            await brand.save()
                            print(f"Updated Dhanak brand banner image URL: {largest_url}")
                        else:
                            print("Banner image has not changed.")
                    else:
                        # If the brand is not found, create a new brand
                        brand = ClothingBrand(brand_name=brand_name, banner_image=largest_url)
                        await brand.save()
                        print(f"Created new Dhanak brand and saved banner image URL: {largest_url}")
                else:
                    print("Image tag or srcset attribute not found.")
            else:
                print("Banner section not found.")
        except requests.exceptions.RequestException as e:
            print("An error occurred while scraping the banner:", e)
    
    @staticmethod
    async def getOutfittersBanner():
        # Scrape Outfitters banner data
        url = "https://outfitters.com.pk/"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Locate the banner image
            banner_img = soup.find("img", class_="image__banner--image")
            if banner_img:
                # Extract the src URL for the desktop image
                desktop_url = banner_img.get("src")

                # Ensure the URL is complete
                if desktop_url and desktop_url.startswith("//"):
                    desktop_url = "https:" + desktop_url

                # Save the banner image URL to the Outfitters brand in the database
                brand_name = "Outfitters"
                brand = await ClothingBrand.find_one({"brand_name": brand_name})

                if brand:
                    # If the brand is found, check if the banner image has changed
                    if brand.banner_image != desktop_url:
                        brand.banner_image = desktop_url
                        brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                        await brand.save()
                        print(f"Updated Outfitters brand banner image URL: {desktop_url}")
                    else:
                        print("Banner image has not changed.")
                else:
                    # If the brand is not found, create a new brand
                    brand = ClothingBrand(brand_name=brand_name, banner_image=desktop_url)
                    await brand.save()
                    print(f"Created new Outfitters brand and saved banner image URL: {desktop_url}")
            else:
                print("Desktop banner image not found.")
        except requests.exceptions.RequestException as e:
            print("An error occurred while scraping the desktop banner:", e)

    @staticmethod
    async def getJjBanner():
        # Scrape Junaid Jamshed banner data
        url = "https://www.junaidjamshed.com/"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find the banner image with the desktop version (exclude mobile version)
            banner_img_tag = soup.find('img', class_='owl-lazy')
            if banner_img_tag:
                banner_image_url = banner_img_tag.get('data-src-desktop')  # Scrape the desktop version

                # Save the banner image URL to the Junaid brand in the database
                brand_name = "J."
                brand = await ClothingBrand.find_one({"brand_name": brand_name})

                if brand:
                    # If the brand is found, check if the banner image has changed
                    if brand.banner_image != banner_image_url:
                        brand.banner_image = banner_image_url
                        brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                        await brand.save()
                        print(f"Updated Junaid Jamshed brand banner image URL: {banner_image_url}")
                    else:
                        print("Banner image has not changed.")
                else:
                    # If the brand is not found, create a new brand
                    brand = ClothingBrand(brand_name=brand_name, banner_image=banner_image_url)
                    await brand.save()
                    print(f"Created new Junaid Jamshed brand and saved banner image URL: {banner_image_url}")
            else:
                print("Banner image not found.")
        except requests.exceptions.RequestException as e:
            print("An error occurred while scraping the Junaid Jamshed banner:", e)

    @staticmethod
    async def getSayaBanner():
        # Scrape Saya banner data
        url = "https://saya.pk/"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Locate the banner image container
            banner_div = soup.find("div", class_="image__banner-image")
            if banner_div:
                # Find the <img> tag for the desktop image
                img_tag = banner_div.find("img")
                if img_tag:
                    desktop_url = img_tag.get("src")

                    # Ensure the URL is complete
                    if desktop_url and desktop_url.startswith("//"):
                        desktop_url = "https:" + desktop_url

                    # Save the banner image URL to the Saya brand in the database
                    brand_name = "Saya"
                    brand = await ClothingBrand.find_one({"brand_name": brand_name})

                    if brand:
                        # If the brand is found, check if the banner image has changed
                        if brand.banner_image != desktop_url:
                            brand.banner_image = desktop_url
                            brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                            await brand.save()
                            print(f"Updated Saya brand banner image URL: {desktop_url}")
                        else:
                            print("Banner image has not changed.")
                    else:
                        # If the brand is not found, create a new brand
                        brand = ClothingBrand(brand_name=brand_name, banner_image=desktop_url)
                        await brand.save()
                        print(f"Created new Saya brand and saved banner image URL: {desktop_url}")
                else:
                    print("Banner image tag not found.")
            else:
                print("Banner image container not found.")
        except requests.exceptions.RequestException as e:
            print("An error occurred while scraping the Saya banner:", e)

    @staticmethod
    async def getAlkaramBanner():
        # Scrape Alkaram banner data
        url = "https://www.alkaramstudio.com/"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Locate the banner image
            banner_img = soup.find("img", class_="t4s-img-as-bg t4s-d-none t4s-d-md-block t4s-slide-none")
            if banner_img and "srcset" in banner_img.attrs:
                # Extract the largest resolution URL from the srcset
                srcset_urls = banner_img["srcset"].split(", ")
                largest_url = srcset_urls[-1].split(" ")[0]

                # Ensure the URL is complete
                if largest_url.startswith("//"):
                    largest_url = "https:" + largest_url

                # Save the banner image URL to the Alkaram brand in the database
                brand_name = "Alkaram"
                brand = await ClothingBrand.find_one({"brand_name": brand_name})

                if brand:
                    # If the brand is found, check if the banner image has changed
                    if brand.banner_image != largest_url:
                        brand.banner_image = largest_url
                        brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                        await brand.save()
                        print(f"Updated Alkaram brand banner image URL: {largest_url}")
                    else:
                        print("Banner image has not changed.")
                else:
                    # If the brand is not found, create a new brand
                    brand = ClothingBrand(brand_name=brand_name, banner_image=largest_url)
                    await brand.save()
                    print(f"Created new Alkaram brand and saved banner image URL: {largest_url}")
            else:
                print("Banner image or srcset attribute not found.")
        except requests.exceptions.RequestException as e:
            print("An error occurred while scraping the Alkaram banner:", e)

    @staticmethod
    async def getZeenBanner():
        # Scrape Zeen banner data
        url = "https://zeenwoman.com/"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Scrape all image tags with class 't4s-img-as-bg'
            banner_img_tags = soup.find_all("img", class_="t4s-img-as-bg")

            # Find the web version of the banner image (exclude mobile version)
            banner_image_url = None
            for img_tag in banner_img_tags:
                img_url = img_tag.get("src") if img_tag.has_attr("src") else None
                if img_url and "Mobile" not in img_url:  # Exclude mobile images
                    banner_image_url = img_url
                    break

            # Prepend 'https:' if the URL is relative
            if banner_image_url and not banner_image_url.startswith("http"):
                banner_image_url = "https:" + banner_image_url

            if banner_image_url:
                # Save the banner image URL to the Zeen brand in the database
                brand_name = "Zeen"
                brand = await ClothingBrand.find_one({"brand_name": brand_name})

                if brand:
                    # If the brand is found, check if the banner image has changed
                    if brand.banner_image != banner_image_url:
                        brand.banner_image = banner_image_url
                        brand.updatedAt = datetime.utcnow()  # Update the updatedAt timestamp
                        await brand.save()
                        print(f"Updated Zeen brand banner image URL: {banner_image_url}")
                    else:
                        print("Banner image has not changed.")
                else:
                    # If the brand is not found, create a new brand
                    brand = ClothingBrand(brand_name=brand_name, banner_image=banner_image_url)
                    await brand.save()
                    print(f"Created new Zeen brand and saved banner image URL: {banner_image_url}")
            else:
                print("Banner image not found.")

        except requests.exceptions.RequestException as e:
            print("An error occurred while scraping the Zeen banner:", e)

def schedule_clothing_scraping():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ClothingService.getKhaadiData, "interval", minutes=1000, id="khaadi_scraping")
    scheduler.add_job(ClothingService.getDhanakData, "interval", minutes=1000, id="dhanak_scraping")
    scheduler.add_job(ClothingService.getAlkaramData, "interval", minutes=17000, id="alkaram_scraping")
    scheduler.add_job(ClothingService.getJjData, "interval", minutes=19000, id="jj_scraping")
    scheduler.add_job(ClothingService.getOutfittersData, "interval", minutes=15000, id="outfitters_scraping")
    scheduler.add_job(ClothingService.getSayaData, "interval", minutes=20000, id="saya_scraping")
    scheduler.add_job(ClothingService.getZeenData, "interval", minutes=30000, id="zeen_scraping")
    scheduler.add_job(ClothingService.getKhaadiBanner, "interval", minutes=1000, id="khaadiBanner_scraping")
    scheduler.add_job(ClothingService.getDhanakBanner, "interval", minutes=1000, id="dhanakBanner_scraping")
    scheduler.add_job(ClothingService.getOutfittersBanner, "interval", minutes=1000, id="outfittersBanner_scraping")
    scheduler.add_job(ClothingService.getJjBanner, "interval", minutes=1000, id="JjBanner_scraping")
    scheduler.add_job(ClothingService.getSayaBanner, "interval", minutes=1000, id="sayaBanner_scraping")
    scheduler.add_job(ClothingService.getAlkaramBanner, "interval", minutes=1000, id="alkaramBanner_scraping")
    scheduler.add_job(ClothingService.getZeenBanner, "interval", minutes=1000, id="zeenBanner_scraping")
    scheduler.start()
    print("Clothing Scheduler Started!")