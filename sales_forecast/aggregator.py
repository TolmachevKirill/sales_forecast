# sales_forecast/aggregator.py
import pandas as pd

class SalesDataAggregator:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

    def preprocess(self):
        # Загружаем файл, начиная со второго столбца (B:E) и второй строки
        self.df = pd.read_excel(self.file_path, usecols="B:E", skiprows=1)

        # Переименовываем столбцы
        self.df.columns = ["date", "checks", "avg_check", "total_sales"]

        # Убираем строки, где дата отсутствует
        self.df = self.df.dropna(subset=["date"])

        # Преобразуем дату
        try:
            self.df["date"] = pd.to_datetime(self.df["date"], format="%d %B %Y г.", dayfirst=True)
        except ValueError:
            self.df["date"] = pd.to_datetime(self.df["date"], format="%d %B %Y", dayfirst=True, errors="coerce")

        # Проверяем ошибки преобразования дат
        if self.df["date"].isna().sum() > 0:
            print("Ошибка преобразования дат! Проблемные строки:")
            print(self.df[self.df["date"].isna()])
            raise ValueError("Ошибка в формате дат, проверьте исходные данные.")

        # Заменяем запятые на точки и приводим к float
        for col in ["checks", "avg_check", "total_sales"]:
            self.df[col] = self.df[col].astype(str).str.replace(",", ".").astype(float)

        # Добавляем столбцы "Год", "Месяц", "Номер месяца"
        self.df["year"] = self.df["date"].dt.year
        self.df["month"] = self.df["date"].dt.month
        self.df["month_number"] = (self.df["year"] - self.df["year"].min()) * 12 + self.df["month"]

        print("Данные успешно обработаны!")
        return self.df
