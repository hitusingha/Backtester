import streamlit as st
import pandas as pd
import numpy as np
import glob

# Page configuration
st.set_page_config(page_title="Crypto Real Backtester", layout="wide")

st.title("📈 Crypto Trading Strategy Backtester (Real Data)")
st.subheader("आपके अपलोड किए गए असली डेटा पर टेस्टिंग")

# 1. Load and Combine All CSV Files Automatically
@st.cache_data
def load_combined_data():
    csv_files = glob.glob("*.csv")
    if not csv_files:
        return None
    
    df_list = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            # Column names को साफ़ और छोटे अक्षरों में करना
            df.columns = df.columns.str.strip().str.lower()
            
            # अगर कॉलम का नाम date, time या timestamp है तो उसे 'date' कर दो
            for col in df.columns:
                if col in ['date', 'timestamp', 'time', 'datetime']:
                    df.rename(columns={col: 'date'}, inplace=True)
                    break
            
            # अगर कॉलम का नाम price है तो उसे 'close' कर दो
            if 'price' in df.columns and 'close' not in df.columns:
                df.rename(columns={'price': 'close'}, inplace=True)
            elif 'close/last' in df.columns:
                df.rename(columns={'close/last': 'close'}, inplace=True)
                
            if 'close' in df.columns:
                df_list.append(df[['date', 'close']])
        except Exception as e:
            st.error(f"फाइल {file} को पढ़ने में दिक्कत हुई: {e}")
            
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
        if 'date' in combined_df.columns:
            # तारीख को सही फॉर्मेट में बदलना
            combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce')
            combined_df.dropna(subset=['date'], inplace=True)
            
            # एरर फिक्स: कीमत (Close) कॉलम को जबरन नंबर (Float) में बदलना ताकी एरर न आए
            combined_df['close'] = combined_df['close'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            combined_df['close'] = pd.to_numeric(combined_df['close'], errors='coerce')
            combined_df.dropna(subset=['close'], inplace=True)
            
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
            return combined_df
    return None

data = load_combined_data()

if data is None or len(data) == 0:
    st.warning("⚠️ कृपया GitHub पर अपनी CSV फाइलें सही से अपलोड करें। अभी कोई मान्य डेटा नहीं मिला है।")
else:
    # साल का कॉलम बनाना
    data['year'] = data['date'].dt.year
    years = sorted(data['year'].unique())
    
    # === साइडबार सेटिंग्स (Sidebar Inputs) ===
    st.sidebar.header("⚙️ बैकटेस्टर सेटिंग्स")
    
    # 1. ईयर बाय ईयर सिलेक्शन
    selected_year = st.sidebar.selectbox("वर्ष चुनें (Select Year)", ["सभी (All)"] + [str(y) for y in years])

    # 2. टोटल मनी इनपुट (Initial Capital)
    initial_capital = st.sidebar.number_input("शुरुआती पूँजी / Total Money (INR)", value=20000, step=1000)
    
    # 3. पर ट्रेड रिस्क (Risk Per Trade)
    risk_per_trade_pct = st.sidebar.slider("प्रति ट्रेड रिस्क / Risk (%)", 0.5, 10.0, 2.0, 0.5)
    
    # 4. रिवॉर्ड रेश्यो (Reward Ratio)
    risk_reward_ratio = st.sidebar.slider("रिस्क-रिवॉर्ड रेश्यो / Reward (1:X)", 1.0, 5.0, 2.0, 0.5)
    
    # 5. मूविंग एवरेज पीरियड
    sma_period = st.sidebar.slider("Moving Average Period", 5, 50, 20)

    # चुने हुए साल के हिसाब से डेटा रिफाइन (Filter) करना
    if selected_year != "सभी (All)":
        filtered_data = data[data['year'] == int(selected_year)].copy()
        st.success(f"✅ सफलता! वर्ष {selected_year} के लिए {len(filtered_data)} दिनों का डेटा लोड हुआ है।")
    else:
        filtered_data = data.copy()
        st.success(f"✅ सफलता! कुल {len(filtered_data)} दिनों का डेटा लोड हो चुका है।")

    # बैकटेस्ट लॉजिक
    if st.button("🚀 असली डेटा पर बैकटेस्ट रन करें"):
        st.info("डेटा का विश्लेषण चल रहा है...")
        
        # सुनिश्चित करना कि डेटा पूरी तरह से नंबर फॉर्मैट में ही है
        filtered_data['close'] = pd.to_numeric(filtered_data['close'], errors='coerce')
        filtered_data['sma'] = filtered_data['close'].rolling(window=sma_period).mean()
        
        current_capital = initial_capital
        capital_curve = [initial_capital]
        wins = 0
        losses = 0
        position = 0 
        entry_price = 0
        
        for i in range(1, len(filtered_data)):
            if pd.isna(filtered_data['sma'].iloc[i]) or pd.isna(filtered_data['sma'].iloc[i-1]):
                continue
                
            # Buy signal (Price crosses above SMA)
            if filtered_data['close'].iloc[i] > filtered_data['sma'].iloc[i] and filtered_data['close'].iloc[i-1] <= filtered_data['sma'].iloc[i-1] and position == 0:
                position = 1
                entry_price = filtered_data['close'].iloc[i]
                
            # Exit signal (Based on User's Risk and Reward inputs)
            elif position == 1:
                current_price = filtered_data['close'].iloc[i]
                risk_amount = current_capital * (risk_per_trade_pct / 100)
                
                # Take Profit (Reward)
                if current_price >= entry_price * (1 + (risk_per_trade_pct * risk_reward_ratio / 100)):
                    current_capital += risk_amount * risk_reward_ratio
                    wins += 1
                    position = 0
                    capital_curve.append(current_capital)
                # Stop Loss (Risk)
                elif current_price <= entry_price * (1 - (risk_per_trade_pct / 100)):
                    current_capital -= risk_amount
                    losses += 1
                    position = 0
                    capital_curve.append(current_capital)
        
        # नतीजे दिखाना
        total_trades = wins + losses
        if total_trades > 0:
            net_profit = current_capital - initial_capital
            roi = (net_profit / initial_capital) * 100
            win_rate = (wins / total_trades) * 100
            
            col1, col2, col3 = st.columns(3)
            col1.metric("कुल ट्रेड्स", f"{total_trades}")
            col2.metric("विन रेट", f"{win_rate:.2f}%")
            col3.metric("शुद्ध मुनाफ़ा", f"₹{net_profit:,.2f}", f"{roi:.2f}% ROI")
            
            st.subheader("📉 आपका इक्विटी कर्व (Equity Curve)")
            st.line_chart(pd.DataFrame(capital_curve, columns=["Capital (INR)"]))
        else:
            st.warning("इस टाइमफ्रेम और पैरामीटर्स पर कोई ट्रेड नहीं मिला। कृपया पैरामीटर्स बदलें।")
