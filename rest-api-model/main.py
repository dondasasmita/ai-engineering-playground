from fastapi import FastAPI, HTTPException
from models.SalesData import SalesData
from models.Prediction import Prediction

app = FastAPI()
prediction = Prediction()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/predict")
def predict(sales_data: SalesData):
    try:
        budget = sales_data.budget
        result = prediction.predict(budget)
        return {"prediction": int(result[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))