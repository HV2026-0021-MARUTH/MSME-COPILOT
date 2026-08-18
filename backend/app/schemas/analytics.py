from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SalesTrendPoint(BaseModel):
    date: str
    revenue: float
    cost: float
    profit: float
    units_sold: int

class SalesTrendResponse(BaseModel):
    period_days: int
    data: List[SalesTrendPoint]
    total_revenue: float
    total_profit: float
    total_units: int

class ProductPerformanceItem(BaseModel):
    product_id: str
    name: str
    category: str
    brand: Optional[str] = None
    selling_price: float
    purchase_price: float
    units_sold: int
    revenue: float
    cost: float
    profit: float
    margin_pct: float
    current_stock: int
    inventory_value: float
    reorder_level: int
    average_daily_demand: float
    days_of_stock: Optional[float] = None
    stock_status: str

class SlowMovingProductItem(BaseModel):
    product_id: str
    name: str
    current_stock: int
    units_sold_30d: int
    velocity_per_day: float
    last_sale_date: Optional[str] = None
    reason: str
    status: str

class PlanningSuggestion(BaseModel):
    title: str = "Planning Suggestion"
    target_days: int
    target_stock: int
    recommended_purchase: int
    reason: str

class ForecastExplanation(BaseModel):
    recent_7d_avg: float
    prev_7d_avg: float
    recent_30d_avg: float
    formula: str
    data_points_count: int

class ForecastItem(BaseModel):
    product_id: str
    name: str
    category: str
    current_stock: int
    reorder_level: int
    forecast_status: str
    forecast_daily_demand: float
    days_of_stock: Optional[float] = None
    stock_status: str
    reason: str
    planning_suggestion: PlanningSuggestion
    explanation: ForecastExplanation

class ForecastResponse(BaseModel):
    shop_id: str
    total_products: int
    forecasts: List[ForecastItem]

class ProductDetailAnalytics(BaseModel):
    product_id: str
    name: str
    category: str
    brand: Optional[str] = None
    unit: str
    purchase_price: float
    selling_price: float
    reorder_level: int
    current_stock: int
    inventory_value: float
    units_sold_total: int
    revenue_total: float
    cost_total: float
    profit_total: float
    margin_pct: float
    forecast: ForecastItem
    recent_sales: List[Dict[str, Any]] = []

class DashboardSummaryResponse(BaseModel):
    shop_id: str
    today_revenue: float
    today_sales: float
    today_profit: float
    today_margin: float
    inventory_value: float
    total_products: int
    low_stock_count: int
    out_of_stock_count: int
    top_selling_products: List[Dict[str, Any]]
    profit_leaders: List[Dict[str, Any]]
    slow_moving_products: List[SlowMovingProductItem]
    reorder_suggestions: List[ForecastItem]
