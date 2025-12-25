import streamlit as st
import pandas_datareader.data as web
import datetime
import pandas as pd

st.title("Yield Curve Inversion Checker")
st.markdown("This app checks the U.S. Treasury 10-2 yield spread to assess recession risks. A negative spread indicates inversion.")

# Define date range
end = datetime.date.today()
start = end - datetime.timedelta(days=60)  # Extend to ensure data

# Fetch data
try:
    df = web.DataReader(['DGS10', 'DGS2'], 'fred', start, end)
    df = df.dropna()  # Drop NaN rows

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
except Exception as e:
    st.error(f"Error fetching data: {e}")
