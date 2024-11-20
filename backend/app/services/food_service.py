import os
import json
import requests
import pyautogui
import pyperclip
import time
from bs4 import BeautifulSoup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from urllib.parse import urlparse
from pydantic import HttpUrl
from app.models.food_brand_model import FoodBrand
from app.models.food_product_model import FoodProduct
import webbrowser

class FoodService:
    @staticmethod
    async def save_html_content(url):
        """Automate the browser to fetch dynamic HTML content."""
        webbrowser.open(url)
        time.sleep(8)

        pyautogui.hotkey("ctrl", "shift", "c")  # Open DevTools
        time.sleep(5)
        pyautogui.hotkey("ctrl", "]")          # Switch to Elements tab
        time.sleep(3)
        pyautogui.hotkey("ctrl", "l")          # Focus Console
        time.sleep(2)

        js_command = 'copy(document.getElementsByClassName("items-section-wrapper")[0].outerHTML);'
        pyautogui.write(js_command)
        time.sleep(1.5)
        pyautogui.press("enter")
        time.sleep(2.5)

        html_content = pyperclip.paste()
        parsed_url = urlparse(url)
        domain_name = parsed_url.netloc.split(".")[0]
        file_name = f"{domain_name}_Menu.html"

        with open(file_name, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML content saved to {os.path.abspath(file_name)}")
        pyautogui.hotkey("ctrl", "w")  # Close the browser tab
        time.sleep(1.3)

        return file_name

    @staticmethod
    def extract_menu_data(html_file, category_mapping):
        """Parse HTML file and extract product details."""
        with open(html_file, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")

        product_divs = soup.find_all("div", class_="p-0 mb-3 mb-md-0 large_icons_menu_2-item undefined col-6 col-sm-6 col-md-4 col-lg-4")
        products = []

        for div in product_divs:
            product = {}

            datacatid = div.get("datacatid", "")
            dataitemid = div.get("dataitemid", "")
            if datacatid and dataitemid:
                product["product_url"] = f"https://www.kababjeesfriedchicken.com/?item_id={dataitemid}%7C{datacatid}"

            title_tag = div.find("h2", style="color: rgb(33, 37, 41);")
            if title_tag:
                product["title"] = title_tag.get_text(strip=True)

            description_tag = div.find("p", style="color: rgb(113, 128, 150);")
            if description_tag:
                product["description"] = description_tag.get_text(strip=True)

            price_tag = div.find("div", class_="price-wrapper").find("span")
            if price_tag:
                product["price"] = price_tag.get_text(strip=True).replace("Rs.", "").strip()

            img_tag = div.find("img", class_="rounded-0")
            if img_tag and img_tag.get("src"):
                product["image_url"] = f"https://www.kababjeesfriedchicken.com{img_tag['src']}"

            product["food_category"] = category_mapping.get(datacatid, "Unknown")
            if product:
                products.append(product)

        return products

    @staticmethod
    async def save_products_to_db(products):
        """Save or update product data in the database."""
        brand_name = "Kababjees Fried Chicken"
        brand = await FoodBrand.find_one({"brand_name": brand_name})
        if not brand:
            brand = FoodBrand(brand_name=brand_name)
            await brand.save()

        for product in products:
            existing_product = await FoodProduct.find_one({"product_url": product["product_url"]})
            if not existing_product:
                food_product = FoodProduct(
                    brand_id=brand.id,
                    product_url=HttpUrl(product["product_url"]),
                    title=product["title"],
                    description=product.get("description"),
                    price=product["price"],
                    image_url=HttpUrl(product["image_url"]),
                    food_category=product["food_category"]
                )
                await food_product.insert()

    @staticmethod
    async def scrape_and_save():
        """Main function to scrape and save data."""
        url = "https://www.kababjeesfriedchicken.com/"
        html_file = await FoodService.save_html_content(url)

        category_mapping = {
            "419981": "Deal", "416671": "Deal", "414069": "Wing",
            "415886": "Chicken Bites", "415892": "Starter", "407639": "Deal",
            "407640": "Deal", "407641": "Burger", "416904": "Kid",
            "407642": "Add Ons", "407643": "Beverage"
        }

        products = FoodService.extract_menu_data(html_file, category_mapping)
        await FoodService.save_products_to_db(products)

        os.remove(html_file)  # Cleanup
        print("Data scraping and saving completed!")

def schedule_food_scraping():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(FoodService.scrape_and_save, "interval", minutes=10)
    scheduler.start()
    print("Scheduler started: scraping every 10 minutes!")

