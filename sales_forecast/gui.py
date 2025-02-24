# sales_forecast/gui.py
import tkinter as tk
from tkinter import messagebox
from sales_forecast.data_loader import DataLoader
from sales_forecast.forecast import SalesForecaster
from sales_forecast.excel_exporter import ExcelExporter


class SalesForecastApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sales Forecast Tool")

        self.data_loader = DataLoader()
        self.forecaster = None

        self.label = tk.Label(root, text="Выберите файл с данными (CSV или Excel)")
        self.label.pack(pady=10)

        self.button = tk.Button(root, text="Загрузить данные", command=self.load_data)
        self.button.pack(pady=10)

        self.process_button = tk.Button(root, text="Рассчитать прогноз по дням", command=self.process_data, state=tk.DISABLED)
        self.process_button.pack(pady=10)

        self.save_button = tk.Button(root, text="Сохранить в Excel", command=self.save_results, state=tk.DISABLED)
        self.save_button.pack(pady=10)

    def load_data(self):
        if self.data_loader.load_data():
            self.forecaster = SalesForecaster(self.data_loader.df)
            self.process_button.config(state=tk.NORMAL)
            messagebox.showinfo("Успех", "Данные успешно загружены!")

    def process_data(self):
        if self.forecaster is None:
            messagebox.showerror("Ошибка", "Сначала загрузите данные!")
            return

        self.forecaster.forecast()
        self.save_button.config(state=tk.NORMAL)
        messagebox.showinfo("Успех", "Прогноз продаж по дням на 2025 год рассчитан!")

    def save_results(self):
        if self.forecaster.forecast_df is None:
            messagebox.showerror("Ошибка", "Нет данных для сохранения!")
            return

        if ExcelExporter.save_to_excel(self.forecaster.forecast_df):
            messagebox.showinfo("Успех", "Прогноз сохранен в Excel!")