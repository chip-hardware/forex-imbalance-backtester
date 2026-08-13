import pandas as pd
import os

# ============================================================
# 1. ЗАВАНТАЖЕННЯ ДАНИХ
# ============================================================
columns = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
file_name = 'USDCHF.fx240.csv'

if not os.path.exists(file_name):
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if csv_files:
        file_name = csv_files[0]
    else:
        print("Помилка: CSV файл не знайдено")
        exit()

print(f"Аналізуємо файл: {file_name}...")
df = pd.read_csv(file_name, names=columns, header=None)

# ============================================================
# 2. НАЛАШТУВАННЯ
# ============================================================
min_impulse_points = 600   # 60 піпсів (велика свічка)
h4_bars_in_day = 6
min_wait_days = 14         # Мінімум 14 днів консолідації
results = []

print(f"Мінімальний імпульс: {min_impulse_points} пунктів ({min_impulse_points/10} піпсів)")
print(f"Мінімальне очікування: {min_wait_days} днів")

# ============================================================
# 3. СКАНУВАННЯ
# ============================================================
for i in range(len(df) - 100):
    open_p = df.loc[i, 'Open']
    close_p = df.loc[i, 'Close']
    high_p = df.loc[i, 'High']
    low_p = df.loc[i, 'Low']
    
    body_size = abs(open_p - close_p) * 100000
    
    if body_size >= min_impulse_points:
        # Запам'ятовуємо велику свічку
        impulse_high = max(open_p, close_p)
        impulse_low = min(open_p, close_p)
        imbalance_zone = (impulse_high + impulse_low) / 2.0  # СЕРЕДИНА
        
        impulse_date = df.loc[i, 'Date']
        impulse_time = df.loc[i, 'Time']
        is_buy = close_p > open_p
        direction = "UP" if is_buy else "DOWN"
        
        print(f"\nЗнайдено імпульс: {impulse_date} {impulse_time} {direction} {body_size/10:.1f} піпсів")
        print(f"  Зона дисбалансу: {imbalance_zone:.5f}")
        print(f"  Межі: {impulse_low:.5f} - {impulse_high:.5f}")
        
        # Шукаємо перше повернення в зону дисбалансу після консолідації
        entered_zone = -1
        days_passed = 0
        bars_passed = 0
        max_deviation_above = 0
        max_deviation_below = 0
        fake_breaks = 0
        consolidation_start = -1
        
        for j in range(i + 1, len(df)):
            high_j = df.loc[j, 'High']
            low_j = df.loc[j, 'Low']
            close_j = df.loc[j, 'Close']
            
            # Перевіряємо, чи ціна ще в консолідації (не повернулася в зону)
            if close_j < imbalance_zone - 0.00005 or close_j > imbalance_zone + 0.00005:
                # Рахуємо дні
                if consolidation_start == -1:
                    consolidation_start = j
                
                days_passed = (j - consolidation_start) / h4_bars_in_day
                
                # Вимірюємо максимальне відхилення від зони дисбалансу
                if high_j > imbalance_zone:
                    dev = (high_j - imbalance_zone) * 100000
                    if dev > max_deviation_above:
                        max_deviation_above = dev
                if low_j < imbalance_zone:
                    dev = (imbalance_zone - low_j) * 100000
                    if dev > max_deviation_below:
                        max_deviation_below = dev
                
                # Перевіряємо фальшиві пробої (заходи в зону дисбалансу)
                if (low_j <= imbalance_zone <= high_j):
                    fake_breaks += 1
            else:
                # Ціна повернулася в зону дисбалансу
                if days_passed >= min_wait_days / h4_bars_in_day:
                    entered_zone = j
                    print(f"  ✅ Повернення в зону через {days_passed:.1f} днів")
                break
        
        # Фіксуємо результат
        if entered_zone != -1 and days_passed >= min_wait_days / h4_bars_in_day:
            total_bars = entered_zone - i
            weeks_to_return = total_bars / 30.0
            
            # Який був напрямок повернення?
            close_at_return = df.loc[entered_zone, 'Close']
            return_direction = "UP" if close_at_return > imbalance_zone else "DOWN"
            
            results.append({
                'Impulse_Date': impulse_date,
                'Impulse_Time': impulse_time,
                'Direction': direction,
                'Impulse_Pips': round(body_size / 10, 1),
                'Imbalance_Zone': round(imbalance_zone, 5),
                'Wait_Days': round(days_passed, 1),
                'Weeks_To_Return': round(weeks_to_return, 1),
                'Max_Dev_Above_Pips': round(max_deviation_above / 10, 1),
                'Max_Dev_Below_Pips': round(max_deviation_below / 10, 1),
                'Fake_Breaks': fake_breaks,
                'Return_Direction': return_direction
            })

# ============================================================
# 4. СТАТИСТИКА
# ============================================================
if len(results) > 0:
    res_df = pd.DataFrame(results)
    res_df.to_csv('Imbalance_Return_Statistics.csv', index=False, sep=';')
    
    print("\n" + "="*60)
    print("СТАТИСТИКА ПОВЕРНЕНЬ В ЗОНУ ДИСБАЛАНСУ")
    print("="*60)
    print(f"Всього знайдено: {len(res_df)}")
    print(f"Середній розмір імпульсу: {round(res_df['Impulse_Pips'].mean(), 1)} піпсів")
    print(f"Середній час очікування: {round(res_df['Wait_Days'].mean(), 1)} днів")
    print(f"Середній час до повернення: {round(res_df['Weeks_To_Return'].mean(), 1)} тижнів")
    print(f"Середня кількість фальшивих пробоїв: {round(res_df['Fake_Breaks'].mean(), 1)}")
    
    print("\n--- МАКСИМАЛЬНІ ВІДХИЛЕННЯ ВІД ЗОНИ ---")
    print(f"Середнє відхилення ВГОРУ: {round(res_df['Max_Dev_Above_Pips'].mean(), 1)} піпсів")
    print(f"Середнє відхилення ВНИЗ: {round(res_df['Max_Dev_Below_Pips'].mean(), 1)} піпсів")
    
    print("\n--- РОЗПОДІЛ ЗА НАПРЯМКОМ ---")
    print(res_df['Direction'].value_counts().to_string())
    
    print("\n--- ПЕРЦЕНТИЛІ МАКС. ВІДХИЛЕНЬ (для SL) ---")
    print("Відхилення ВГОРУ:")
    print(f"  90%: {round(res_df['Max_Dev_Above_Pips'].quantile(0.90), 1)} піпсів")
    print(f"  95%: {round(res_df['Max_Dev_Above_Pips'].quantile(0.95), 1)} піпсів")
    print("Відхилення ВНИЗ:")
    print(f"  90%: {round(res_df['Max_Dev_Below_Pips'].quantile(0.90), 1)} піпсів")
    print(f"  95%: {round(res_df['Max_Dev_Below_Pips'].quantile(0.95), 1)} піпсів")
    
    print("\n" + "-"*60)
    print("ДЕТАЛЬНА ТАБЛИЦЯ:")
    cols = ['Impulse_Date', 'Direction', 'Impulse_Pips', 'Wait_Days', 'Fake_Breaks', 'Max_Dev_Above_Pips', 'Max_Dev_Below_Pips']
    print(res_df[cols].to_string(index=False))
    
    print("\nТаблиця збережена в: Imbalance_Return_Statistics.csv")
else:
    print(f"\nНе знайдено жодного повернення в зону дисбалансу.")
    print("Спробуйте зменшити min_impulse_points або min_wait_days.")