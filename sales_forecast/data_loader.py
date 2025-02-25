# sales_forecast/data_loader.py
import pandas as pd
from tkinter import filedialog, messagebox


class DataLoader:
    def __init__(self):
        self.df = None

    def load_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            messagebox.showwarning("Ошибка", "Файл не выбран!")
            return False

        try:
            df = pd.read_excel(file_path, engine="openpyxl")
            print("Заголовки столбцов:", df.columns)

            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            required_columns = ["По дням", "Количество чеков", "Средняя сумма чека", "Сумма продажи"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                messagebox.showerror("Ошибка", f"Отсутствуют столбцы: {missing_columns}")
                return False

            df["По дням"] = pd.to_datetime(df["По дням"], errors="coerce", dayfirst=True)
            if df["По дням"].isna().sum() > 0:
                messagebox.showerror("Ошибка", "Некоторые даты не распознаны! Проверь формат.")
                print("Проблемные даты:", df[df["По дням"].isna()])
                return False

            # Переименовываем столбцы
            df.rename(columns={
                "По дням": "date",
                "Количество чеков": "checks",
                "Средняя сумма чека": "avg_check",
                "Сумма продажи": "total_sales"
            }, inplace=True)

            # Преобразуем числа
            df["checks"] = df["checks"].astype(str).str.replace(",", "").astype(int)
            df["avg_check"] = df["avg_check"].astype(str).str.replace(",", ".").astype(float)
            df["total_sales"] = df["total_sales"].astype(str).str.replace(" ", "").str.replace(",", ".").astype(float)

            # Добавляем номер дня от минимальной даты
            df["day_number"] = (df["date"] - df["date"].min()).dt.days + 1

            self.df = df
            return True

        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить Excel: {e}")
            return False