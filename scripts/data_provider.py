import streamlit as st
import pandas as pd

@st.cache_data(ttl=600)
def load_matches():
    try:
        # Load both files from the data folder
        df_matches = pd.read_csv("data/wc26_matches.csv")
        df_knockouts = pd.read_csv("data/wc26_knockouts.csv")
        
        # Merge them into one dataframe
        full_df = pd.concat([df_matches, df_knockouts], ignore_index=True)
        
        # Convert match_time to datetime
        full_df['match_time'] = pd.to_datetime(full_df['match_time'])
        
        # Fill missing round names if any
        full_df['round_name'] = full_df['round_name'].fillna("Other Matches")
        
        return full_df
    except Exception as e:
        st.error(f"Error loading matches: {e}")
        return pd.DataFrame()
