import pandas as pd

def get_team_flag(team_name):
    """Returns the flag image URL for a given team name."""
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
    return f"https://flagcdn.com/w80/{code}.png" if code else None

def get_match_round(match_id):
    """Categorizes matches into their specific tournament stages."""
    try:
        m_id = int(match_id)
        if 1 <= m_id <= 24: return "Matchday 1"
        if 25 <= m_id <= 48: return "Matchday 2"
        if 49 <= m_id <= 72: return "Matchday 3"
        if 73 <= m_id <= 88: return "Round of 32"
        if 89 <= m_id <= 96: return "Round of 16"
        if 97 <= m_id <= 100: return "Quarter-Finals"
        if 101 <= m_id <= 102: return "Semi-Finals"
        if m_id == 103: return "Third Place"
        if m_id == 104: return "Final"
        return "Knockouts"
    except:
        return "Other Matches"

def calculate_score(pred_outcome, predict_goals, pred_home, pred_away, 
                    pred_pens, pred_hp, pred_ap, 
                    actual_home, actual_away, act_pens, act_hp, act_ap, is_knockout):
    """
    Calculates points based on the new Tournament Rules:
    - Base: +3 for correct winner.
    - Advanced: +2 per correct goal, -1 per incorrect, +5 bonus for perfect score.
    - Knockout: +2 bonus for predicting penalties, -1 penalty for false pen prediction,
      +1 for smart consolation, +3/-1 for penalty shootout scores.
    """
    if pd.isna(actual_home) or pd.isna(actual_away): return 0
    
    points = 0
    act_h, act_a = int(actual_home), int(actual_away)
    actual_outcome = "home" if act_h > act_a else "away" if act_a > act_h else "draw"
    
    # 1. Base Outcome Prediction
    if pred_outcome == actual_outcome:
        points += 3
        # Penalty Shootout Bonus
        if is_knockout and pred_pens and act_pens:
            points += 2
    else:
        # Smart Prediction (Consolation)
        if is_knockout and pred_pens and act_pens:
            points += 1
            
    # Penalty False Prediction Penalty
    if is_knockout and pred_pens and not act_pens:
        points -= 1

    # 2. Advanced Score Prediction
    if predict_goals:
        h_corr, a_corr = (pred_home == act_h), (pred_away == act_a)
        if h_corr and a_corr:
            points += 5 # Perfect score bonus
        else:
            points += (2 if h_corr else -1) + (2 if a_corr else -1)
            
    # 3. Master of Penalties (Shootout Score)
    if is_knockout and act_pens:
        points += (3 if pred_hp == act_hp else -1)
        points += (3 if pred_ap == act_ap else -1)
        
    return points
