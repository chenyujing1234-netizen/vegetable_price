"""ORM 模型"""

from app.models.api_key import ApiKey
from app.models.cropland import CroplandYearly
from app.models.market import Market
from app.models.news import News
from app.models.policy import Policy
from app.models.prediction import Prediction
from app.models.price import PriceDaily
from app.models.product import Product
from app.models.region import Region
from app.models.user import PriceAlert, User
from app.models.weather import WeatherDaily

__all__ = [
    "Market",
    "Region",
    "Product",
    "PriceDaily",
    "WeatherDaily",
    "Policy",
    "News",
    "CroplandYearly",
    "Prediction",
    "User",
    "PriceAlert",
    "ApiKey",
]
