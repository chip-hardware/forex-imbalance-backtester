import pandas as pd
import os

# ============================================================
# 1. DATA LOADING
# ============================================================
columns = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
file_name = 'USDCHF.fx240.csv'

if not os.path.exists(file_name):
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if csv_files:
        file_name = csv_files[0]
    else:
        print("Error: CSV file not found")
        exit()

print(f"Analyzing file: {file_name}...")
df = pd.read_csv(file_name, names=columns, header=None)

# ============================================================
# 2. SETTINGS
# ============================================================
min_impulse_points = 600   # 60 pips (large candle)
h4_bars_in_day = 6
min_wait_days = 14         # Minimum 14 days of consolidation
results = []

print(f"Minimum impulse: {min_impulse_points} points ({min_impulse_points/10} pips)")
print(f"Minimum wait: {min_wait_days} days")

# ============================================================
# 3. SCANNING
# ============================================================
for i in range(len(df) - 100):
    open_p = df.loc[i, 'Open']
    close_p = df.loc[i, 'Close']
    high_p = df.loc[i, 'High']
    low_p = df.loc[i, 'Low']
    
    body_size = abs(open_p - close_p) * 100000
    
    if body_size >= min_impulse_points:
        # Remember the large candle
        impulse_high = max(open_p, close_p)
        impulse_low = min(open_p, close_p)
        imbalance_zone = (impulse_high + impulse_low) / 2.0  # MIDDLE
        
        impulse_date = df.loc[i, 'Date']
        impulse_time = df.loc[i, 'Time']
        is_buy = close_p > open_p
        direction = "UP" if is_buy else "DOWN"
        
        print(f"\nFound impulse: {impulse_date} {impulse_time} {direction} {body_size/10:.1f} pips")
        print(f"  Imbalance zone: {imbalance_zone:.5f}")
        print(f"  Boundaries: {impulse_low:.5f} - {impulse_high:.5f}")
        
        # Look for the first return to the imbalance zone after consolidation
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
            
            # Check if price is still in consolidation (hasn't returned to the zone)
            if close_j < imbalance_zone - 0.00005 or close_j > imbalance_zone + 0.00005:
                # Count days
                if consolidation_start == -1:
                    consolidation_start = j
                
                days_passed = (j - consolidation_start) / h4_bars_in_day
                
                # Measure maximum deviation from the imbalance zone
                if high_j > imbalance_zone:
                    dev = (high_j - imbalance_zone) * 100000
                    if dev > max_deviation_above:
                        max_deviation_above = dev
                if low_j < imbalance_zone:
                    dev = (imbalance_zone - low_j) * 100000
                    if dev > max_deviation_below:
                        max_deviation_below = dev
                
                # Check for fake breaks (entries into the imbalance zone)
                if (low_j <= imbalance_zone <= high_j):
                    fake_breaks += 1
            else:
                # Price returned to the imbalance zone
                if days_passed >= min_wait_days / h4_bars_in_day:
                    entered_zone = j
                    print(f"  ✅ Return to zone after {days_passed:.1f} days")
                break
        
        # Record the result
        if entered_zone != -1 and days_passed >= min_wait_days / h4_bars_in_day:
            total_bars = entered_zone - i
            weeks_to_return = total_bars / 30.0
            
            # What was the direction of return?
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
# 4. STATISTICS
# ============================================================
if len(results) > 0:
    res_df = pd.DataFrame(results)
    res_df.to_csv('Imbalance_Return_Statistics.csv', index=False, sep=';')
    
    print("\n" + "="*60)
    print("STATISTICS OF RETURNS TO IMBALANCE ZONE")
    print("="*60)
    print(f"Total found: {len(res_df)}")
    print(f"Average impulse size: {round(res_df['Impulse_Pips'].mean(), 1)} pips")
    print(f"Average waiting time: {round(res_df['Wait_Days'].mean(), 1)} days")
    print(f"Average time to return: {round(res_df['Weeks_To_Return'].mean(), 1)} weeks")
    print(f"Average number of fake breaks: {round(res_df['Fake_Breaks'].mean(), 1)}")
    
    print("\n--- MAXIMUM DEVIATIONS FROM THE ZONE ---")
    print(f"Average deviation UP: {round(res_df['Max_Dev_Above_Pips'].mean(), 1)} pips")
    print(f"Average deviation DOWN: {round(res_df['Max_Dev_Below_Pips'].mean(), 1)} pips")
    
    print("\n--- DISTRIBUTION BY DIRECTION ---")
    print(res_df['Direction'].value_counts().to_string())
    
    print("\n--- PERCENTILES OF MAX DEVIATIONS (for SL) ---")
    print("Deviation UP:")
    print(f"  90%: {round(res_df['Max_Dev_Above_Pips'].quantile(0.90), 1)} pips")
    print(f"  95%: {round(res_df['Max_Dev_Above_Pips'].quantile(0.95), 1)} pips")
    print("Deviation DOWN:")
    print(f"  90%: {round(res_df['Max_Dev_Below_Pips'].quantile(0.90), 1)} pips")
    print(f"  95%: {round(res_df['Max_Dev_Below_Pips'].quantile(0.95), 1)} pips")
    
    print("\n" + "-"*60)
    print("DETAILED TABLE:")
    cols = ['Impulse_Date', 'Direction', 'Impulse_Pips', 'Wait_Days', 'Fake_Breaks', 'Max_Dev_Above_Pips', 'Max_Dev_Below_Pips']
    print(res_df[cols].to_string(index=False))
    
    print("\nTable saved to: Imbalance_Return_Statistics.csv")
else:
    print(f"\nNo returns to the imbalance zone found.")
    print("Try reducing min_impulse_points or min_wait_days.")
