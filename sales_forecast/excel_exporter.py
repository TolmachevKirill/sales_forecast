# sales_forecast/excel_exporter.py
from openpyxl import Workbook
from tkinter import filedialog

class ExcelExporter:
    @staticmethod
    def save_to_excel(data):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            wb = Workbook()
            ws = wb.active
            ws.append(["Месяц", "Количество чеков", "Средняя сумма чека", "Общая сумма продаж"])
            for _, row in data.iterrows():
                ws.append(row.tolist())
            wb.save(file_path)
            return True
        return False