import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


class SalesForecaster:
    def __init__(self, data):
        self.df = data
        self.forecast_df = None

    def forecast(self):
        if self.df is None or self.df.empty:
            print("Ошибка: self.df пустой!")
            return None

        # Добавляем столбец с номером дня от начала данных
        self.df["day_number"] = (self.df["date"] - self.df["date"].min()).dt.days + 1
        daily_data = self.df[["day_number", "checks", "avg_check", "total_sales"]]

        if daily_data.empty:
            print("Ошибка: Данные для обучения пустые!")
            return None

        # Убираем выбросы в avg_check
        Q1 = daily_data["avg_check"].quantile(0.25)
        Q3 = daily_data["avg_check"].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        daily_data = daily_data[
            (daily_data["avg_check"] >= lower_bound) & (daily_data["avg_check"] <= upper_bound)
        ]

        # Подготовка данных для регрессии
        days = daily_data[["day_number"]].values
        start_date = pd.to_datetime("2025-01-01")
        end_date = pd.to_datetime("2025-12-31")
        forecast_days = pd.date_range(start=start_date, end=end_date)
        forecast_day_numbers = np.array((forecast_days - self.df["date"].min()).days) + 1
        forecast_day_numbers = forecast_day_numbers.reshape(-1, 1)

        # Прогнозирование
        forecast = {}
        for column in ["checks", "avg_check", "total_sales"]:
            model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
            model.fit(days, daily_data[column])
            forecast[column] = model.predict(forecast_day_numbers)

        # Создаем DataFrame с прогнозами
        self.forecast_df = pd.DataFrame({
            "Дата": forecast_days,
            "Количество чеков": forecast["checks"],
            "Средняя сумма чека": forecast["avg_check"],
            "Общая сумма продаж": forecast["total_sales"]
        })

        # Корректировка: прогноз не ниже лучших значений прошлых лет для каждого дня месяца
        self.df["day_of_year"] = self.df["date"].dt.dayofyear  # Номер дня в году
        self.forecast_df["day_of_year"] = self.forecast_df["Дата"].dt.dayofyear

        column_mapping = {
            "Количество чеков": "checks",
            "Средняя сумма чека": "avg_check",
            "Общая сумма продаж": "total_sales"
        }

        for forecast_col, original_col in column_mapping.items():
            # Максимальные значения по дням года из исторических данных
            max_values = self.df.groupby("day_of_year")[original_col].max() * 1.05
            # Применяем корректировку, но для "Количество чеков" округляем до целого
            if forecast_col == "Количество чеков":
                self.forecast_df[forecast_col] = self.forecast_df[forecast_col].apply(
                    lambda x: max(int(round(x)), int(max_values.get(self.forecast_df.loc[self.forecast_df[forecast_col] == x, "day_of_year"].iloc[0], 0)))
                )
            else:
                self.forecast_df[forecast_col] = self.forecast_df.apply(
                    lambda row: max(max_values.get(row["day_of_year"], 0), row[forecast_col]),
                    axis=1
                )

        # Удаляем вспомогательный столбец
        self.forecast_df.drop(columns=["day_of_year"], inplace=True)

        # Дополнительная корректировка: учет 15-го числа каждого месяца из 2024 года
        # Фильтруем данные за 2024 год
        df_2024 = self.df[self.df["date"].dt.year == 2024]
        # Находим суммы продаж за 15-е число каждого месяца в 2024 году
        sales_15th_2024 = df_2024[df_2024["date"].dt.day == 15].groupby(df_2024["date"].dt.month)["total_sales"].sum()
        # Удваиваем эти суммы
        sales_15th_2024_doubled = sales_15th_2024 * 2

        # Применяем корректировку к прогнозу 2025 года для 15-го числа каждого месяца
        for month in range(1, 13):
            date_15th = pd.to_datetime(f"15-{month:02d}-2025", dayfirst=True).strftime("%d-%m-2025")
            if date_15th in self.forecast_df["Дата"].values:
                adjustment = sales_15th_2024_doubled.get(month, 0)
                if adjustment > 0:
                    current_sales = self.forecast_df.loc[self.forecast_df["Дата"] == date_15th, "Общая сумма продаж"].iloc[0]
                    self.forecast_df.loc[self.forecast_df["Дата"] == date_15th, "Общая сумма продаж"] = current_sales + adjustment

        # Повторное округление и принудительное приведение к int для количества чеков
        self.forecast_df["Количество чеков"] = self.forecast_df["Количество чеков"].round().astype(int)

        # Форматируем дату в "день-месяц-2025"
        self.forecast_df["Дата"] = self.forecast_df["Дата"].dt.strftime("%d-%m-2025")

        print("\nПрогноз по дням (с округлением и корректировкой 15-го числа):\n", self.forecast_df.head())

        # Визуализация тренда
        historical_sales = self.df.groupby("date")["total_sales"].sum()
        forecast_sales = self.forecast_df.set_index("Дата")["Общая сумма продаж"]

        plt.figure(figsize=(12, 5))
        plt.plot(historical_sales.index, historical_sales.values, label="Фактические данные", marker="o")
        plt.plot(forecast_days, forecast_sales.values, label="Прогноз 2025", marker="o", linestyle="dashed")
        plt.xlabel("Дата")
        plt.ylabel("Общая сумма продаж")
        plt.title("Динамика продаж (История и Прогноз 2025)")
        plt.legend()
        plt.grid()
        plt.show()

        return self.forecast_df