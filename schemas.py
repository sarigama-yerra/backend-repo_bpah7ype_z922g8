"""
Database Schemas for Protein-focused Food Delivery App

Each Pydantic model represents a MongoDB collection.
Collection name = lowercase of class name.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr, conlist, conint, confloat
from typing import Optional, List, Dict, Literal

# Core nutrition structure used across models
class Macros(BaseModel):
    protein: confloat(ge=0) = Field(..., description="Protein grams per serving")
    carbs: confloat(ge=0) = Field(..., description="Carbohydrate grams per serving")
    fats: confloat(ge=0) = Field(..., description="Fat grams per serving")
    calories: confloat(ge=0) = Field(..., description="Calories per serving")

DietTag = Literal["vegan", "vegetarian", "keto", "low-carb", "gluten-free", "dairy-free"]
CategoryType = Literal["Breakfasts", "Main Meals", "Smoothies & Shakes"]

class Meal(BaseModel):
    title: str = Field(..., description="Meal title")
    description: Optional[str] = Field(None, description="Short description")
    category: CategoryType = Field(..., description="Meal category")
    diet_tags: List[DietTag] = Field(default_factory=list, description="Dietary tags")
    price: confloat(ge=0) = Field(..., description="Price per serving in USD")
    macros: Macros = Field(..., description="Nutrition per serving")
    image_url: Optional[str] = Field(None, description="Image URL")
    # For smoothies builder
    is_customizable: bool = Field(False, description="Whether meal supports add-ons/size customization")
    available_add_ons: Optional[List[str]] = Field(default=None, description="Available add-ons for customizable items")

class SmoothiePreset(BaseModel):
    name: str
    base: str
    macros: Macros
    base_price: confloat(ge=0)
    available_add_ons: List[str]

class SubscriptionItem(BaseModel):
    meal_id: str = Field(..., description="MongoDB ObjectId as string")
    servings: confloat(ge=0.5, le=5) = Field(1.0, description="Portion multiplier per delivery")

class Subscription(BaseModel):
    email: EmailStr
    frequency: Literal["weekly", "biweekly", "monthly"]
    target_protein_g_per_day: confloat(ge=20, le=400)
    items: conlist(SubscriptionItem, min_length=1)
    notes: Optional[str] = None

class Preference(BaseModel):
    email: EmailStr
    target_protein_g_per_day: confloat(ge=20, le=400) = 120
    diet_filters: List[DietTag] = []

# Keep example schemas for reference if needed by tools (non-used)
class User(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
