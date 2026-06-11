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

def calculate_score(pred_outcome, predict_goals, pred_home, pred_away, actual_home, actual_away):
    if pd.isna(actual_home) or pd.isna(actual_away):
        return 0
    actual_home, actual_away = int(actual_home), int(actual_away)
    
    # Determine the actual match outcome
    if actual_home > actual_away:
        actual_outcome = "home"
    elif actual_away > actual_home:
        actual_outcome = "away"
    else:
        actual_outcome = "draw"
    
    points = 0
    
    # Base rule: +3 points for correct match outcome prediction
    if pred_outcome == actual_outcome:
        points += 3
        
    # Optional advanced rule: Predict exact goals per team (High Risk / Reward)
    if predict_goals:
        home_correct = (pred_home == actual_home)
        away_correct = (pred_away == actual_away)
        
        if home_correct and away_correct:
            points += 5 # Special bonus instead of 4 points if both are correct
        else:
            points += 2 if home_correct else -1
            points += 2 if away_correct else -1
            
    return points
