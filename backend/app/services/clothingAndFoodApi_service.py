from app.models.clothing_brand_model import ClothingBrand
from app.models.food_brand_model import FoodBrand
from app.models.clothing_product_model import ClothingProduct
from app.models.food_product_model import FoodProduct
from datetime import datetime, timedelta
from googlemaps import Client as GoogleMapsClient

GOOGLE_MAPS_API_KEY = "AIzaSyA87Mlrc7Ct2nPdEsQcaBAsCVS53PEqfs4"

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

        gmaps = GoogleMapsClient(key=GOOGLE_MAPS_API_KEY)

        clothing_brands = await ClothingBrand.find_all().to_list()
        food_brands = await FoodBrand.find_all().to_list()

        clothing_brand_names = [brand.brand_name for brand in clothing_brands]
        food_brand_names = [brand.brand_name for brand in food_brands]

        nearby_outlets = []

        if category in ["clothing", "both"]:
            for brand in clothing_brand_names:
                results = gmaps.places_nearby(
                    location=(user_lat, user_lon),
                    radius=1500,
                    keyword=brand
                )
                for result in results.get("results", []):
                    nearby_outlets.append({
                        "category": "clothing",
                        "brand_name": brand,
                        "address": result.get("vicinity"),
                        "location": result.get("geometry", {}).get("location")
                    })

        if category in ["food", "both"]:
            for brand in food_brand_names:
                results = gmaps.places_nearby(
                    location=(user_lat, user_lon),
                    radius=1500,
                    keyword=brand
                )
                for result in results.get("results", []):
                    nearby_outlets.append({
                        "category": "food",
                        "brand_name": brand,
                        "address": result.get("vicinity"),
                        "location": result.get("geometry", {}).get("location")
                    })

        return nearby_outlets

