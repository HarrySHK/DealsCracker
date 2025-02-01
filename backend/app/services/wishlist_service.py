from app.models.wishlist_model import Wishlist
from bson import ObjectId, DBRef
from app.models.user_model import User
from fastapi import HTTPException, status
from typing import Union
from app.models.clothing_product_model import ClothingProduct
from app.models.food_product_model import FoodProduct
from datetime import datetime
from app.utils.emailSender import send_email
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class WishlistService:
    @staticmethod
    async def toggle_wishlist(user_id: str, product_id: ObjectId):
        # Create references for checking the product type
        user_ref = DBRef("users", ObjectId(user_id))

        # Check if the product is already in the user's wishlist
        existing_item = await Wishlist.find_one({
            "userId": user_ref,
            "productId.$id": product_id  # Match by product ID
        })

        if existing_item:
            # If it exists, delete it (toggle off)
            await existing_item.delete()
            return {
                "message": "Product removed from wishlist",
                "wishlistItemId": str(existing_item.id),
                "productId": str(product_id),
            }
        else:
            # Determine if the product is clothing or food
            product = await ClothingProduct.find_one({"_id": product_id}) or await FoodProduct.find_one({"_id": product_id})

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            # Prepare lastKnownPrices based on product type and set the correct collection reference
            if isinstance(product, ClothingProduct):
                last_known_prices = {
                    "original_price": product.original_price,
                    "sale_price": product.sale_price
                }
                product_ref = DBRef("clothing_products", product_id)
            elif isinstance(product, FoodProduct):
                last_known_prices = {
                    "original_price": product.original_price,
                    "discount_price": product.discount_price
                }
                product_ref = DBRef("food_products", product_id)
            else:
                last_known_prices = {}
                product_ref = None

            # Ensure the product reference is not None
            if not product_ref:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid product reference"
                )

            # Create a new wishlist item with price details and correct product reference
            new_wishlist_item = Wishlist(
                userId=user_ref,
                productId=product_ref,
                lastKnownPrices=last_known_prices
            )
            await new_wishlist_item.insert()

            return {
                "message": "Product added to wishlist",
                "wishlistItemId": str(new_wishlist_item.id),
                "productId": str(product_id),
                "lastKnownPrices": last_known_prices,
            }
    
    @staticmethod
    async def get_user_wishlist(user_id: str):
        pipeline = [
            {
                "$match": {"userId.$id": ObjectId(user_id)}  # Access the `id` from `DBRef`
            },
            {
                "$lookup": {
                    "from": "clothing_products",
                    "let": {"product_id": "$productId.$id"},  # Extract `id` from `DBRef`
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$product_id"]}}}
                    ],
                    "as": "clothing_product"
                }
            },
            {
                "$lookup": {
                    "from": "food_products",
                    "let": {"product_id": "$productId.$id"},  # Extract `id` from `DBRef`
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$product_id"]}}}
                    ],
                    "as": "food_product"
                }
            },
            {
                "$project": {
                    "title": {
                        "$cond": [
                            {"$gt": [{"$size": "$clothing_product"}, 0]},
                            {"$arrayElemAt": ["$clothing_product.title", 0]},
                            {"$arrayElemAt": ["$food_product.title", 0]}
                        ]
                    },
                    "image_url": {
                        "$cond": [
                            {"$gt": [{"$size": "$clothing_product"}, 0]},
                            {"$arrayElemAt": ["$clothing_product.image_url", 0]},
                            {"$arrayElemAt": ["$food_product.image_url", 0]}
                        ]
                    },
                    "product_url": {
                        "$cond": [
                            {"$gt": [{"$size": "$clothing_product"}, 0]},
                            {"$arrayElemAt": ["$clothing_product.product_page", 0]},
                            {"$arrayElemAt": ["$food_product.product_url", 0]}
                        ]
                    },
                    "type": {
                        "$cond": [
                            {"$gt": [{"$size": "$clothing_product"}, 0]},
                            "Clothing",
                            "Food"
                        ]
                    },
                     "productId": {  # Extract _id as productId
                    "$cond": [
                        {"$gt": [{"$size": "$clothing_product"}, 0]},
                        {"$toString": {"$arrayElemAt": ["$clothing_product._id", 0]}},
                        {"$toString": {"$arrayElemAt": ["$food_product._id", 0]}}
                    ]
                },
                    "createdAt": 1 ,
                    "lastKnownPrices": 1 
                }
            }
        ]

        # Execute aggregation and return results
        wishlist_items = await Wishlist.aggregate(pipeline).to_list()

        # Convert ObjectId fields to strings in the result
        for item in wishlist_items:
            if "_id" in item:
                item["_id"] = str(item["_id"])
        
        return wishlist_items
    
    @staticmethod
    async def sendUserWishlistUpdates():
        wishlist_items = await Wishlist.find_all().to_list()

        for wishlist_item in wishlist_items:
            try:
                # Fetch user and product documents
                user = await wishlist_item.userId.fetch()
                product = await wishlist_item.productId.fetch()

                if not user or not product:
                    continue  # Skip if either user or product is missing

                # Initialize price change tracking
                price_changed = False
                price_details = ""

                # Check for price changes
                if isinstance(product, ClothingProduct):
                    if not wishlist_item.lastKnownPrices:
                        wishlist_item.lastKnownPrices = {"original_price": product.original_price, "sale_price": product.sale_price}

                    if product.original_price != wishlist_item.lastKnownPrices.get("original_price"):
                        price_changed = True
                        price_details += f"Original Price updated from {wishlist_item.lastKnownPrices.get('original_price')} to {product.original_price}\n"
                    if product.sale_price != wishlist_item.lastKnownPrices.get("sale_price"):
                        price_changed = True
                        price_details += f"Sale Price updated from {wishlist_item.lastKnownPrices.get('sale_price')} to {product.sale_price}\n"

                elif isinstance(product, FoodProduct):
                    if not wishlist_item.lastKnownPrices:
                        wishlist_item.lastKnownPrices = {"original_price": product.original_price, "discount_price": product.discount_price}

                    if product.original_price != wishlist_item.lastKnownPrices.get("original_price"):
                        price_changed = True
                        price_details += f"Original Price updated from {wishlist_item.lastKnownPrices.get('original_price')} to {product.original_price}\n"
                    if product.discount_price != wishlist_item.lastKnownPrices.get("discount_price"):
                        price_changed = True
                        price_details += f"Discount Price updated from {wishlist_item.lastKnownPrices.get('discount_price')} to {product.discount_price}\n"

                # Send email if price changed
                if price_changed:
                    subject = f"Price Update for {product.title}"
                    body = (
                        f"Dear {user.username},\n\n"
                        f"The price of the product in your wishlist has been updated:\n"
                        f"{price_details}\n"
                        f"Check it out here: {product.product_page or product.product_url}\n\n"
                        f"Best regards,\nYour DealsCracker Team"
                    )
                    await send_email(user.email, subject, body)

                    # Update the last known price
                    wishlist_item.lastKnownPrices = {
                        "original_price": getattr(product, "original_price", None),
                        "sale_price": getattr(product, "sale_price", None),
                        "discount_price": getattr(product, "discount_price", None),
                    }
                    await wishlist_item.save()

            except Exception as e:
                print(f"Error processing wishlist item {wishlist_item.id}: {e}")

        return {"message": "Wishlist updates processed and emails sent if needed"}


def schedule_wishlist():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(WishlistService.sendUserWishlistUpdates, "interval", minutes=0)
    scheduler.start()
    print("Wishlist Scheduler Started!")