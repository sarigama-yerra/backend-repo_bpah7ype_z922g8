import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Meal, Subscription, Preference, Macros

app = FastAPI(title="Protein Meals API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Protein-focused Food Delivery Backend"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Seed helper for initial meals if empty
INITIAL_MEALS: List[Meal] = [
    Meal(title="Protein Pancakes", description="Fluffy oat-banana pancakes with whey.", category="Breakfasts", diet_tags=["vegetarian"], price=9.99, macros=Macros(protein=35, carbs=45, fats=8, calories=420), image_url=None, is_customizable=False),
    Meal(title="Spinach Omelette", description="Egg whites, spinach, feta.", category="Breakfasts", diet_tags=["keto"], price=8.50, macros=Macros(protein=32, carbs=6, fats=14, calories=290), image_url=None, is_customizable=False),
    Meal(title="Greek Yogurt Bowl", description="Greek yogurt, berries, almonds.", category="Breakfasts", diet_tags=["low-carb"], price=7.90, macros=Macros(protein=28, carbs=22, fats=10, calories=320), image_url=None, is_customizable=False),
    Meal(title="Chicken Power Bowl", description="Grilled chicken, quinoa, veggies.", category="Main Meals", diet_tags=[], price=12.99, macros=Macros(protein=50, carbs=40, fats=12, calories=520), image_url=None, is_customizable=False),
    Meal(title="Tofu Teriyaki Bowl", description="High-protein tofu, brown rice, broccoli.", category="Main Meals", diet_tags=["vegan"], price=11.50, macros=Macros(protein=35, carbs=55, fats=14, calories=540), image_url=None, is_customizable=False),
    Meal(title="Custom Protein Smoothie", description="Build your own shake.", category="Smoothies & Shakes", diet_tags=["vegan"], price=6.99, macros=Macros(protein=25, carbs=30, fats=6, calories=310), image_url=None, is_customizable=True, available_add_ons=["whey", "vegan protein", "creatine", "peanut butter", "chia seeds"]) 
]

@app.post("/seed")
def seed():
    try:
        existing = db["meal"].count_documents({}) if db is not None else 0
        if existing == 0:
            for m in INITIAL_MEALS:
                create_document("meal", m)
            return {"seeded": True, "count": len(INITIAL_MEALS)}
        return {"seeded": False, "count": existing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/meals")
def list_meals(
    category: Optional[str] = Query(None),
    diet: Optional[str] = Query(None),
    min_protein: Optional[float] = Query(None, ge=0),
):
    try:
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if diet:
            filter_dict["diet_tags"] = {"$in": [diet]}
        meals = get_documents("meal", filter_dict)
        # Basic protein filter
        if min_protein is not None:
            meals = [m for m in meals if m.get("macros", {}).get("protein", 0) >= min_protein]
        # Transform ObjectId to string
        for m in meals:
            if "_id" in m:
                m["id"] = str(m.pop("_id"))
        return {"items": meals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PortionRequest(BaseModel):
    meal_id: str
    servings: float = 1.0

@app.post("/meals/portion")
def get_portion_macros(req: PortionRequest):
    try:
        from bson import ObjectId
        doc = db["meal"].find_one({"_id": ObjectId(req.meal_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Meal not found")
        macros = doc.get("macros", {})
        factor = max(0.25, float(req.servings))
        scaled = {k: round(v * factor, 1) for k, v in macros.items()}
        return {"servings": factor, "macros": scaled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subscriptions")
def create_subscription(payload: Subscription):
    try:
        sub_id = create_document("subscription", payload)
        return {"id": sub_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preferences")
def upsert_preferences(pref: Preference):
    try:
        # upsert by email
        db["preference"].update_one({"email": pref.email}, {"$set": pref.model_dump()}, upsert=True)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

