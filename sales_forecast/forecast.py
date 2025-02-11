
# sales_forecast/forecast.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from statsmodels.tsa.statespace.sarimax import SARIMAX


class SalesForecaster:
    def __init__(self, data):
        self.df = data
        self.forecast_df = None

    def forecast(self):
        if self.df is None or self.df.empty:
            print("Ошибка: self.df пустой!")
            return None

        # Агрегация данных по месяцам
        monthly_data = self.df.groupby("month_number").agg({
            "checks": "sum",
            "avg_check": "mean",
            "total_sales": "sum"
        }).reset_index()

        if monthly_data.empty:
            print("Ошибка: Данные для обучения пустые!")
            return None

        # Убираем выбросы в avg_check
        Q1 = monthly_data["avg_check"].quantile(0.25)
        Q3 = monthly_data["avg_check"].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        monthly_data = monthly_data[
            (monthly_data["avg_check"] >= lower_bound) & (monthly_data["avg_check"] <= upper_bound)]

        # Подготовка данных для прогноза
        months = monthly_data[["month_number"]].values
        forecast_months = np.arange(37, 49).reshape(-1, 1)

        forecast = {}
        for column in ["checks", "avg_check", "total_sales"]:
            model = SARIMAX(monthly_data[column], order=(1, 1, 1), seasonal_order=(0, 1, 1, 12))
            sarima_result = model.fit(disp=False)
            forecast[column] = sarima_result.forecast(steps=12)

        # Создаем DataFrame с прогнозами
        self.forecast_df = pd.DataFrame(forecast_months, columns=["month_number"])
        self.forecast_df["Количество чеков"] = forecast["checks"].values
        self.forecast_df["Средняя сумма чека"] = forecast["avg_check"].values
        self.forecast_df["Общая сумма продаж"] = forecast["total_sales"].values

        # Преобразуем "month_number" в дату
        base_year = 2022
        self.forecast_df["Год"] = (base_year + (self.forecast_df["month_number"] - 1) // 12).astype(int)
        self.forecast_df["Месяц_номер"] = ((self.forecast_df["month_number"] - 1) % 12 + 1).astype(int)

        # Исправлено: преобразование в дату
        self.forecast_df["Дата"] = pd.to_datetime(
            self.forecast_df["Год"].astype(int).astype(str) + "-" +
            self.forecast_df["Месяц_номер"].astype(int).astype(str) + "-01"
        )

        # Удаляем вспомогательные столбцы
        self.forecast_df.drop(columns=["month_number", "Год", "Месяц_номер"], inplace=True)

        # Переставляем столбцы
        self.forecast_df = self.forecast_df[["Дата", "Количество чеков", "Средняя сумма чека", "Общая сумма продаж"]]

        # Проверка: прогноз не ниже лучших значений прошлых лет
        column_mapping = {
            "Количество чеков": "checks",
            "Средняя сумма чека": "avg_check",
            "Общая сумма продаж": "total_sales"
        }

        for forecast_col, original_col in column_mapping.items():
            min_values = self.df.groupby("month_number")[original_col].max()
            min_values = min_values.reindex(range(37, 49), fill_value=0) * 1.05
            self.forecast_df[forecast_col] = np.maximum(self.forecast_df[forecast_col], min_values.values)

        print("\nПрогноз после корректировки:\n", self.forecast_df)

        # Визуализация тренда
        historical_sales = self.df.groupby("month_number")["total_sales"].sum()
        forecast_sales = self.forecast_df.set_index("Дата")["Общая сумма продаж"]

        plt.figure(figsize=(12, 5))

        # Преобразуем ось X к датам
        historical_sales.index = pd.to_datetime(base_year + (historical_sales.index - 1) // 12, format='%Y') + \
                                 pd.to_timedelta(((historical_sales.index - 1) % 12) * 30, unit='D')

        forecast_sales.index = pd.to_datetime(forecast_sales.index)

        plt.plot(historical_sales.index, historical_sales.values, label="Фактические данные (2022–2024)", marker="o")
        plt.plot(forecast_sales.index, forecast_sales.values, label="Прогноз 2025", marker="o", linestyle="dashed")

        # Улучшенная разметка оси X
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # Каждые 3 месяца
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))  # Формат YYYY-MM
        plt.xticks(rotation=45)  # Наклон для удобочитаемости

        plt.xlabel("Месяц")
        plt.ylabel("Общая сумма продаж")
        plt.title("Динамика продаж (2022–2025)")
        plt.legend()
        plt.grid()
        plt.show()

        return self.forecast_df
