from math import ceil
from app.models.clothing_brand_model import ClothingBrand
from app.models.food_brand_model import FoodBrand
from app.models.clothing_product_model import ClothingProduct
from app.models.food_product_model import FoodProduct
from datetime import datetime, timedelta
from googlemaps import Client as GoogleMapsClient
from app.core.config import settings
from bson import ObjectId

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
    ):
        try:
            # Input validation
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10
            if sortPrice not in [None, "ascending", "descending"]:
                raise ValueError("Invalid sortPrice. Must be 'ascending' or 'descending'.")

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

                # Calculate pagination for each collection
                half_limit = limit // 2
                remainder = limit % 2

                # Get paginated data from both collections
                clothing_data = await get_paginated_data(
                    ClothingProduct, 
                    clothing_pipeline, 
                    skip // 2, 
                    half_limit + (remainder if skip % 2 == 0 else 0)
                )
                
                food_data = await get_paginated_data(
                    FoodProduct, 
                    food_pipeline, 
                    skip // 2, 
                    half_limit + (remainder if skip % 2 == 1 else 0)
                )

                # Combine and sort if needed
                data = []
                c_idx, f_idx = 0, 0
                
                while len(data) < limit and (c_idx < len(clothing_data) or f_idx < len(food_data)):
                    if c_idx < len(clothing_data):
                        data.append(clothing_data[c_idx])
                        c_idx += 1
                    if f_idx < len(food_data) and len(data) < limit:
                        data.append(food_data[f_idx])
                        f_idx += 1

                if sortPrice:
                    data.sort(
                        key=lambda x: x["price"],
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

