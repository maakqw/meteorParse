import pandas as pd
from datetime import timedelta


FILE_PATH = "007_020a.csv"
YEAR = 2012  
DAYS_BEFORE = 10
DAYS_AFTER = 10

SHOWERS = ["LEO", "LYR", "ORI", "SDA", "PER"]

print(f"Чтение файла {FILE_PATH}...")
df = pd.read_csv(FILE_PATH, skipinitialspace=True, engine='python')

if df.columns[-1].startswith('Unnamed'):
    df = df.drop(columns=[df.columns[-1]])
df.columns = [c.strip() for c in df.columns]

df['day(UT)'] = pd.to_datetime(df['day(UT)'], format='%Y/%m/%d', errors='coerce')
df = df.dropna(subset=['day(UT)'])
df = df[df['day(UT)'].dt.year == YEAR]

df['Shower'] = df['Shower'].astype(str).str.strip().str.upper()
print(f"Загружено записей за {YEAR} год: {len(df)}")

results = []

for shower in SHOWERS:

    shower_data = df[df['Shower'].str.contains(shower, na=False)].copy()

    if shower_data.empty:
        print(f"⚠️ [{shower}] Нет данных за {YEAR} год.")
        continue

    daily_stats_all_year = shower_data.groupby(shower_data['day(UT)'].dt.date).agg(
        Count=('ZHR', 'count'),
        NightTime=('NightTime(hour)', 'max')
    ).reset_index()

    daily_stats_all_year = daily_stats_all_year.rename(columns={'day(UT)': 'Date'})

    daily_stats_all_year['Meteors_per_hour'] = daily_stats_all_year.apply(
        lambda row: row['Count'] / row['NightTime'] if row['NightTime'] > 0 else 0,
        axis=1
    )

    peak_row = daily_stats_all_year.loc[daily_stats_all_year['Meteors_per_hour'].idxmax()]
    real_peak_date = pd.to_datetime(peak_row['Date'])
    peak_value = peak_row['Meteors_per_hour']

    print(f"[{shower}] Наивысшая активность: {real_peak_date.date()} (Метеоров/час = {peak_value:.2f})")

    start_date = real_peak_date - timedelta(days=DAYS_BEFORE)
    end_date = real_peak_date + timedelta(days=DAYS_AFTER)

    mask_date = (shower_data['day(UT)'] >= start_date) & (shower_data['day(UT)'] <= end_date)
    filtered = shower_data[mask_date]

    if filtered.empty:
        continue

    final_daily = filtered.groupby(filtered['day(UT)'].dt.date).agg(
        Count=('ZHR', 'count'),
        NightTime=('NightTime(hour)', 'max')
    ).reset_index()

    final_daily = final_daily.rename(columns={'day(UT)': 'Date'})

    final_daily['Meteors_per_hour'] = final_daily.apply(
        lambda row: round(row['Count'] / row['NightTime'], 2) if row['NightTime'] > 0 else 0,
        axis=1
    )

    final_daily['Shower'] = shower
    final_daily['Days_From_Peak'] = (pd.to_datetime(final_daily['Date']) - real_peak_date).dt.days

    results.append(final_daily)
    print(f"[{shower}] Обработано дней: {len(final_daily)}")

if results:
    final_df = pd.concat(results, ignore_index=True)
    final_df = final_df.sort_values(['Shower', 'Days_From_Peak'])

    output_file = f"meteor_peaks_{YEAR}.xlsx"
    final_df.to_excel(output_file, index=False)

    print(f"\nДанные сохранены в файл: {output_file}")
else:
    print("\nНе удалось найти данные.")
