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

            existing_product = await ClothingProduct.find_one({"product_page": product_info["product_page"]})
            if not existing_product:
                # If the product does not exist, insert it into the database
                product = ClothingProduct(**product_info)
                await product.save()

        print("Khaadi data scraping and saving completed!")

def schedule_clothing_scraping():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ClothingService.getKhaadiData, "interval", minutes=10)
    scheduler.start()
    print("Scheduler started to scrape Khaadi data every 5 minutes!")