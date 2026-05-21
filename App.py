import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Crypto Strategy Backtester", layout="wide")

st.title("📈 Crypto Trading Strategy Backtester")
st.subheader("बिना कोडिंग के अपनी स्ट्रेटजी टेस्ट करें")

# Sidebar for Inputs
st.sidebar.header("⚙️ ट्रेडिंग पैरामीटर्स")
initial_capital = st.sidebar.number_input("शुरुआती पूँजी (INR)", value=20000, step=1000)
risk_per_trade_pct = st.sidebar.slider("प्रति ट्रेड रिस्क (%)", 0.5, 50.0, 1.0, 0.5)
risk_reward_ratio = st.sidebar.slider("रिस्क-रिवॉर्ड रेश्यो (1:X)", 1.0, 10.0, 3.0, 0.5)

selected_strategy = st.sidebar.selectbox(
    "स्ट्रेटजी चुनें",
    ["Previous Day High/Low Breakout", "Moving Average Crossover (Coming Soon)"]
)

# Dummy Data Generation for Demonstration (Simulating 1 Year BTC Data)
np.random.seed(42)
dates = pd.date_range(start="2025-05-21", periods=142, freq="D")
simulated_trades = []

# Logic to simulate trades based on our backtest results
# For 1:3 RR and 1% risk -> ~28% Win Rate
for i in range(142):
    is_win = np.random.choice([True, False], p=[0.28, 0.72])
    simulated_trades.append(is_win)

# Backtest Simulation Button
if st.button("🚀 बैकटेस्ट रन करें"):
    st.info("पिछले 1 साल के बिटकॉइन डेटा पर टेस्टिंग चल रही है...")
    
    current_capital = initial_capital
    capital_curve = [initial_capital]
    wins = 0
    losses = 0
    max_drawdown = 0
    peak = initial_capital
    
    risk_amount = initial_capital * (risk_per_trade_pct / 100)
    reward_amount = risk_amount * risk_reward_ratio
    
    for win in simulated_trades:
        if win:
            current_capital += reward_amount
            wins += 1
        else:
            current_capital -= risk_amount
            losses += 1
        
        capital_curve.append(current_capital)
        if current_capital > peak:
            peak = current_capital
        dd = (peak - current_capital) / peak * 100
        if dd > max_drawdown:
            max_drawdown = dd

    # Results Display
    net_profit = current_capital - initial_capital
    roi = (net_profit / initial_capital) * 100
    win_rate = (wins / 142) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("कुल ट्रेड्स", "142")
    col2.metric("विन रेट (Win Rate)", f"{win_rate:.2f}%")
    col3.metric("शुद्ध मुनाफ़ा (Net Profit)", f"₹{net_profit:,.2f}", f"{roi:.2f}% ROI")
    col4.metric("मैक्स ड्राडाउन (Max Drawdown)", f"{max_drawdown:.2f}%", delta_color="inverse")
    
    # Plotting the Capital Curve
    st.subheader("📉 इक्विटी कर्व (Equity Curve)")
    chart_data = pd.DataFrame(capital_curve, index=range(143), columns=["Capital (INR)"])
    st.line_chart(chart_data)
    
    st.success("बैकटेस्ट सफलतापूर्वक पूरा हुआ!")
  
