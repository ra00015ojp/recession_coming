import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(page_title="Yield Curve Monitor", page_icon="📊", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .big-metric {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .inverted {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .normal {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        margin: 20px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 15px;
        border-radius: 5px;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title with emoji
st.title("📊 U.S. Yield Curve Monitor")
st.markdown("### Real-time recession indicator based on Treasury yield spreads")

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **What is Yield Curve Inversion?**
    
    When the 2-year Treasury yield exceeds the 10-year yield, 
    it signals that investors expect economic trouble ahead.
    
    **Historical Accuracy:**
    - Predicted 7 of the last 9 recessions
    - Typically leads recession by 6-24 months
    
    **Current Thresholds:**
    - 🟢 Normal: Spread > 0%
    - 🟡 Flattening: 0% to -0.2%
    - 🔴 Inverted: < -0.2%
    """)
    
    st.markdown("---")
    st.markdown("**Data Source:** Federal Reserve Economic Data (FRED)")

def fetch_fred_data(series_id, start_date, end_date, api_key=None):
    """Fetch data from FRED API"""
    url = "https://api.stlouisfed.org/fred/series/observations"
    
    # Use demo API key or allow user to input their own
    if api_key is None:
        api_key = st.secrets.get("fred_api_key", "d0d2c8e46964b4dd9fafc65fe9141aa8")
    
    params = {
        'series_id': series_id,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date
    }
    
    if api_key:
        params['api_key'] = api_key
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'observations' in data:
            df = pd.DataFrame(data['observations'])
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df[['date', 'value']].set_index('date')
            return df
        else:
            return None
    except Exception as e:
        return None

# API Key input
api_key_input = st.text_input(
    "🔑 Enter your FRED API Key (get free key at https://fred.stlouisfed.org/docs/api/api_key.html)",
    type="password",
    help="Required for data access. Free registration at FRED."
)

if not api_key_input:
    st.warning("⚠️ Please enter a FRED API key to fetch data. Get your free key here: https://fred.stlouisfed.org/docs/api/api_key.html")
    st.stop()

# Define date range
end = datetime.date.today()
start = end - datetime.timedelta(days=365)  # Get 1 year of data

start_str = start.strftime('%Y-%m-%d')
end_str = end.strftime('%Y-%m-%d')

# Fetch data
with st.spinner("📡 Fetching latest Treasury yield data..."):
    dgs10 = fetch_fred_data('DGS10', start_str, end_str, api_key_input)
    dgs2 = fetch_fred_data('DGS2', start_str, end_str, api_key_input)

if dgs10 is None or dgs2 is None:
    st.error("❌ Unable to fetch data from FRED. Please check your API key and try again.")
    st.stop()

# Combine data
df = pd.concat([dgs10.rename(columns={'value': 'DGS10'}), 
               dgs2.rename(columns={'value': 'DGS2'})], axis=1)
df = df.dropna()

if df.empty:
    st.error("No data available. Please try again later.")
    st.stop()

# Calculate spread
df['Spread'] = df['DGS10'] - df['DGS2']

# Latest values
ten_year = df['DGS10'].iloc[-1]
two_year = df['DGS2'].iloc[-1]
latest_date = df.index[-1]
spread = ten_year - two_year

# Determine status
if spread < -0.2:
    status = "🔴 Inverted"
    status_class = "inverted"
    message = "Strong recession signal. Historical precedent suggests elevated recession risk."
elif spread < 0:
    status = "🟡 Flattening"
    status_class = "normal"
    message = "Yield curve is flattening. Monitor for further inversion."
else:
    status = "🟢 Normal"
    status_class = "normal"
    message = "Healthy yield curve. No immediate recession signal."

# Display metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="10-Year Treasury Yield",
        value=f"{ten_year:.2f}%",
        delta=f"{df['DGS10'].iloc[-1] - df['DGS10'].iloc[-5]:.2f}% (5-day)"
    )

with col2:
    st.metric(
        label="2-Year Treasury Yield",
        value=f"{two_year:.2f}%",
        delta=f"{df['DGS2'].iloc[-1] - df['DGS2'].iloc[-5]:.2f}% (5-day)"
    )

with col3:
    st.metric(
        label="10-2 Year Spread",
        value=f"{spread:.2f}%",
        delta=f"{df['Spread'].iloc[-1] - df['Spread'].iloc[-5]:.2f}% (5-day)"
    )

# Big status display
st.markdown(f"""
    <div class="big-metric {status_class}">
        {status}
    </div>
""", unsafe_allow_html=True)

st.markdown(f"**As of:** {latest_date.strftime('%B %d, %Y')}")
st.markdown(f"**Analysis:** {message}")

# Create interactive chart
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=('Treasury Yields (Past Year)', 'Yield Spread (10Y - 2Y)'),
    vertical_spacing=0.12,
    row_heights=[0.5, 0.5]
)

# Yields chart
fig.add_trace(
    go.Scatter(x=df.index, y=df['DGS10'], name='10-Year',
               line=dict(color='#667eea', width=2)),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(x=df.index, y=df['DGS2'], name='2-Year',
               line=dict(color='#f5576c', width=2)),
    row=1, col=1
)

# Spread chart with colored zones
fig.add_trace(
    go.Scatter(x=df.index, y=df['Spread'], name='Spread',
               line=dict(color='#764ba2', width=3),
               fill='tozeroy',
               fillcolor='rgba(118, 75, 162, 0.2)'),
    row=2, col=1
)

# Add zero line
fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

# Update layout
fig.update_xaxes(title_text="Date", row=2, col=1)
fig.update_yaxes(title_text="Yield (%)", row=1, col=1)
fig.update_yaxes(title_text="Spread (%)", row=2, col=1)

fig.update_layout(
    height=700,
    showlegend=True,
    hovermode='x unified',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, use_container_width=True)

# Statistics
st.markdown("---")
st.subheader("📈 Historical Statistics (Past Year)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**10-Year Treasury**")
    st.write(f"Current: {ten_year:.2f}%")
    st.write(f"Average: {df['DGS10'].mean():.2f}%")
    st.write(f"Range: {df['DGS10'].min():.2f}% - {df['DGS10'].max():.2f}%")

with col2:
    st.markdown("**2-Year Treasury**")
    st.write(f"Current: {two_year:.2f}%")
    st.write(f"Average: {df['DGS2'].mean():.2f}%")
    st.write(f"Range: {df['DGS2'].min():.2f}% - {df['DGS2'].max():.2f}%")

# Inversion days count
inversion_days = len(df[df['Spread'] < 0])
total_days = len(df)
inversion_pct = (inversion_days / total_days) * 100

st.markdown(f"""
    <div class="info-box">
        <strong>Inversion History:</strong> The yield curve has been inverted for 
        <strong>{inversion_days}</strong> out of <strong>{total_days}</strong> trading days 
        in the past year (<strong>{inversion_pct:.1f}%</strong> of the time).
    </div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("⚠️ Disclaimer: This tool is for informational purposes only and should not be considered financial advice. Past performance does not guarantee future results.")
