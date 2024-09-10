from pydantic import BaseModel, validator

class SalesData(BaseModel):
    budget: float

    @validator('budget')
    def budget_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError('budget must be positive')
        return value
    
    @validator('budget')
    def budget_within_range(cls, value):
        if value > 999999:
            raise ValueError('budget must be less than or equal to 999999')
        return value