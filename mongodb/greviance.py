from mongodb import college_db

collection_name = "grievance"

collection = college_db[collection_name]


async def get_all_active_grievances():
    records = await collection.find({"status": "Active"})
    return records

