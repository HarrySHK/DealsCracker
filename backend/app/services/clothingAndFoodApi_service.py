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
    
    # @staticmethod
    # async def get_all_products(
    #     category: str = None,  # Can be "food", "clothing", or "both"
    #     page: int = 1,
    #     limit: int = 10,
    #     search: str = None,
    #     brand_name: str = None,
    # ):
    #     try:
    #         # Validate inputs
    #         if page < 1:
    #             page = 1
    #         if limit < 1:
    #             limit = 10

    #         # Calculate the number of documents to skip
    #         skip = (page - 1) * limit

    #         # Build filters for search and brand name
    #         match_conditions = []
    #         if search:
    #             match_conditions.append({
    #                 "$or": [
    #                     {"title": {"$regex": search, "$options": "i"}},  # Case-insensitive search in title
    #                     {"brand_info.brand_name": {"$regex": search, "$options": "i"}}  # Case-insensitive search in brand name
    #                 ]
    #             })
    #         if brand_name:
    #             match_conditions.append({
    #                 "brand_info.brand_name": {"$regex": brand_name, "$options": "i"}  # Case-insensitive exact brand name match
    #             })

    #         # Combine conditions
    #         match_stage = {"$and": match_conditions} if match_conditions else None

    #         # Aggregation pipelines for clothing and food products
    #         def create_pipeline(collection_name, category_name):
    #             pipeline = [
    #                 {
    #                     "$addFields": {
    #                         "brand_id": {"$ifNull": ["$brand_id.$id", None]}
    #                     }
    #                 },
    #                 {
    #                     "$lookup": {
    #                         "from": collection_name,
    #                         "localField": "brand_id",
    #                         "foreignField": "_id",
    #                         "as": "brand_info"
    #                     }
    #                 },
    #                 {"$unwind": "$brand_info"},
    #             ]
    #             if match_stage:  # Add filters only if match_stage is not empty
    #                 pipeline.append({"$match": match_stage})
    #             pipeline.append({
    #                 "$project": {
    #                     "_id": {"$toString": "$_id"},
    #                     "title": 1,
    #                     "product_page": 1,
    #                     "product_url": 1,
    #                     "image_url": 1,
    #                     "original_price": 1,
    #                     "sale_price": 1 if category_name == "clothing" else None,
    #                     "discount_price": 1 if category_name == "food" else None,
    #                     "category": {"$literal": category_name},
    #                     "brand_name": "$brand_info.brand_name",
    #                     "isWishlist": {"$literal": False}
    #                 }
    #             })
    #             pipeline.append({
    #                 "$facet": {
    #                     "metadata": [{"$count": "total"}],
    #                     "data": [
    #                         {"$skip": skip},
    #                         {"$limit": limit}
    #                     ]
    #                 }
    #             })
    #             return pipeline

    #         # Build separate pipelines for clothing and food
    #         clothing_pipeline = create_pipeline("clothing_brands", "clothing") if category in ["clothing", "both"] else []
    #         food_pipeline = create_pipeline("food_brands", "food") if category in ["food", "both"] else []

    #         # Combine pipelines based on category
    #         if category == "clothing":
    #             pipeline = clothing_pipeline
    #             result = await ClothingProduct.aggregate(pipeline).to_list()
    #         elif category == "food":
    #             pipeline = food_pipeline
    #             result = await FoodProduct.aggregate(pipeline).to_list()
    #         elif category == "both":
    #             # Retrieve clothing and food results
    #             clothing_result = await ClothingProduct.aggregate(clothing_pipeline).to_list()
    #             food_result = await FoodProduct.aggregate(food_pipeline).to_list()

    #             # Get the total counts for both categories
    #             clothing_metadata = clothing_result[0]["metadata"] if clothing_result else []
    #             food_metadata = food_result[0]["metadata"] if food_result else []
                
    #             total_clothing_items = clothing_metadata[0]["total"] if clothing_metadata else 0
    #             total_food_items = food_metadata[0]["total"] if food_metadata else 0
                
    #             total_items = total_clothing_items + total_food_items

    #             # Calculate total pages for both categories
    #             total_clothing_pages = ceil(total_clothing_items / limit) if total_clothing_items > 0 else 0
    #             total_food_pages = ceil(total_food_items / limit) if total_food_items > 0 else 0
    #             total_pages = total_clothing_pages + total_food_pages

    #             # Interlace clothing and food results
    #             combined_result = []
    #             max_len = max(len(clothing_result[0]["data"]), len(food_result[0]["data"]))

    #             for i in range(max_len):
    #                 if i < len(clothing_result[0]["data"]):
    #                     combined_result.append(clothing_result[0]["data"][i])
    #                 if i < len(food_result[0]["data"]):
    #                     combined_result.append(food_result[0]["data"][i])

    #             # Pagination for combined results
    #             skip = (page - 1) * limit
    #             paginated_data = combined_result[skip: skip + limit]

    #             return {
    #                 "currentPage": page,
    #                 "totalPages": total_pages,
    #                 "totalItems": total_items,
    #                 "products": paginated_data
    #             }

    #         # Handle results for a single category
    #         metadata = result[0]["metadata"] if result and "metadata" in result[0] else []
    #         data = result[0]["data"] if result and "data" in result[0] else []

    #         # Calculate total pages
    #         total = metadata[0]["total"] if metadata else 0
    #         total_pages = ceil(total / limit)

    #         return {
    #             "currentPage": page,
    #             "totalPages": total_pages,
    #             "totalItems": total,
    #             "products": data
    #         }

    #     except Exception as e:
    #         raise RuntimeError(f"An error occurred while retrieving products: {str(e)}")
    
    @staticmethod
    async def get_all_products(
        category: str = None,  # Can be "food", "clothing", or "both"
        page: int = 1,
        limit: int = 10,
        search: str = None,
        brand_name: str = None,
        latest: bool = True,  # Sort order for createdAt or created_at field
    ):
        try:
            # Validate inputs
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10

            # Calculate the number of documents to skip
            skip = (page - 1) * limit

            # Build filters for search and brand name
            match_conditions = []
            if search:
                match_conditions.append({
                    "$or": [
                        {"title": {"$regex": search, "$options": "i"}},  # Case-insensitive search in title
                        {"brand_info.brand_name": {"$regex": search, "$options": "i"}}  # Case-insensitive search in brand name
                    ]
                })
            if brand_name:
                match_conditions.append({
                    "brand_info.brand_name": {"$regex": brand_name, "$options": "i"}  # Case-insensitive exact brand name match
                })

            # Combine conditions
            match_stage = {"$and": match_conditions} if match_conditions else None

            # Define sort stage for created_at/createdAt
            sort_order = -1 if latest else 1

            # Aggregation pipelines for clothing and food products
            def create_pipeline(collection_name, category_name, date_field):
                pipeline = [
                    {
                        "$addFields": {
                            "brand_id": {"$ifNull": ["$brand_id.$id", None]}
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
                ]
                if match_stage:  # Add filters only if match_stage is not empty
                    pipeline.append({"$match": match_stage})
                pipeline.append({"$sort": {date_field: sort_order}})  # Add sort stage
                pipeline.append({
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
                        "isWishlist": {"$literal": False}
                    }
                })
                pipeline.append({
                    "$facet": {
                        "metadata": [{"$count": "total"}],
                        "data": [
                            {"$skip": skip},
                            {"$limit": limit}
                        ]
                    }
                })
                return pipeline

            # Build separate pipelines for clothing and food
            clothing_pipeline = create_pipeline("clothing_brands", "clothing", "created_at") if category in ["clothing", "both"] else []
            food_pipeline = create_pipeline("food_brands", "food", "createdAt") if category in ["food", "both"] else []

            # Combine pipelines based on category
            if category == "clothing":
                pipeline = clothing_pipeline
                result = await ClothingProduct.aggregate(pipeline).to_list()
            elif category == "food":
                pipeline = food_pipeline
                result = await FoodProduct.aggregate(pipeline).to_list()
            elif category == "both":
                # Retrieve clothing and food results
                clothing_result = await ClothingProduct.aggregate(clothing_pipeline).to_list()
                food_result = await FoodProduct.aggregate(food_pipeline).to_list()

                # Combine and paginate results
                combined_result = []
                max_len = max(len(clothing_result[0]["data"]), len(food_result[0]["data"])) if clothing_result and food_result else 0

                for i in range(max_len):
                    if clothing_result and i < len(clothing_result[0]["data"]):
                        combined_result.append(clothing_result[0]["data"][i])
                    if food_result and i < len(food_result[0]["data"]):
                        combined_result.append(food_result[0]["data"][i])

                # Pagination for combined results
                skip = (page - 1) * limit
                paginated_data = combined_result[skip: skip + limit]

                total_clothing_items = clothing_result[0]["metadata"][0]["total"] if clothing_result and clothing_result[0]["metadata"] else 0
                total_food_items = food_result[0]["metadata"][0]["total"] if food_result and food_result[0]["metadata"] else 0

                return {
                    "currentPage": page,
                    "totalPages": ceil((total_clothing_items + total_food_items) / limit),
                    "totalItems": total_clothing_items + total_food_items,
                    "products": paginated_data
                }

            # Handle results for a single category
            metadata = result[0]["metadata"] if result and "metadata" in result[0] else []
            data = result[0]["data"] if result and "data" in result[0] else []

            # Calculate total pages
            total = metadata[0]["total"] if metadata else 0
            total_pages = ceil(total / limit)

            return {
                "currentPage": page,
                "totalPages": total_pages,
                "totalItems": total,
                "products": data
            }

        except Exception as e:
            raise RuntimeError(f"An error occurred while retrieving products: {str(e)}")






