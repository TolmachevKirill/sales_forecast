# forecast.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sales_forecast.fifteenth_adjustment import adjust_fifteenth_sales  # Импортируем новый модуль


class SalesForecaster:
    def __init__(self, data):
        # Преобразуем заголовки данных для соответствия коду
        if 'По дням' in data.columns and 'Количество чеков' in data.columns and 'Средняя сумма чека' in data.columns and 'Сумма продажи' in data.columns:
            data = data.rename(columns={
                'По дням': 'date',
                'Количество чеков': 'checks',
                'Средняя сумма чека': 'avg_check',
                'Сумма продажи': 'total_sales'
            })
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

        # Убираем выбросы в avg_check (добавляем жесткий диапазон)
        Q1 = daily_data["avg_check"].quantile(0.25)
        Q3 = daily_data["avg_check"].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = max(Q1 - 1.5 * IQR, 2000)  # Минимум 2000, чтобы исключить аномально низкие значения
        upper_bound = min(Q3 + 1.5 * IQR, 7000)  # Максимум 7000, чтобы исключить аномалии
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

        # Прогнозирование только Количество чеков и Средняя сумма чека
        forecast_checks = {}
        forecast_avg_check = {}
        for column in ["checks", "avg_check"]:
            model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
            model.fit(days, daily_data[column])
            if column == "checks":
                forecast_checks = model.predict(forecast_day_numbers)
            else:
                forecast_avg_check = model.predict(forecast_day_numbers)

        # Создаем DataFrame с прогнозами
        self.forecast_df = pd.DataFrame({
            "Дата": forecast_days,
            "Количество чеков": forecast_checks,
            "Средняя сумма чека": forecast_avg_check
        })

        # Корректировка: прогноз не ниже лучших значений прошлых лет для каждого дня месяца
        self.df["day_of_year"] = self.df["date"].dt.dayofyear  # Номер дня в году
        self.forecast_df["day_of_year"] = self.forecast_df["Дата"].dt.dayofyear

        column_mapping = {
            "Количество чеков": "checks",
            "Средняя сумма чека": "avg_check"
        }

        for forecast_col, original_col in column_mapping.items():
            # Максимальные значения по дням года из исторических данных
            max_values = self.df.groupby("day_of_year")[original_col].max() * 1.05
            # Применяем корректировку
            if forecast_col == "Количество чеков":
                self.forecast_df[forecast_col] = self.forecast_df[forecast_col].apply(
                    lambda x: max(round(x), max_values.get(self.forecast_df.loc[self.forecast_df[forecast_col] == x, "day_of_year"].iloc[0], 0))
                )
            else:
                self.forecast_df[forecast_col] = self.forecast_df.apply(
                    lambda row: max(max_values.get(row["day_of_year"], 0), row[forecast_col]),
                    axis=1
                )

        # Дополнительная корректировка: учет 15-го числа каждого месяца из 2024 года для Количество чеков и Средняя сумма чека
        # Фильтруем данные за 2024 год
        df_2024 = self.df[self.df["date"].dt.year == 2024]
        # Находим средние значения за 15-е число каждого месяца в 2024 году
        checks_15th_2024 = df_2024[df_2024["date"].dt.day == 15].groupby(df_2024["date"].dt.month)["checks"].mean()
        avg_check_15th_2024 = df_2024[df_2024["date"].dt.day == 15].groupby(df_2024["date"].dt.month)["avg_check"].mean()

        # Применяем корректировку к прогнозу 2025 года для 15-го числа каждого месяца
        for month in range(1, 13):
            date_15th = pd.to_datetime(f"15-{month:02d}-2025", dayfirst=True).strftime("%Y-%m-%d")  # Используем формат "YYYY-MM-DD" с dayfirst=True
            if date_15th in self.forecast_df["Дата"].values:
                adjustment_checks = checks_15th_2024.get(month, self.forecast_df["Количество чеков"].mean())
                adjustment_avg_check = avg_check_15th_2024.get(month, self.forecast_df["Средняя сумма чека"].mean())
                if not np.isnan(adjustment_checks) and not np.isnan(adjustment_avg_check):
                    self.forecast_df.loc[self.forecast_df["Дата"] == date_15th, "Количество чеков"] = int(round(adjustment_checks))
                    self.forecast_df.loc[self.forecast_df["Дата"] == date_15th, "Средняя сумма чека"] = adjustment_avg_check

        # Округляем количество чеков до целых чисел после всех корректировок
        self.forecast_df["Количество чеков"] = self.forecast_df["Количество чеков"].round().astype(int)

        # Вычисляем Общую сумму продаж как произведение перед корректировкой 15-го числа
        self.forecast_df["Общая сумма продаж"] = self.forecast_df["Количество чеков"] * self.forecast_df["Средняя сумма чека"]

        # Преобразуем столбец "Дата" в строковый формат для .str.endswith()
        self.forecast_df["Дата"] = self.forecast_df["Дата"].astype(str)

        # Проверяем значения Общая сумма продаж для 15-го числа до корректировки
        print("Значения Общая сумма продаж для 15-го числа до корректировки:")
        print(self.forecast_df[self.forecast_df["Дата"].str.endswith("-15")][["Дата", "Общая сумма продаж"]])

        # Проверяем, есть ли 15-е числа в прогнозе (используем формат "YYYY-MM-DD")
        print("Тип данных столбца 'Дата' до фильтрации:", self.forecast_df["Дата"].dtype)
        print("Первые 5 строк 'Дата' до фильтрации:", self.forecast_df["Дата"].head())
        fifteenth_dates = self.forecast_df[self.forecast_df["Дата"].str.endswith("-15")]
        print("Даты 15-го числа в прогнозе 2025 года:")
        print(fifteenth_dates["Дата"].tolist() if not fifteenth_dates.empty else "Нет строк с 15-м числом")

        # Применяем корректировку 15-го числа из нового модуля
        corrected_forecast_df = adjust_fifteenth_sales(self.forecast_df.copy(), self.df)  # Используем копию и сохраняем результат
        print("Значения Общая сумма продаж для 15-го числа после корректировки:")
        print(corrected_forecast_df[corrected_forecast_df["Дата"].str.endswith("-15")][["Дата", "Общая сумма продаж"]])
        print("Тип данных столбца 'Дата' после корректировки:", corrected_forecast_df["Дата"].dtype)
        print("Первые 5 строк 'Дата' после корректировки:", corrected_forecast_df["Дата"].head())
        print("Проверяем корректированные данные для 15-го числа:")
        corrected_fifteenth_dates = corrected_forecast_df[corrected_forecast_df["Дата"].str.endswith("-15")]
        print(corrected_fifteenth_dates if not corrected_fifteenth_dates.empty else "Нет корректированных строк с 15-м числом")

        # Обновляем self.forecast_df с корректированными данными
        self.forecast_df = corrected_forecast_df

        # Проверяем, сохранились ли корректированные строки
        final_fifteenth_dates = self.forecast_df[self.forecast_df["Дата"].str.endswith("-15")]
        print("Итоговые даты 15-го числа в прогнозе 2025 года:")
        print(final_fifteenth_dates if not final_fifteenth_dates.empty else "Нет итоговых строк с 15-м числом")

        # Удаляем вспомогательный столбец (если он еще есть)
        if "day_of_year" in self.forecast_df.columns:
            self.forecast_df.drop(columns=["day_of_year"], inplace=True)

        print("\nПрогноз по дням (с округлением Количество чеков и корректировкой 15-го числа):\n", self.forecast_df.head())
        print("\nПолный прогноз для 15-го числа каждого месяца:")
        print(self.forecast_df[self.forecast_df["Дата"].str.endswith("-15")])

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