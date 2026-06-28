import streamlit as st
import pandas as pd
from scripts.utils import get_match_round

@st.cache_data(ttl=600)
def load_matches():
    try:
        # Load both files
        df_matches = pd.read_csv("data/wc26_matches.csv")
        df_knockouts = pd.read_csv("data/wc26_knockouts.csv")
        
        # Merge them
        full_df = pd.concat([df_matches, df_knockouts], ignore_index=True)
        
        # Ensure match_time is datetime
        full_df['match_time'] = pd.to_datetime(full_df['match_time'])
        
        if 'round_name' not in full_df.columns:
            full_df['round_name'] = full_df['match_id'].apply(get_match_round)
        
        # Fill any missing values in round_name
        full_df['round_name'] = full_df['round_name'].fillna("Other Matches")
        
        return full_df
    except Exception as e:
        st.error(f"Error loading matches: {e}")
        return pd.DataFrame()
