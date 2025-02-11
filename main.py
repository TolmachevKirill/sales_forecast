# main.py
from sales_forecast.gui import SalesForecastApp
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = SalesForecastApp(root)
    root.mainloop()