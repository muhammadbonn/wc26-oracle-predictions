import pandas as pd

def get_team_flag(team_name):
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

def calculate_score(pred_outcome, predict_goals, pred_home, pred_away, actual_home, actual_away):
    if pd.isna(actual_home) or pd.isna(actual_away): return 0, False
    
    act_h, act_a = int(actual_home), int(actual_away)
    actual_outcome = "home" if act_h > act_a else "away" if act_a > act_h else "draw"
    
    points = 0
    outcome_correct = (pred_outcome == actual_outcome)
    if outcome_correct: points += 3
    
    if predict_goals:
        h_corr, a_corr = (pred_home == act_h), (pred_away == act_a)
        if h_corr and a_corr: points += 5
        else: points += (2 if h_corr else -1) + (2 if a_corr else -1)
    return points, outcome_correct

def get_match_round(match_id):
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
