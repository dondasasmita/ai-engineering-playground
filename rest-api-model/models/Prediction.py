import os
import pickle
import pandas as pd
from sklearn.linear_model import LinearRegression

class Prediction:
    def __init__(self):
        base_path = os.path.dirname(__file__)
        file_path = os.path.join(base_path, "simple_linear_regression.pkl")
        self.model = pickle.load(open(file_path, "rb"))

    def predict(self, budget):
        df = pd.DataFrame([int(budget)], columns=['Marketing Budget (X) in Thousands'])
        return self.model.predict(df)