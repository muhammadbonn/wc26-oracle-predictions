import pandas as pd

def get_team_flag(team_name):
    # Mapping tournament team names to ISO 2-letter country codes for FlagCDN
    team_codes = {
        "Mexico": "mx", "South Africa": "za", "Rep. of Korea": "kr", "Czech Rep.": "cz",
        "Canada": "ca", "Bosnia/Herzeg.": "ba", "USA": "us", "Paraguay": "py",
        "Qatar": "qa", "Switzerland": "ch", "Brazil": "br", "Morocco": "ma",
        "Haiti": "ht", "Scotland": "gb-sct", "Australia": "au", "Turkey": "tr",
        "Germany": "de", "Curaçao": "cw", "Netherlands": "nl", "Japan": "jp",
        "Ivory Coast": "ci", "Ecuador": "ec", "Sweden": "se", "Tunisia": "tn",
        "Spain": "es", "Cape Verde": "cv", "Belgium": "be", "Egypt": "eg",
        "Saudi Arabia": "sa", "Uruguay": "uy", "IR Iran": "ir", "New Zealand": "nz",
        "France": "fr", "Senegal": "sn", "Iraq": "iq", "Norway": "no",
        "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Jordan": "jo",
        "Portugal": "pt", "DR Congo": "cd", "England": "gb-eng", "Croatia": "hr",
        "Ghana": "gh", "Panama": "pa", "Uzbekistan": "uz", "Colombia": "co"
    }
    code = team_codes.get(team_name)
    if code:
        return f"https://flagcdn.com/w80/{code}.png"
    return None

def calculate_score(pred_home, pred_away, actual_home, actual_away):
    if pd.isna(actual_home) or pd.isna(actual_away):
        return 0
    actual_home, actual_away = int(actual_home), int(actual_away)
    
    pred_result = "home" if pred_home > pred_away else "away" if pred_away > pred_home else "draw"
    actual_result = "home" if actual_home > actual_away else "away" if actual_away > actual_home else "draw"
    
    points = 0
    if pred_result == actual_result:
        points += 3 # Points for predicting the correct outcome (win/draw)
        if pred_home == actual_home and pred_away == actual_away:
            points += 5 # Bonus points for predicting the exact score
    return points
