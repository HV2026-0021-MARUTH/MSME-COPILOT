from pydantic import BaseModel, Field
from typing import Optional

class ReportParams(BaseModel):
    shop_id: str = "shop_001"
    period: str = Field("7d", description="Report period: today, 7d, 30d")

class ReportSummaryMetadata(BaseModel):
    shop_name: str = "Sri Lakshmi General Store"
    period_code: str
    period_start: str
    period_end: str
    generated_at: str
    data_source: str = "MARUTHI Verified Business Data"
