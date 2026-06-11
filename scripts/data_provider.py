import streamlit as st
import pandas as pd

@st.cache_data(ttl=600)
def load_matches(csv_path="data/wc26_matches.csv"):
    try:
        df = pd.read_csv(csv_path)
        df['match_time'] = pd.to_datetime(df['match_time'])
        return df
    except Exception as e:
        st.error(f"Error loading matches from local data folder: {e}")
        return pd.DataFrame()
