from app.models.clothing_product_model import ClothingProduct
from math import ceil

class ClothingService:
    @staticmethod
    async def get_all_clothing_products(
        page: int = 1, limit: int = 10, search: str = None, brand_name: str = None
    ):
        try:
            # Validate inputs
            if page < 1:
                page = 1
            if limit < 1:
                limit = 10

            # Calculate the number of documents to skip
            skip = (page - 1) * limit

            # Build the $match stage for searching
            match_conditions = []
            if search:
                match_conditions.append({
                    "$or": [
                        {"title": {"$regex": search, "$options": "i"}},  # Case-insensitive search in title
                        {"brand_info.brand_name": {"$regex": search, "$options": "i"}}  # Case-insensitive search in brand_name
                    ]
                })
            if brand_name:
                match_conditions.append({
                    "brand_info.brand_name": {"$regex": brand_name, "$options": "i"}  # Case-insensitive exact brand name match
                })

            # Combine all conditions into a single $and condition
            match_stage = {"$and": match_conditions} if match_conditions else {}

            # MongoDB aggregation pipeline
            pipeline = [
                {
                    "$addFields": {
                        "brand_id": {"$ifNull": ["$brand_id.$id", None]}
                    }
                },
                {
                    "$lookup": {
                        "from": "clothing_brands",  
                        "localField": "brand_id",  
                        "foreignField": "_id",     
                        "as": "brand_info"
                    }
                },
                {
                    "$unwind": "$brand_info"
                },
                {
                    "$match": match_stage  # Add search and brand filter
                } if match_stage else {},  # Include only if filters exist
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "title": 1,
                        "product_page": 1,
                        "image_url": 1,
                        "original_price": 1,
                        "sale_price": 1,
                        "brand_name": "$brand_info.brand_name"
                    }
                },
                {
                    "$facet": {
                        "metadata": [
                            {"$count": "total"},  # Total number of documents
                        ],
                        "data": [
                            {"$skip": skip},      # Skip the documents
                            {"$limit": limit},    # Limit the number of documents
                        ]
                    }
                }
            ]

            # Run the aggregation query
            result = await ClothingProduct.aggregate(pipeline).to_list()
            metadata = result[0]["metadata"]
            data = result[0]["data"]

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
            raise RuntimeError(f"An error occurred while retrieving clothing products: {str(e)}")