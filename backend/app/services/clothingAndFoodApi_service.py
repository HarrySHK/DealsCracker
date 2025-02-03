from math import ceil
from app.models.clothing_brand_model import ClothingBrand
from app.models.food_brand_model import FoodBrand
from app.models.clothing_product_model import ClothingProduct
from app.models.food_product_model import FoodProduct
from app.models.wishlist_model import Wishlist
from datetime import datetime, timedelta
from googlemaps import Client as GoogleMapsClient
from app.core.config import settings
from bson import ObjectId, DBRef
from beanie.odm.fields import Link

class ClothingAndFoodService:
    @staticmethod
    async def get_random_brands_banner(category: str):
        try:
            # Define pipelines for fetching random banners
            clothing_pipeline = [
                {"$match": {"banner_image": {"$ne": None}}},  # Exclude brands with null banner_image
                {"$sample": {"size": 4}},  # Randomly select 4 documents
                {
                    "$project": {
                        "_id": 0,
                        "brand_name": 1,
                        "banner_image": 1,
                    }
                },
            ]

            food_pipeline = [
                {"$match": {"banner_image": {"$ne": None}}},  # Exclude brands with null banner_image
                {"$sample": {"size": 4}},  # Randomly select 4 documents
                {
                    "$project": {
                        "_id": 0,
                        "brand_name": 1,
                        "banner_image": 1,
                    }
                },
            ]

            # Fetch data based on category
            clothing_banners = []
            food_banners = []

            if category in ["clothing", "both"]:
                clothing_banners = await ClothingBrand.aggregate(clothing_pipeline).to_list()

            if category in ["food", "both"]:
                food_banners = await FoodBrand.aggregate(food_pipeline).to_list()

            # Construct the response
            if category == "clothing":
                return {"clothing_banners": clothing_banners}
            elif category == "food":
                return {"food_banners": food_banners}
            elif category == "both":
                # Interleave the banners
                interleaved_banners = []
                max_length = max(len(clothing_banners), len(food_banners))
                for i in range(max_length):
                    if i < len(food_banners):
                        interleaved_banners.append(food_banners[i])
                    if i < len(clothing_banners):
                        interleaved_banners.append(clothing_banners[i])
                return {"both_banners": interleaved_banners}

        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving brand banners: {str(e)}")
    
    @staticmethod
    async def get_todays_best_deals(category: str):
        try:
            # Fetch top discounted clothing products
            clothing_deals = []
            if category in ["clothing", "both"]:
                clothing_pipeline = [
                    {"$match": {"sale_price": {"$ne": None}, "original_price": {"$gt": 0}, "sale_price": {"$gt": 0}}},
                    {
                        "$addFields": {
                            "discount_percentage": {
                                "$multiply": [
                                    {"$divide": [{"$subtract": ["$original_price", "$sale_price"]}, "$original_price"]},
                                    100,
                                ]
                            }
                        }
                    },
                    {"$sort": {"createdAt": -1}},
                    {"$limit": 2},  # Get top 2 products
                    {
                        "$lookup": {
                            "from": "clothing_brands",  # Collection name
                            "localField": "brand_id.$id",  # Access the $id of DBRef (brand_id is a DBRef)
                            "foreignField": "_id",  # Match _id in the clothing_brands collection
                            "as": "brand_info",  # Alias for the joined result
                        }
                    },
                    {"$unwind": {"path": "$brand_info", "preserveNullAndEmptyArrays": True}},  # Ensure unmatched brands are included
                    {
                        "$project": {
                            "_id": 0,
                            "title": 1,
                            "original_price": 1,
                            "sale_price": 1,
                            "product_page": 1,
                            "image_url": 1,
                            "brand_name": "$brand_info.brand_name",  # Extract brand_name from the brand_info
                            "discount_percentage": {"$round": ["$discount_percentage", 2]},
                        }
                    },
                ]
                clothing_deals = await ClothingProduct.aggregate(clothing_pipeline).to_list()

            # Fetch top discounted food products
            food_deals = []
            if category in ["food", "both"]:
                food_pipeline = [
                    {"$match": {
                        "food_category": "Deal",  # Filter products in "Deal" category
                    }},
                    {
                        "$addFields": {
                            "discount_percentage": {
                                "$cond": {
                                    "if": {"$gt": ["$discount_price", 0]},  # Check if discount_price is greater than 0
                                    "then": {
                                        "$multiply": [
                                            {"$divide": [{"$subtract": ["$original_price", "$discount_price"]}, "$original_price"]},
                                            100,
                                        ]
                                    },
                                    "else": None  # If discount_price is not greater than 0 (e.g., null or 0), set discount_percentage as null
                                }
                            }
                        }
                    },
                    {"$sort": {"createdAt": -1}},
                    {"$limit": 2},  # Get top 2 products
                    {
                        "$lookup": {
                            "from": "food_brands",
                            "localField": "brand_id.$id",  # Access the $id of DBRef (brand_id is a DBRef)
                            "foreignField": "_id",  # Match _id in the food_brands collection
                            "as": "brand_info",
                        }
                    },
                    {"$unwind": "$brand_info"},  # Unwind brand info array
                    {
                        "$project": {
                            "_id": 0,
                            "title": 1,
                            "original_price": 1,
                            "discount_price": 1,  # Include discount_price even if it's null
                            "product_url": 1,
                            "image_url": 1,
                            "brand_name": "$brand_info.brand_name",  # Extract brand_name from the food brand
                            "discount_percentage": 1,  # Include discount_percentage, which can be null
                        }
                    },
                ]
                food_deals = await FoodProduct.aggregate(food_pipeline).to_list()

            # Construct the response
            if category == "clothing":
                return {"clothing_deals": clothing_deals}
            elif category == "food":
                return {"food_deals": food_deals}
            elif category == "both":
                return {"clothing_deals": clothing_deals, "food_deals": food_deals}

        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving today's best deals: {str(e)}")

    @staticmethod
    async def get_top_5_products(category: str):
        try:
            # Fetch top 5 discounted clothing products
            clothing_deals = []
            if category in ["clothing", "both"]:
                clothing_pipeline = [
                    {"$match": {"sale_price": {"$ne": None}, "original_price": {"$gt": 0}, "sale_price": {"$gt": 0}}}, 
                    {
                        "$addFields": {
                            "discount_percentage": {
                                "$multiply": [
                                    {"$divide": [{"$subtract": ["$original_price", "$sale_price"]}, "$original_price"]},
                                    100,
                                ]
                            }
                        }
                    },
                    {"$sort": {"discount_percentage": -1}},  # Sort by highest discount percentage
                    {"$limit": 5},  # Get top 5 products
                    {
                        "$lookup": {
                            "from": "clothing_brands",  # Collection name
                            "localField": "brand_id.$id",  # Access the $id of DBRef (brand_id is a DBRef)
                            "foreignField": "_id",  # Match _id in the clothing_brands collection
                            "as": "brand_info",  # Alias for the joined result
                        }
                    },
                    {"$unwind": {"path": "$brand_info", "preserveNullAndEmptyArrays": True}},  # Ensure unmatched brands are included
                    {
                        "$project": {
                            "_id": 0,
                            "title": 1,
                            "original_price": 1,
                            "sale_price": 1,
                            "product_page": 1,
                            "image_url": 1,
                            "brand_name": "$brand_info.brand_name",  # Extract brand_name from the brand_info
                            "discount_percentage": {"$round": ["$discount_percentage", 2]},
                        }
                    },
                ]
                clothing_deals = await ClothingProduct.aggregate(clothing_pipeline).to_list()

            # Fetch top 5 discounted food products
            food_deals = []
            if category in ["food", "both"]:
                food_pipeline = [
                    {"$match": {
                        "food_category": "Deal",  # Filter products in "Deal" category
                    }},
                    {
                        "$addFields": {
                            "discount_percentage": {
                                "$cond": {
                                    "if": {"$gt": ["$discount_price", 0]},  # Check if discount_price is greater than 0
                                    "then": {
                                        "$multiply": [
                                            {"$divide": [{"$subtract": ["$original_price", "$discount_price"]}, "$original_price"]},
                                            100,
                                        ]
                                    },
                                    "else": None  # If discount_price is not greater than 0 (e.g., null or 0), set discount_percentage as null
                                }
                            }
                        }
                    },
                    {"$sort": {"discount_percentage": -1}},  # Sort by highest discount percentage
                    {"$limit": 5},  # Get top 5 products
                    {
                        "$lookup": {
                            "from": "food_brands",
                            "localField": "brand_id.$id",  # Access the $id of DBRef (brand_id is a DBRef)
                            "foreignField": "_id",  # Match _id in the food_brands collection
                            "as": "brand_info",
                        }
                    },
                    {"$unwind": "$brand_info"},  # Unwind brand info array
                    {
                        "$project": {
                            "_id": 0,
                            "title": 1,
                            "original_price": 1,
                            "discount_price": 1,  # Include discount_price even if it's null
                            "product_url": 1,
                            "image_url": 1,
                            "brand_name": "$brand_info.brand_name",  # Extract brand_name from the food brand
                            "discount_percentage": 1,  # Include discount_percentage, which can be null
                        }
                    },
                ]
                food_deals = await FoodProduct.aggregate(food_pipeline).to_list()

            # Construct the response
            if category == "clothing":
                return {"clothing_deals": clothing_deals}
            elif category == "food":
                return {"food_deals": food_deals}
            elif category == "both":
                return {"clothing_deals": clothing_deals, "food_deals": food_deals}

        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving top 5 products: {str(e)}")
        
    @staticmethod
    async def get_nearby_outlets(category: str, user):
        if not user.location:
            raise ValueError("User location is required to find nearby outlets.")

        user_lat = user.location.latitude
        user_lon = user.location.longitude

        if user_lat is None or user_lon is None:
            raise ValueError("Invalid user location.")

        gmaps = GoogleMapsClient(key=settings.GOOGLE_MAPS_API_KEY)

        clothing_brands = await ClothingBrand.find_all().to_list()
        food_brands = await FoodBrand.find_all().to_list()

        clothing_brand_names = [brand.brand_name for brand in clothing_brands]
        food_brand_names = [brand.brand_name for brand in food_brands]

        clothing_outlets = []
        food_outlets = []

        # Fetch clothing outlets
        if category in ["clothing", "both"]:
            for brand in clothing_brand_names:
                results = gmaps.places_nearby(
                    location=(user_lat, user_lon),
                    radius=1500,
                    keyword=brand
                )
                for result in results.get("results", []):
                    location = result.get("geometry", {}).get("location")
                    if location:
                        lat, lng = location["lat"], location["lng"]
                        location_url = f"https://www.google.com/maps?q={lat},{lng}"
                        clothing_outlets.append({
                            "category": "clothing",
                            "brand_name": brand,
                            "address": result.get("vicinity"),
                            "location": location,
                            "locationUrl": location_url
                        })

        # Fetch food outlets
        if category in ["food", "both"]:
            for brand in food_brand_names:
                results = gmaps.places_nearby(
                    location=(user_lat, user_lon),
                    radius=1500,
                    keyword=brand
                )
                for result in results.get("results", []):
                    location = result.get("geometry", {}).get("location")
                    if location:
                        lat, lng = location["lat"], location["lng"]
                        location_url = f"https://www.google.com/maps?q={lat},{lng}"
                        food_outlets.append({
                            "category": "food",
                            "brand_name": brand,
                            "address": result.get("vicinity"),
                            "location": location,
                            "locationUrl": location_url
                        })

        # Interleave clothing and food outlets for "both" category
        if category == "both":
            nearby_outlets = []
            max_len = max(len(clothing_outlets), len(food_outlets))
            for i in range(max_len):
                if i < len(clothing_outlets):
                    nearby_outlets.append(clothing_outlets[i])
                if i < len(food_outlets):
                    nearby_outlets.append(food_outlets[i])
        else:
            nearby_outlets = clothing_outlets + food_outlets

        return nearby_outlets
    
    @staticmethod
    async def get_top_trending_brands(category: str):
        top_brands = []

        try:
            clothing_brands = []
            food_brands = []

            # Fetch top clothing brands by average discount percentage
            if category in ["clothing", "both"]:
                clothing_pipeline = [
                    {
                        "$lookup": {
                            "from": "clothing_products",
                            "localField": "_id",
                            "foreignField": "brand_id.$id",
                            "as": "products",
                        }
                    },
                    {"$unwind": {"path": "$products", "preserveNullAndEmptyArrays": True}},
                    {"$match": {"products.sale_price": {"$ne": None}, "products.original_price": {"$gt": 0}}},
                    {
                        "$addFields": {
                            "discount_percentage": {
                                "$multiply": [
                                    {
                                        "$divide": [
                                            {"$subtract": ["$products.original_price", "$products.sale_price"]},
                                            "$products.original_price",
                                        ]
                                    },
                                    100,
                                ]
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": "$_id",
                            "brand_name": {"$first": "$brand_name"},
                            "banner_image": {"$first": "$banner_image"},
                            "avg_discount": {"$avg": "$discount_percentage"},
                        }
                    },
                    {
                        "$addFields": {
                            "avg_discount": {
                                "$round": ["$avg_discount", 0]  # Rounds to the nearest integer
                            }
                        }
                    },
                    {"$sort": {"avg_discount": -1}},
                    {"$limit": 4},
                ]

                clothing_brands = await ClothingBrand.aggregate(clothing_pipeline).to_list()
                for brand in clothing_brands:
                    brand["_id"] = str(brand["_id"])  # Convert ObjectId to string

            # Fetch top food brands by average deals percentage
            if category in ["food", "both"]:
                food_pipeline = [
                    # Join food_products collection to get products for each brand
                    {
                        "$lookup": {
                            "from": "food_products",
                            "localField": "_id",
                            "foreignField": "brand_id.$id",
                            "as": "all_products",  # Join to get all products for the brand
                        }
                    },
                    # Unwind the all_products array to calculate counts per product
                    {"$unwind": {"path": "$all_products", "preserveNullAndEmptyArrays": True}},
                    {
                        "$group": {
                            "_id": "$_id",  # Group by brand_id
                            "brand_name": {"$first": "$brand_name"},
                            "banner_image": {"$first": "$banner_image"},
                            "deal_count": {
                                "$sum": {
                                    "$cond": [
                                        {"$eq": ["$all_products.food_category", "Deal"]},  # Count only 'Deal' products
                                        1,
                                        0
                                    ]
                                }
                            },
                            "total_products": {"$sum": 1},  # Count total products (all categories)
                        }
                    },
                    # Calculate the average deal percentage
                    {
                        "$addFields": {
                            "avg_deal_percentage": {
                                "$cond": {
                                    "if": {"$eq": ["$total_products", 0]},  # Default to 0 if no products
                                    "then": 0,
                                    "else": {
                                        "$multiply": [
                                            {"$divide": ["$deal_count", "$total_products"]},
                                            100
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    {
                        "$addFields": {
                            "avg_deal_percentage": {
                                "$round": ["$avg_deal_percentage", 0]  # Rounds to the nearest integer
                            }
                        }
                    },
                    {
                        "$sort": {"avg_deal_percentage": -1},  # Sort by avg_deal_percentage in descending order
                    },
                    {"$limit": 4}  # Optional: Limit to top 4 brands
                ]

                food_brands = await FoodBrand.aggregate(food_pipeline).to_list()
                for brand in food_brands:
                    brand["_id"] = str(brand["_id"])  # Convert ObjectId to string

            # Alternate between clothing and food brands when category is "both"
            if category == "both":
                max_length = max(len(clothing_brands), len(food_brands))
                for i in range(max_length):
                    if i < len(clothing_brands):
                        top_brands.append(clothing_brands[i])
                    if i < len(food_brands):
                        top_brands.append(food_brands[i])
            else:
                # If category is "clothing" or "food", just extend the respective list
                top_brands.extend(clothing_brands if category == "clothing" else food_brands)

            return top_brands
        except Exception as e:
            raise RuntimeError(f"Error fetching top trending brands: {str(e)}")

    @staticmethod
    async def get_all_products(
        category: str = None,
        page: int = 1,
        limit: int = 10,
        search: str = None,
        brand_name: str = None,
        latest: bool = True,
        sortPrice: str = None,
        maxPrice: float = None,
        food_category: str = None,  # Added food_category parameter
    ):
        try:
            # Input validation
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10
            if sortPrice not in [None, "ascending", "descending"]:
                raise ValueError("Invalid sortPrice. Must be 'ascending' or 'descending'.")
            if maxPrice is not None and maxPrice < 0:
                raise ValueError("Invalid maxPrice. Must be a non-negative number.")

            # Calculate skip
            skip = (page - 1) * limit

            # Build match conditions
            match_conditions = []
            if search:
                match_conditions.append({
                    "$or": [
                        {"title": {"$regex": search, "$options": "i"}},
                        {"brand_info.brand_name": {"$regex": search, "$options": "i"}}
                    ]
                })
            if brand_name:
                match_conditions.append({
                    "brand_info.brand_name": {"$regex": brand_name, "$options": "i"}
                })
            if maxPrice is not None:
                match_conditions.append({
                    "$or": [
                        {"original_price": {"$lte": maxPrice}},
                        {"sale_price": {"$lte": maxPrice}},
                        {"discount_price": {"$lte": maxPrice}}
                    ]
                })
            if food_category and category == "food":  # Apply food_category filter only for food
                match_conditions.append({
                    "food_category": {"$regex": food_category, "$options": "i"}
                })

            match_stage = {"$and": match_conditions} if match_conditions else {}

            async def get_paginated_data(collection, pipeline, skip_val, limit_val):
                # Add pagination stages
                pipeline.extend([
                    {"$skip": skip_val},
                    {"$limit": limit_val}
                ])
                return await collection.aggregate(pipeline).to_list(length=None)

            async def get_total_count(collection, pipeline):
                count_pipeline = pipeline.copy()
                count_pipeline.append({"$count": "total"})
                result = await collection.aggregate(count_pipeline).to_list(length=None)
                return result[0]["total"] if result else 0

            def create_base_pipeline(collection_name, category_name, date_field):
                price_sort_order = 1 if sortPrice == "ascending" else -1 if sortPrice == "descending" else None

                pipeline = [
                    {
                        "$addFields": {
                            "brand_id": {"$ifNull": ["$brand_id.$id", None]},
                            "price": {
                                "$cond": [
                                    {"$eq": [category_name, "clothing"]},
                                    {"$ifNull": ["$sale_price", "$original_price"]},
                                    {"$ifNull": ["$discount_price", "$original_price"]}
                                ]
                            }
                        }
                    },
                    {
                        "$lookup": {
                            "from": collection_name,
                            "localField": "brand_id",
                            "foreignField": "_id",
                            "as": "brand_info"
                        }
                    },
                    {"$unwind": "$brand_info"},
                    {"$match": match_stage} if match_conditions else {"$match": {}},
                    {"$sort": {"price": price_sort_order}} if price_sort_order is not None
                    else {"$sort": {date_field: -1 if latest else 1}},
                    {
                        "$project": {
                            "_id": {"$toString": "$_id"},
                            "title": 1,
                            "product_page": 1,
                            "product_url": 1,
                            "image_url": 1,
                            "original_price": 1,
                            "sale_price": 1 if category_name == "clothing" else None,
                            "discount_price": 1 if category_name == "food" else None,
                            "category": {"$literal": category_name},
                            "brand_name": "$brand_info.brand_name",
                            "food_category": 1 if category_name == "food" else None,
                            "price": 1,
                            "isWishlist": {"$literal": False}
                        }
                    }
                ]
                return pipeline

            if category in ["clothing", "food"]:
                collection = ClothingProduct if category == "clothing" else FoodProduct
                date_field = "created_at" if category == "clothing" else "createdAt"

                pipeline = create_base_pipeline(f"{category}_brands", category, date_field)
                total = await get_total_count(collection, pipeline)
                data = await get_paginated_data(collection, pipeline, skip, limit)

            elif category == "both":
                # Create pipelines for both collections
                clothing_pipeline = create_base_pipeline("clothing_brands", "clothing", "created_at")
                food_pipeline = create_base_pipeline("food_brands", "food", "createdAt")

                # Get counts
                clothing_count = await get_total_count(ClothingProduct, clothing_pipeline)
                food_count = await get_total_count(FoodProduct, food_pipeline)
                total = clothing_count + food_count

                # Get paginated data from both collections
                clothing_data = await get_paginated_data(ClothingProduct, clothing_pipeline, skip, limit // 2)
                food_data = await get_paginated_data(FoodProduct, food_pipeline, skip, limit - (limit // 2))

                # Combine and sort if needed
                data = clothing_data + food_data
                if sortPrice:
                    # data.sort(
                    #     key=lambda x: x["price"],
                    #     reverse=(sortPrice == "descending")
                    # )
                    data.sort(
                        key=lambda x: float(x["price"]) if isinstance(x["price"], (int, float, str)) and x["price"] else 0,
                        reverse=(sortPrice == "descending")
                    )
            else:
                raise ValueError("Invalid category. Must be 'clothing', 'food', or 'both'.")

            return {
                "currentPage": page,
                "totalPages": ceil(total / limit),
                "totalItems": total,
                "products": data
            }

        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving products: {str(e)}")
        
    @staticmethod
    async def getProductFilterDetail(category: str):
        """
        Get filter details for products based on the provided category.
        - If category is "clothing", returns clothing brand names and the highest original_price as maxPrice in clothing_products.
        - If category is "food", returns food brand names, the highest original_price as maxPrice in food_products, and all food categories.
        - If category is "both", returns both clothing and food brand names, and their respective highest original_prices.
        """
        try:
            if category not in ["clothing", "food", "both"]:
                raise ValueError("Invalid category. Must be 'clothing', 'food', or 'both'.")

            # Helper to calculate the max original price from a collection (ensure valid number type)
            async def get_max_price(collection, price_field="original_price"):
                pipeline = [
                    {
                        "$match": {
                            price_field: {"$type": "double"}  # Ensures price field is a number
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "maxPrice": {"$max": f"${price_field}"}  # Max on original_price field
                        }
                    }
                ]
                result = await collection.aggregate(pipeline).to_list(length=1)
                return float(result[0]["maxPrice"]) if result and result[0]["maxPrice"] else None

            # Helper to get all brand names for a collection
            async def get_brand_names(collection):
                pipeline = [
                    {"$project": {"brand_name": 1}},
                    {"$group": {"_id": None, "brandNames": {"$addToSet": "$brand_name"}}}
                ]
                result = await collection.aggregate(pipeline).to_list(length=1)
                return result[0]["brandNames"] if result else []

            # Helper to get all unique food categories
            async def get_food_categories():
                pipeline = [
                    {"$group": {"_id": "$food_category"}},
                    {"$project": {"_id": 0, "food_category": "$_id"}}
                ]
                result = await FoodProduct.aggregate(pipeline).to_list(length=None)
                return [item["food_category"] for item in result]

            # Prepare response
            response = {}

            # Fetch details for clothing
            if category in ["clothing", "both"]:
                clothing_brands = await get_brand_names(ClothingBrand)
                clothing_max_price = await get_max_price(ClothingProduct)  # Get max original price from clothing products
                response["clothing"] = {
                    "brands": clothing_brands,
                    "maxPrice": clothing_max_price
                }

            # Fetch details for food
            if category in ["food", "both"]:
                food_brands = await get_brand_names(FoodBrand)
                food_max_price = await get_max_price(FoodProduct)  # Get max original price from food products
                food_categories = await get_food_categories() if category == "food" else None
                response["food"] = {
                    "brands": food_brands,
                    "maxPrice": food_max_price,
                    "foodCategories": food_categories if food_categories else []
                }

            return response

        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving filter details: {str(e)}")
        
    
    @staticmethod
    async def get_all_products_by_user(
        user_id: str,
        category: str = None,
        page: int = 1,
        limit: int = 10,
        search: str = None,
        brand_name: str = None,
        latest: bool = True,
        sortPrice: str = None,
        maxPrice: float = None,
        food_category: str = None,
    ):
        try:
            # Input validation
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10
            if sortPrice not in [None, "ascending", "descending"]:
                raise ValueError("Invalid sortPrice. Must be 'ascending' or 'descending'.")
            if maxPrice is not None and maxPrice < 0:
                raise ValueError("Invalid maxPrice. Must be a non-negative number.")

            # Calculate skip
            skip = (page - 1) * limit

            # Get user's wishlist items
            user_wishlist = await Wishlist.find({"userId": DBRef("users", ObjectId(user_id))}).to_list(length=None)
            
            # Extract wishlist product IDs with their respective collections
            wishlist_products = {}
            for item in user_wishlist:
                try:
                    # Handle Beanie Link object
                    if hasattr(item.productId, 'ref') and item.productId.ref:
                        # Get the DBRef from the Link object
                        db_ref = item.productId.ref
                        if isinstance(db_ref, DBRef):
                            wishlist_products[str(db_ref.id)] = db_ref.collection
                        elif isinstance(db_ref, dict) and '$ref' in db_ref:
                            wishlist_products[str(db_ref['$id']['$oid'])] = db_ref['$ref']
                        else:
                            print(f"Unexpected ref format in Link: {type(db_ref)}, value: {db_ref}")
                    else:
                        print(f"No ref found in Link object: {item.productId}")
                except Exception as e:
                    print(f"Error processing wishlist item: {e}")

            print("Wishlist Products: ", wishlist_products)

            print("\nDebug Information:")
            for item in user_wishlist:
                print(f"\nWishlist Item: {item}")
                print(f"ProductId Type: {type(item.productId)}")
                if hasattr(item.productId, 'ref'):
                    print(f"ProductId Ref: {item.productId.ref}")
                    if item.productId.ref:
                        print(f"Ref Type: {type(item.productId.ref)}")

            # Build match conditions
            match_conditions = []
            if search:
                match_conditions.append({
                    "$or": [
                        {"title": {"$regex": search, "$options": "i"}},
                        {"brand_info.brand_name": {"$regex": search, "$options": "i"}}
                    ]
                })
            if brand_name:
                match_conditions.append({
                    "brand_info.brand_name": {"$regex": brand_name, "$options": "i"}
                })
            if maxPrice is not None:
                match_conditions.append({
                    "$or": [
                        {"original_price": {"$lte": maxPrice}},
                        {"sale_price": {"$lte": maxPrice}},
                        {"discount_price": {"$lte": maxPrice}}
                    ]
                })
            if food_category and category == "food":
                match_conditions.append({
                    "food_category": {"$regex": food_category, "$options": "i"}
                })

            match_stage = {"$and": match_conditions} if match_conditions else {}

            async def get_paginated_data(collection, pipeline, skip_val, limit_val):
                pipeline.extend([
                    {"$skip": skip_val},
                    {"$limit": limit_val}
                ])
                return await collection.aggregate(pipeline).to_list(length=None)

            async def get_total_count(collection, pipeline):
                count_pipeline = pipeline.copy()
                count_pipeline.append({"$count": "total"})
                result = await collection.aggregate(count_pipeline).to_list(length=None)
                return result[0]["total"] if result else 0

            def create_base_pipeline(collection_name, category_name, date_field):
                price_sort_order = 1 if sortPrice == "ascending" else -1 if sortPrice == "descending" else None
                expected_collection = f"{category_name}_products"

                pipeline = [
                    {
                        "$addFields": {
                            "brand_id": {"$ifNull": ["$brand_id.$id", None]},
                            "price": {
                                "$cond": [
                                    {"$eq": [category_name, "clothing"]},
                                    {"$ifNull": ["$sale_price", "$original_price"]},
                                    {"$ifNull": ["$discount_price", "$original_price"]}
                                ]
                            }
                        }
                    },
                    {
                        "$lookup": {
                            "from": collection_name,
                            "localField": "brand_id",
                            "foreignField": "_id",
                            "as": "brand_info"
                        }
                    },
                    {"$unwind": "$brand_info"},
                    {"$match": match_stage} if match_conditions else {"$match": {}},
                    {"$sort": {"price": price_sort_order}} if price_sort_order is not None
                    else {"$sort": {date_field: -1 if latest else 1}},
                    {
                        "$project": {
                            "_id": {"$toString": "$_id"},
                            "title": 1,
                            "product_page": 1,
                            "product_url": 1,
                            "image_url": 1,
                            "original_price": 1,
                            "sale_price": 1 if category_name == "clothing" else None,
                            "discount_price": 1 if category_name == "food" else None,
                            "category": {"$literal": category_name},
                            "brand_name": "$brand_info.brand_name",
                            "food_category": 1 if category_name == "food" else None,
                            "price": 1,
                            "isWishlist": {
                                "$let": {
                                    "vars": {
                                        "product_id_str": {"$toString": "$_id"}
                                    },
                                    "in": {
                                        "$in": [
                                            "$$product_id_str",
                                            {
                                                "$map": {
                                                    "input": {
                                                        "$filter": {
                                                            "input": {"$objectToArray": wishlist_products},
                                                            "cond": {"$eq": ["$$this.v", expected_collection]}
                                                        }
                                                    },
                                                    "as": "item",
                                                    "in": "$$item.k"
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                ]
                return pipeline

            if category in ["clothing", "food"]:
                collection = ClothingProduct if category == "clothing" else FoodProduct
                date_field = "created_at" if category == "clothing" else "createdAt"

                pipeline = create_base_pipeline(f"{category}_brands", category, date_field)
                total = await get_total_count(collection, pipeline)
                data = await get_paginated_data(collection, pipeline, skip, limit)

            elif category == "both":
                # Create pipelines for both collections
                clothing_pipeline = create_base_pipeline("clothing_brands", "clothing", "created_at")
                food_pipeline = create_base_pipeline("food_brands", "food", "createdAt")

                # Get counts
                clothing_count = await get_total_count(ClothingProduct, clothing_pipeline)
                food_count = await get_total_count(FoodProduct, food_pipeline)
                total = clothing_count + food_count

                # Get paginated data from both collections
                clothing_data = await get_paginated_data(ClothingProduct, clothing_pipeline, skip, limit // 2)
                food_data = await get_paginated_data(FoodProduct, food_pipeline, skip, limit - (limit // 2))

                # Combine and sort if needed
                data = clothing_data + food_data
                if sortPrice:
                    data.sort(
                        key=lambda x: float(x["price"]) if isinstance(x["price"], (int, float, str)) and x["price"] else 0,
                        reverse=(sortPrice == "descending")
                    )
            else:
                raise ValueError("Invalid category. Must be 'clothing', 'food', or 'both'.")

            return {
                "currentPage": page,
                "totalPages": ceil(total / limit),
                "totalItems": total,
                "products": data
            }

        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving products: {str(e)}")
        
    @staticmethod
    async def get_all_brands(category: str):
        try:
            clothing_brands = []
            food_brands = []

            # Fetch all clothing brands with product counts
            if category in ["clothing", "both"]:
                clothing_pipeline = [
                    {
                        "$lookup": {
                            "from": "clothing_products",
                            "localField": "_id",
                            "foreignField": "brand_id.$id",
                            "as": "products",
                        }
                    },
                    {
                        "$addFields": {
                            "products_count": {"$size": "$products"}  # Calculate the size of the array here
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "brand_name": 1,
                            "products_count": 1,
                        }
                    },
                    {"$sort": {"products_count": -1}},
                ]

                clothing_brands = await ClothingBrand.aggregate(clothing_pipeline).to_list()
                for brand in clothing_brands:
                    brand["_id"] = str(brand["_id"])  # Convert ObjectId to string

            # Fetch all food brands with product counts
            if category in ["food", "both"]:
                food_pipeline = [
                    {
                        "$lookup": {
                            "from": "food_products",
                            "localField": "_id",
                            "foreignField": "brand_id.$id",
                            "as": "products",
                        }
                    },
                    {
                        "$addFields": {
                            "products_count": {"$size": "$products"}  # Calculate the size of the array here
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "brand_name": 1,
                            "products_count": 1,
                        }
                    },
                    {"$sort": {"products_count": -1}},
                ]

                food_brands = await FoodBrand.aggregate(food_pipeline).to_list()
                for brand in food_brands:
                    brand["_id"] = str(brand["_id"])  # Convert ObjectId to string

            # Structure the response
            result = {}
            if category in ["clothing", "both"]:
                result["clothingBrands"] = clothing_brands
            if category in ["food", "both"]:
                result["foodBrands"] = food_brands

            return result
        except Exception as e:
            raise RuntimeError(f"Error fetching all brands: {str(e)}")
        
    # @staticmethod
    # async def get_wishlisted_brands(category: str):
    #     try:
    #         clothing_wishlisted = []
    #         food_wishlisted = []

    #         # Fetch total wishlist count for calculating percentages
    #         total_wishlist_count = await Wishlist.count()

    #         # Fetch wishlisted clothing brands
    #         if category in ["clothing", "both"]:
    #             clothing_pipeline = [
    #                 # First get all brands and their products
    #                 {
    #                     "$lookup": {
    #                         "from": "clothing_products",
    #                         "let": { "brandId": "$_id" },
    #                         "pipeline": [
    #                             {
    #                                 "$match": {
    #                                     "$expr": {
    #                                         "$eq": ["$brand_id.$id", "$$brandId"]
    #                                     }
    #                                 }
    #                             }
    #                         ],
    #                         "as": "products"
    #                     }
    #                 },
    #                 # For each brand's products, look up wishlist entries
    #                 {
    #                     "$unwind": {
    #                         "path": "$products",
    #                         "preserveNullAndEmptyArrays": True
    #                     }
    #                 },
    #                 {
    #                     "$lookup": {
    #                         "from": "wishlists",
    #                         "let": { "productId": "$products._id" },
    #                         "pipeline": [
    #                             {
    #                                 "$match": {
    #                                     "$expr": {
    #                                         "$eq": ["$productId.$id", "$$productId"]
    #                                     }
    #                                 }
    #                             }
    #                         ],
    #                         "as": "product_wishlists"
    #                     }
    #                 },
    #                 # Group back by brand to consolidate results
    #                 {
    #                     "$group": {
    #                         "_id": "$_id",
    #                         "brand_name": { "$first": "$brand_name" },
    #                         "all_wishlists": {
    #                             "$push": "$product_wishlists"
    #                         }
    #                     }
    #                 },
    #                 # Flatten the nested arrays of wishlists
    #                 {
    #                     "$addFields": {
    #                         "flattened_wishlists": {
    #                             "$reduce": {
    #                                 "input": "$all_wishlists",
    #                                 "initialValue": [],
    #                                 "in": { "$concatArrays": ["$$value", "$$this"] }
    #                             }
    #                         }
    #                     }
    #                 },
    #                 # Calculate wishlist metrics
    #                 {
    #                     "$addFields": {
    #                         "wishlist_count": { "$size": "$flattened_wishlists" },
    #                         "wishlist_percent": {
    #                             "$cond": [
    #                                 { "$gt": [total_wishlist_count, 0] },
    #                                 {
    #                                     "$multiply": [
    #                                         { 
    #                                             "$divide": [
    #                                                 { "$size": "$flattened_wishlists" },
    #                                                 total_wishlist_count
    #                                             ]
    #                                         },
    #                                         100
    #                                     ]
    #                                 },
    #                                 0
    #                             ]
    #                         }
    #                     }
    #                 },
    #                 # Final projection
    #                 {
    #                     "$project": {
    #                         "_id": 1,
    #                         "brand_name": 1,
    #                         "wishlist_count": 1,
    #                         "wishlist_percent": 1
    #                     }
    #                 },
    #                 # Sort by wishlist count
    #                 { 
    #                     "$sort": { 
    #                         "wishlist_count": -1 
    #                     } 
    #                 }
    #             ]

    #             # Execute the pipeline
    #             clothing_wishlisted = await ClothingBrand.aggregate(clothing_pipeline).to_list()
                
    #             # Convert ObjectId to string for JSON serialization
    #             for brand in clothing_wishlisted:
    #                 brand["_id"] = str(brand["_id"])

    #         # Handle food brands
    #         if category in ["food", "both"]:
    #             food_pipeline = [
    #                 # First get all brands and their products
    #                 {
    #                     "$lookup": {
    #                         "from": "food_products",
    #                         "let": { "brandId": "$_id" },
    #                         "pipeline": [
    #                             {
    #                                 "$match": {
    #                                     "$expr": {
    #                                         "$eq": ["$brand_id.$id", "$$brandId"]
    #                                     }
    #                                 }
    #                             }
    #                         ],
    #                         "as": "products"
    #                     }
    #                 },
    #                 # For each brand's products, look up wishlist entries
    #                 {
    #                     "$unwind": {
    #                         "path": "$products",
    #                         "preserveNullAndEmptyArrays": True
    #                     }
    #                 },
    #                 {
    #                     "$lookup": {
    #                         "from": "wishlists",
    #                         "let": { "productId": "$products._id" },
    #                         "pipeline": [
    #                             {
    #                                 "$match": {
    #                                     "$expr": {
    #                                         "$eq": ["$productId.$id", "$$productId"]
    #                                     }
    #                                 }
    #                             }
    #                         ],
    #                         "as": "product_wishlists"
    #                     }
    #                 },
    #                 # Group back by brand to consolidate results
    #                 {
    #                     "$group": {
    #                         "_id": "$_id",
    #                         "brand_name": { "$first": "$brand_name" },
    #                         "all_wishlists": {
    #                             "$push": "$product_wishlists"
    #                         }
    #                     }
    #                 },
    #                 # Flatten the nested arrays of wishlists
    #                 {
    #                     "$addFields": {
    #                         "flattened_wishlists": {
    #                             "$reduce": {
    #                                 "input": "$all_wishlists",
    #                                 "initialValue": [],
    #                                 "in": { "$concatArrays": ["$$value", "$$this"] }
    #                             }
    #                         }
    #                     }
    #                 },
    #                 # Calculate wishlist metrics
    #                 {
    #                     "$addFields": {
    #                         "wishlist_count": { "$size": "$flattened_wishlists" },
    #                         "wishlist_percent": {
    #                             "$cond": [
    #                                 { "$gt": [total_wishlist_count, 0] },
    #                                 {
    #                                     "$multiply": [
    #                                         { 
    #                                             "$divide": [
    #                                                 { "$size": "$flattened_wishlists" },
    #                                                 total_wishlist_count
    #                                             ]
    #                                         },
    #                                         100
    #                                     ]
    #                                 },
    #                                 0
    #                             ]
    #                         }
    #                     }
    #                 },
    #                 # Final projection
    #                 {
    #                     "$project": {
    #                         "_id": 1,
    #                         "brand_name": 1,
    #                         "wishlist_count": 1,
    #                         "wishlist_percent": 1
    #                     }
    #                 },
    #                 # Sort by wishlist count
    #                 { 
    #                     "$sort": { 
    #                         "wishlist_count": -1 
    #                     } 
    #                 }
    #             ]
                
    #             # Execute the pipeline
    #             food_wishlisted = await FoodBrand.aggregate(food_pipeline).to_list()
                
    #             # Convert ObjectId to string for JSON serialization
    #             for brand in food_wishlisted:
    #                 brand["_id"] = str(brand["_id"])

    #         # Structure the response
    #         result = {}
    #         if category in ["clothing", "both"]:
    #             result["clothingWishlistedBrands"] = clothing_wishlisted
    #         if category in ["food", "both"]:
    #             result["foodWishlistedBrands"] = food_wishlisted

    #         return result
    #     except Exception as e:
    #         raise RuntimeError(f"Error fetching wishlisted brands: {str(e)}")

    @staticmethod
    async def get_wishlisted_brands(category: str):
        try:
            clothing_wishlisted = []
            food_wishlisted = []

            # Fetch wishlisted clothing brands
            if category in ["clothing", "both"]:
                # Get total clothing wishlist count
                clothing_wishlist_pipeline = [
                    {
                        "$lookup": {
                            "from": "clothing_products",
                            "localField": "productId.$id",
                            "foreignField": "_id",
                            "as": "product"
                        }
                    },
                    {
                        "$match": {
                            "product": { "$ne": [] }
                        }
                    }
                ]
                clothing_wishlist_count = len(await Wishlist.aggregate(clothing_wishlist_pipeline).to_list())

                clothing_pipeline = [
                    # First get all brands and their products
                    {
                        "$lookup": {
                            "from": "clothing_products",
                            "let": { "brandId": "$_id" },
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$eq": ["$brand_id.$id", "$$brandId"]
                                        }
                                    }
                                }
                            ],
                            "as": "products"
                        }
                    },
                    # For each brand's products, look up wishlist entries
                    {
                        "$unwind": {
                            "path": "$products",
                            "preserveNullAndEmptyArrays": True
                        }
                    },
                    {
                        "$lookup": {
                            "from": "wishlists",
                            "let": { "productId": "$products._id" },
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$eq": ["$productId.$id", "$$productId"]
                                        }
                                    }
                                }
                            ],
                            "as": "product_wishlists"
                        }
                    },
                    # Group back by brand to consolidate results
                    {
                        "$group": {
                            "_id": "$_id",
                            "brand_name": { "$first": "$brand_name" },
                            "all_wishlists": {
                                "$push": "$product_wishlists"
                            }
                        }
                    },
                    # Flatten the nested arrays of wishlists
                    {
                        "$addFields": {
                            "flattened_wishlists": {
                                "$reduce": {
                                    "input": "$all_wishlists",
                                    "initialValue": [],
                                    "in": { "$concatArrays": ["$$value", "$$this"] }
                                }
                            }
                        }
                    },
                    # Calculate wishlist metrics
                    {
                        "$addFields": {
                            "wishlist_count": { "$size": "$flattened_wishlists" },
                            "wishlist_percent": {
                                "$cond": [
                                    { "$gt": [clothing_wishlist_count, 0] },
                                    {
                                        "$round": [
                                            {
                                                "$multiply": [
                                                    {
                                                        "$divide": [
                                                            { "$size": "$flattened_wishlists" },
                                                            clothing_wishlist_count
                                                        ]
                                                    },
                                                    100
                                                ]
                                            },
                                            0  # Specify 0 to round to the nearest integer
                                        ]
                                    },
                                    0
                                ]
                            }
                        }
                    },
                    # Filter out brands with no wishlist items
                    {
                        "$match": {
                            "wishlist_count": { "$gt": 0 }
                        }
                    },
                    # Final projection
                    {
                        "$project": {
                            "_id": 1,
                            "brand_name": 1,
                            "wishlist_count": 1,
                            "wishlist_percent": 1
                        }
                    },
                    # Sort by wishlist count
                    { 
                        "$sort": { 
                            "wishlist_count": -1 
                        } 
                    }
                ]

                clothing_wishlisted = await ClothingBrand.aggregate(clothing_pipeline).to_list()
                for brand in clothing_wishlisted:
                    brand["_id"] = str(brand["_id"])

            # Handle food brands
            if category in ["food", "both"]:
                # Get total food wishlist count
                food_wishlist_pipeline = [
                    {
                        "$lookup": {
                            "from": "food_products",
                            "localField": "productId.$id",
                            "foreignField": "_id",
                            "as": "product"
                        }
                    },
                    {
                        "$match": {
                            "product": { "$ne": [] }
                        }
                    }
                ]
                food_wishlist_count = len(await Wishlist.aggregate(food_wishlist_pipeline).to_list())

                food_pipeline = [
                    # First get all brands and their products
                    {
                        "$lookup": {
                            "from": "food_products",
                            "let": { "brandId": "$_id" },
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$eq": ["$brand_id.$id", "$$brandId"]
                                        }
                                    }
                                }
                            ],
                            "as": "products"
                        }
                    },
                    # For each brand's products, look up wishlist entries
                    {
                        "$unwind": {
                            "path": "$products",
                            "preserveNullAndEmptyArrays": True
                        }
                    },
                    {
                        "$lookup": {
                            "from": "wishlists",
                            "let": { "productId": "$products._id" },
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$eq": ["$productId.$id", "$$productId"]
                                        }
                                    }
                                }
                            ],
                            "as": "product_wishlists"
                        }
                    },
                    # Group back by brand to consolidate results
                    {
                        "$group": {
                            "_id": "$_id",
                            "brand_name": { "$first": "$brand_name" },
                            "all_wishlists": {
                                "$push": "$product_wishlists"
                            }
                        }
                    },
                    # Flatten the nested arrays of wishlists
                    {
                        "$addFields": {
                            "flattened_wishlists": {
                                "$reduce": {
                                    "input": "$all_wishlists",
                                    "initialValue": [],
                                    "in": { "$concatArrays": ["$$value", "$$this"] }
                                }
                            }
                        }
                    },
                    # Calculate wishlist metrics
                    {
                        "$addFields": {
                            "wishlist_count": { "$size": "$flattened_wishlists" },
                            "wishlist_percent": {
                                "$cond": [
                                    { "$gt": [food_wishlist_count, 0] },
                                    {
                                        "$round": [
                                            {
                                                "$multiply": [
                                                    {
                                                        "$divide": [
                                                            { "$size": "$flattened_wishlists" },
                                                            food_wishlist_count
                                                        ]
                                                    },
                                                    100
                                                ]
                                            },
                                            0  # Specify 0 to round to the nearest integer
                                        ]
                                    },
                                    0
                                ]
                            }
                        }
                    },
                    # Filter out brands with no wishlist items
                    {
                        "$match": {
                            "wishlist_count": { "$gt": 0 }
                        }
                    },
                    # Final projection
                    {
                        "$project": {
                            "_id": 1,
                            "brand_name": 1,
                            "wishlist_count": 1,
                            "wishlist_percent": 1
                        }
                    },
                    # Sort by wishlist count
                    { 
                        "$sort": { 
                            "wishlist_count": -1 
                        } 
                    }
                ]
                
                food_wishlisted = await FoodBrand.aggregate(food_pipeline).to_list()
                for brand in food_wishlisted:
                    brand["_id"] = str(brand["_id"])

            # Structure the response
            result = {}
            if category in ["clothing", "both"]:
                result["clothingWishlistedBrands"] = clothing_wishlisted
            if category in ["food", "both"]:
                result["foodWishlistedBrands"] = food_wishlisted

            return result
        except Exception as e:
            raise RuntimeError(f"Error fetching wishlisted brands: {str(e)}")



        