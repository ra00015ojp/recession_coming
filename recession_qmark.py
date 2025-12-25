import streamlit as st
import pandas as pd
import datetime
import requests

st.title("Yield Curve Inversion Checker")
st.markdown("This app checks the U.S. Treasury 10-2 yield spread to assess recession risks. A negative spread indicates inversion.")

# Define date range
end = datetime.date.today()
start = end - datetime.timedelta(days=60)

# Format dates for FRED API
start_str = start.strftime('%Y-%m-%d')
end_str = end.strftime('%Y-%m-%d')

def fetch_fred_data(series_id, start_date, end_date):
    """Fetch data from FRED API"""
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        'series_id': series_id,
        'api_key': 'YOUR_API_KEY_HERE',  # Optional - FRED allows some unauthenticated requests
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date
    }
    
    # Try without API key first (FRED allows limited access)
    params_no_key = {k: v for k, v in params.items() if k != 'api_key'}
    
    try:
        response = requests.get(url, params=params_no_key, timeout=10)
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
        st.warning(f"Error fetching {series_id}: {e}")
        return None

# Fetch data
try:
    with st.spinner("Fetching yield data..."):
        dgs10 = fetch_fred_data('DGS10', start_str, end_str)
        dgs2 = fetch_fred_data('DGS2', start_str, end_str)
    
    if dgs10 is None or dgs2 is None:
        st.error("Unable to fetch data from FRED. Please try again later.")
    else:
        # Combine data
        df = pd.concat([dgs10.rename(columns={'value': 'DGS10'}), 
                       dgs2.rename(columns={'value': 'DGS2'})], axis=1)
        df = df.dropna()
        
        if df.empty:
            st.error("No data available in the range. Try later.")
        else:
            ten_year = df['DGS10'].iloc[-1]
            two_year = df['DGS2'].iloc[-1]
            latest_date = df.index[-1]
            spread = ten_year - two_year
            status = "Inverted (Recession Signal)" if spread < 0 else "Normal"
            
            st.subheader("Latest Data")
            st.write(f"**Date:** {latest_date.date()}")
            st.write(f"**10-Year Yield:** {ten_year:.2f}%")
            st.write(f"**2-Year Yield:** {two_year:.2f}%")
            st.write(f"**10-2 Spread:** {spread:.2f}%")
            st.write(f"**Status:** {status}")
            
            # Optional: Show chart
            st.subheader("Yield Spread History (Last 60 Days)")
            df['Spread'] = df['DGS10'] - df['DGS2']
            st.line_chart(df['Spread'])

except Exception as e:
    st.error(f"Error: {e}")
