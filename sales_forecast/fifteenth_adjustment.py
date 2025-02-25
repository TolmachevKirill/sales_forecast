# sales_forecast/fifteenth_adjustment.py

import pandas as pd


def adjust_fifteenth_sales(forecast_df, historical_df):
    """
    Корректирует прогноз продаж для 15-го числа каждого месяца в 2025 году,
    удваивая сумму продаж за 15-е число соответствующего месяца в 2024 году и прибавляя её к прогнозу.

    Args:
        forecast_df (pd.DataFrame): DataFrame с прогнозом, содержащий колонки 'Дата', 'Количество чеков',
                                   'Средняя сумма чека', 'Общая сумма продаж'.
        historical_df (pd.DataFrame): Исторические данные с колонками 'date', 'total_sales'.

    Returns:
        pd.DataFrame: Обновленный forecast_df с примененными корректировками.
    """
    # Фильтруем данные за 2024 год
    df_2024 = historical_df[historical_df["date"].dt.year == 2024]

    # Проверяем наличие данных за 15-е числа
    print("Данные за 15-е числа 2024 года:")
    print(df_2024[df_2024["date"].dt.day == 15][["date", "total_sales"]])

    # Находим суммы продаж за 15-е число каждого месяца в 2024 году
    sales_15th_2024 = df_2024[df_2024["date"].dt.day == 15].groupby(df_2024["date"].dt.month)["total_sales"].sum()
    print("Суммы продаж за 15-е числа 2024 года по месяцам:")
    print(sales_15th_2024)

    # Удваиваем эти суммы
    sales_15th_2024_doubled = sales_15th_2024 * 2
    print("Удвоенные суммы продаж за 15-е числа 2024 года:")
    print(sales_15th_2024_doubled)

    # Проверяем значения Общая сумма продаж для 15-го числа до корректировки
    print("Значения Общая сумма продаж для 15-го числа до корректировки в adjust_fifteenth_sales:")
    print(forecast_df[forecast_df["Дата"].str.endswith("-15")][["Дата", "Общая сумма продаж"]])

    # Применяем корректировку к прогнозу 2025 года для 15-го числа каждого месяца
    for month in range(1, 13):
        date_15th = pd.to_datetime(f"15-{month:02d}-2025", dayfirst=True).strftime("%Y-%m-%d")  # Используем формат "YYYY-MM-DD" с dayfirst=True
        if date_15th in forecast_df["Дата"].values:
            adjustment = sales_15th_2024_doubled.get(month, 0)
            print(f"Корректировка для {date_15th}: добавляем сумму за 15-{month:02d}-2024 (значение: {adjustment})")
            if adjustment > 0:
                current_sales = forecast_df.loc[forecast_df["Дата"] == date_15th, "Общая сумма продаж"].iloc[0]
                new_sales = current_sales + adjustment
                forecast_df.loc[forecast_df["Дата"] == date_15th, "Общая сумма продаж"] = new_sales
                print(f"Обновленная Общая сумма продаж для {date_15th}: {new_sales}")
            else:
                print(f"Предупреждение: Нет данных или корректировка равна 0 для 15-{month:02d}-2024")

    # Проверяем значения Общая сумма продаж для 15-го числа после корректировки
    print("Значения Общая сумма продаж для 15-го числа после корректировки в adjust_fifteenth_sales:")
    print(forecast_df[forecast_df["Дата"].str.endswith("-15")][["Дата", "Общая сумма продаж"]])

    # Гарантируем, что формат "Дата" остается строковым
    forecast_df["Дата"] = forecast_df["Дата"].astype(str)

    return forecast_df