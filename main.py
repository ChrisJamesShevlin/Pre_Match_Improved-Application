import tkinter as tk
import math

def zip_probability(lam, k, p_zero=0.0):
    """
    Zero-inflated Poisson probability.
    p_zero is set to 0.0 to remove extra weighting for 0 goals.
    """
    if k == 0:
        return p_zero + (1 - p_zero) * math.exp(-lam)
    return (1 - p_zero) * ((lam ** k) * math.exp(-lam)) / math.factorial(k)

def fair_odds(prob):
    return (1/prob) if prob > 0 else float('inf')

def dynamic_kelly(edge):
    # Read Kelly fraction from the new user input (as a percentage)
    try:
        multiplier = float(entries["entry_kelly_fraction"].get()) / 100.0
    except ValueError:
        multiplier = 0.125  # default to 12.5%
    # If nothing valid is entered, default to 0.125 (12.5%)
    if multiplier <= 0:
        multiplier = 0.125
    return max(0, multiplier * edge)

def calculate_insights():
    try:
        # --- 1) Retrieve all inputs ---
        avg_goals_home_scored   = float(entries["entry_home_scored"].get())
        avg_goals_home_conceded = float(entries["entry_home_conceded"].get())
        avg_goals_away_scored   = float(entries["entry_away_scored"].get())
        avg_goals_away_conceded = float(entries["entry_away_conceded"].get())
        
        injuries_home           = int(entries["entry_injuries_home"].get())
        injuries_away           = int(entries["entry_injuries_away"].get())
        position_home           = int(entries["entry_position_home"].get())
        position_away           = int(entries["entry_position_away"].get())
        form_home               = int(entries["entry_form_home"].get())
        form_away               = int(entries["entry_form_away"].get())
        
        home_xg_scored   = float(entries["entry_home_xg_scored"].get())
        away_xg_scored   = float(entries["entry_away_xg_scored"].get())
        home_xg_conceded = float(entries["entry_home_xg_conceded"].get())
        away_xg_conceded = float(entries["entry_away_xg_conceded"].get())
        
        live_under_odds = float(entries["entry_live_under_odds"].get())
        live_over_odds  = float(entries["entry_live_over_odds"].get())
        live_home_odds  = float(entries["entry_live_home_odds"].get())
        live_draw_odds  = float(entries["entry_live_draw_odds"].get())
        live_away_odds  = float(entries["entry_live_away_odds"].get())
        
        account_balance = float(entries["entry_account_balance"].get())
        
        # New inputs for target correct score lay bet:
        target_score_str = entries["entry_target_scoreline"].get().strip()
        target_score_live_odds = float(entries["entry_target_scoreline_odds"].get())
        
        # --- 2) Calculate adjusted expected goals for each team ---
        adjusted_home_goals = ((avg_goals_home_scored + home_xg_scored +
                                avg_goals_away_conceded + away_xg_conceded) / 4)
        adjusted_home_goals *= (1 - 0.03 * injuries_home)
        adjusted_home_goals += form_home * 0.1 - position_home * 0.01
        
        adjusted_away_goals = ((avg_goals_away_scored + away_xg_scored +
                                avg_goals_home_conceded + home_xg_conceded) / 4)
        adjusted_away_goals *= (1 - 0.03 * injuries_away)
        adjusted_away_goals += form_away * 0.1 - position_away * 0.01
        
        # --- 3) Calculate scoreline probabilities using zero-inflated Poisson ---
        goal_range = 10
        scoreline_probs = {}
        for i in range(goal_range):
            for j in range(goal_range):
                p = zip_probability(adjusted_home_goals, i) * zip_probability(adjusted_away_goals, j)
                scoreline_probs[(i, j)] = p
        
        # --- 4) Top 5 most likely scorelines ---
        sorted_scorelines = sorted(scoreline_probs.items(), key=lambda x: x[1], reverse=True)
        top5 = sorted_scorelines[:5]
        
        # --- 5) Match result probabilities from scorelines ---
        model_home_win = sum(p for (i, j), p in scoreline_probs.items() if i > j)
        model_draw     = sum(p for (i, j), p in scoreline_probs.items() if i == j)
        model_away_win = sum(p for (i, j), p in scoreline_probs.items() if i < j)
        
        # --- 6) Blend match result model probabilities with live odds ---
        live_home_prob = 1 / live_home_odds if live_home_odds > 0 else 0
        live_draw_prob = 1 / live_draw_odds if live_draw_odds > 0 else 0
        live_away_prob = 1 / live_away_odds if live_away_odds > 0 else 0
        sum_live = live_home_prob + live_draw_prob + live_away_prob
        if sum_live > 0:
            live_home_prob /= sum_live
            live_draw_prob /= sum_live
            live_away_prob /= sum_live
        
        blend_factor = 0.3  # 30% live, 70% model
        final_home_win = model_home_win * (1 - blend_factor) + live_home_prob * blend_factor
        final_draw     = model_draw     * (1 - blend_factor) + live_draw_prob * blend_factor
        final_away_win = model_away_win * (1 - blend_factor) + live_away_prob * blend_factor
        sum_final = final_home_win + final_draw + final_away_win
        if sum_final > 0:
            final_home_win /= sum_final
            final_draw     /= sum_final
            final_away_win /= sum_final
        
        # --- 7) Compute fair odds for match result ---
        fair_home_odds = fair_odds(final_home_win)
        fair_draw_odds = fair_odds(final_draw)
        fair_away_odds = fair_odds(final_away_win)
        
        # --- 8) Match Odds Bet Recommendations ---
        def rec_bet(fair_val, live, label):
            if live <= 1:
                return f"{label}: No valid live odds."
            if fair_val > live:
                edge = (fair_val - live) / fair_val
                liability = account_balance * dynamic_kelly(edge)
                liability = min(liability, account_balance * 0.10)
                lay_stake = liability / (live - 1) if (live - 1) > 0 else 0
                return f"Lay {label}: Edge {edge:.2%}, Liab {liability:.2f}, Stake {lay_stake:.2f}"
            elif fair_val < live:
                edge = (live - fair_val) / fair_val
                stake = account_balance * dynamic_kelly(edge)
                stake = min(stake, account_balance * 0.10)
                profit = stake * (live - 1)
                return f"Back {label}: Edge {edge:.2%}, Stake {stake:.2f}, Profit {profit:.2f}"
            else:
                return f"{label}: No edge."
        
        match_rec_home = rec_bet(fair_home_odds, live_home_odds, "Home")
        match_rec_draw = rec_bet(fair_draw_odds, live_draw_odds, "Draw")
        match_rec_away = rec_bet(fair_away_odds, live_away_odds, "Away")
        
        # --- 9) Over/Under 2.5 Goals Calculations & Recommendations ---
        under_prob_model = 0.0
        for i in range(goal_range):
            for j in range(goal_range):
                if (i + j) <= 2:
                    under_prob_model += zip_probability(adjusted_home_goals, i) * zip_probability(adjusted_away_goals, j)
        over_prob_model = 1 - under_prob_model
        
        live_under_prob = 1 / live_under_odds if live_under_odds > 0 else 0
        live_over_prob  = 1 / live_over_odds  if live_over_odds > 0 else 0
        sum_live_ou = live_under_prob + live_over_prob
        if sum_live_ou > 0:
            live_under_prob /= sum_live_ou
            live_over_prob  /= sum_live_ou
        
        final_under_prob = under_prob_model * (1 - blend_factor) + live_under_prob * blend_factor
        final_over_prob  = over_prob_model  * (1 - blend_factor) + live_over_prob  * blend_factor
        sum_final_ou = final_under_prob + final_over_prob
        if sum_final_ou > 0:
            final_under_prob /= sum_final_ou
            final_over_prob  /= sum_final_ou
        
        fair_under_odds = fair_odds(final_under_prob)
        fair_over_odds  = fair_odds(final_over_prob)
        
        ou_rec = ""
        if fair_under_odds > live_under_odds > 1:
            edge = (fair_under_odds - live_under_odds) / fair_under_odds
            liability = account_balance * dynamic_kelly(edge)
            liability = min(liability, account_balance * 0.10)
            lay_stake = liability / (live_under_odds - 1) if (live_under_odds - 1) > 0 else 0
            ou_rec += f"Lay Under: Edge {edge:.2%}, Liab {liability:.2f}, Stake {lay_stake:.2f}\n"
        elif fair_under_odds < live_under_odds:
            edge = (live_under_odds - fair_under_odds) / fair_under_odds
            stake = account_balance * dynamic_kelly(edge)
            stake = min(stake, account_balance * 0.10)
            profit = stake * (live_under_odds - 1)
            ou_rec += f"Back Under: Edge {edge:.2%}, Stake {stake:.2f}, Profit {profit:.2f}\n"
        else:
            ou_rec += "Under: No edge.\n"
            
        if fair_over_odds > live_over_odds > 1:
            edge = (fair_over_odds - live_over_odds) / fair_over_odds
            liability = account_balance * dynamic_kelly(edge)
            liability = min(liability, account_balance * 0.10)
            lay_stake = liability / (live_over_odds - 1) if (live_over_odds - 1) > 0 else 0
            ou_rec += f"Lay Over: Edge {edge:.2%}, Liab {liability:.2f}, Stake {lay_stake:.2f}"
        elif fair_over_odds < live_over_odds:
            edge = (live_over_odds - fair_over_odds) / fair_over_odds
            stake = account_balance * dynamic_kelly(edge)
            stake = min(stake, account_balance * 0.10)
            profit = stake * (live_over_odds - 1)
            ou_rec += f"Back Over: Edge {edge:.2%}, Stake {stake:.2f}, Profit {profit:.2f}"
        else:
            ou_rec += "Over: No edge."
        
        # --- 10) Correct Score Lay Recommendation ---
        correct_score_output = "No target bet."
        if target_score_str and target_score_live_odds > 0:
            try:
                target_score = tuple(map(int, target_score_str.split('-')))
            except:
                target_score = None
            if target_score and target_score in scoreline_probs:
                target_prob = scoreline_probs[target_score]
                fair_target_odds = fair_odds(target_prob)
                out_line = f"Target {target_score[0]}-{target_score[1]}: Prob {target_prob*100:.1f}%, Fair Odds {fair_target_odds:.2f}"
                if fair_target_odds > target_score_live_odds:
                    edge = (fair_target_odds - target_score_live_odds) / fair_target_odds
                    base_liability = account_balance * dynamic_kelly(edge)
                    base_liability = min(base_liability, account_balance * 0.10)
                    lay_stake = base_liability / (target_score_live_odds - 1) if (target_score_live_odds - 1) > 0 else 0
                    out_line += f"\nLay Target: Edge {edge:.2%}, Liab {base_liability:.2f}, Stake {lay_stake:.2f}"
                else:
                    out_line += "\nNo lay edge (fair not > live)."
                correct_score_output = out_line
            else:
                correct_score_output = "Target score not found."
        
        # --- 11) Build final output text ---
        output = "=== Match Insights ===\n\n"
        output += f"Adjusted Expected Goals: Home {adjusted_home_goals:.2f}, Away {adjusted_away_goals:.2f}\n\n"
        output += "Top 5 Likely Scorelines:\n"
        for (score, prob) in top5:
            output += f"{score[0]}-{score[1]}: {prob*100:.1f}% (Odds: {fair_odds(prob):.2f})\n"
        output += "\n"
        output += "Match Result (Blended):\n"
        output += f"Home Win: {final_home_win*100:.1f}% (Fair Odds: {fair_home_odds:.2f})\n"
        output += f"Draw: {final_draw*100:.1f}% (Fair Odds: {fair_draw_odds:.2f})\n"
        output += f"Away Win: {final_away_win*100:.1f}% (Fair Odds: {fair_away_odds:.2f})\n\n"
        output += "Match Odds Recommendations:\n"
        output += match_rec_home + "\n" + match_rec_draw + "\n" + match_rec_away + "\n\n"
        output += "Over/Under 2.5 Goals:\n"
        output += f"Under: {final_under_prob*100:.1f}% (Fair Odds: {fair_under_odds:.2f})\n"
        output += f"Over: {final_over_prob*100:.1f}% (Fair Odds: {fair_over_odds:.2f})\n"
        output += "Over/Under Rec:\n" + ou_rec + "\n\n"
        output += "Correct Score Lay Recommendation:\n" + correct_score_output + "\n"
        
        # --- Insert output line by line with color tags ---
        result_text_widget.delete("1.0", tk.END)
        lines = output.split("\n")
        for line in lines:
            if "Lay " in line:
                result_text_widget.insert(tk.END, line + "\n", "lay")
            elif "Back " in line:
                result_text_widget.insert(tk.END, line + "\n", "back")
            elif line.startswith("---"):
                result_text_widget.insert(tk.END, line + "\n", "insight")
            else:
                result_text_widget.insert(tk.END, line + "\n", "normal")
        
    except ValueError:
        result_text_widget.delete("1.0", tk.END)
        result_text_widget.insert(tk.END, "Please enter valid numerical values.", "normal")

def reset_fields():
    for entry in entries.values():
        entry.delete(0, tk.END)
    result_text_widget.delete("1.0", tk.END)

# --- GUI Layout ---
root = tk.Tk()
root.title("Odds Apex - Prematch Model")

# Define input fields
entries = {
    "entry_home_scored":      tk.Entry(root),
    "entry_home_conceded":    tk.Entry(root),
    "entry_away_scored":      tk.Entry(root),
    "entry_away_conceded":    tk.Entry(root),
    "entry_injuries_home":    tk.Entry(root),
    "entry_injuries_away":    tk.Entry(root),
    "entry_position_home":    tk.Entry(root),
    "entry_position_away":    tk.Entry(root),
    "entry_form_home":        tk.Entry(root),
    "entry_form_away":        tk.Entry(root),
    "entry_home_xg_scored":   tk.Entry(root),
    "entry_away_xg_scored":   tk.Entry(root),
    "entry_home_xg_conceded": tk.Entry(root),
    "entry_away_xg_conceded": tk.Entry(root),
    "entry_live_under_odds":  tk.Entry(root),
    "entry_live_over_odds":   tk.Entry(root),
    "entry_live_home_odds":   tk.Entry(root),
    "entry_live_draw_odds":   tk.Entry(root),
    "entry_live_away_odds":   tk.Entry(root),
    "entry_account_balance":  tk.Entry(root),
    # New inputs for target correct score lay bet:
    "entry_target_scoreline":         tk.Entry(root),
    "entry_target_scoreline_odds":      tk.Entry(root),
    # New input for Kelly staking fraction (as a percentage)
    "entry_kelly_fraction":             tk.Entry(root)
}

labels_text = [
    "Avg Goals Home Scored", "Avg Goals Home Conceded", "Avg Goals Away Scored", "Avg Goals Away Conceded",
    "Injuries Home", "Injuries Away", "Position Home", "Position Away",
    "Form Home", "Form Away", "Home xG Scored", "Away xG Scored",
    "Home xG Conceded", "Away xG Conceded", "Live Under 2.5 Odds", "Live Over 2.5 Odds",
    "Live Home Win Odds", "Live Draw Odds", "Live Away Win Odds", "Account Balance",
    "Target Scoreline (e.g. 1-1)", "Target Scoreline Live Odds",
    "Kelly Staking Fraction (%)"
]

for i, (key, text) in enumerate(zip(entries.keys(), labels_text)):
    label = tk.Label(root, text=text)
    label.grid(row=i, column=0, padx=5, pady=5, sticky="e")
    entries[key].grid(row=i, column=1, padx=5, pady=5)

# Create a frame for the output (with a scrollbar)
result_frame = tk.Frame(root)
result_frame.grid(row=len(entries), column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
root.grid_rowconfigure(len(entries), weight=1)
root.grid_columnconfigure(1, weight=1)

# Increase output widget size: 80 characters wide and 40 lines high
result_text_widget = tk.Text(result_frame, wrap=tk.WORD, background="white", width=80, height=40)
result_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = tk.Scrollbar(result_frame, command=result_text_widget.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
result_text_widget.config(yscrollcommand=scrollbar.set)

calc_button = tk.Button(root, text="Calculate Match Insights", command=calculate_insights)
calc_button.grid(row=len(entries)+1, column=0, columnspan=2, padx=5, pady=10)
reset_button = tk.Button(root, text="Reset All Fields", command=reset_fields)
reset_button.grid(row=len(entries)+2, column=0, columnspan=2, padx=5, pady=10)

# Configure text tags: back bets in blue, lay bets in red, insights in green, normal in black.
result_text_widget.tag_configure("insight", foreground="green")
result_text_widget.tag_configure("lay", foreground="red")
result_text_widget.tag_configure("back", foreground="blue")
result_text_widget.tag_configure("normal", foreground="black")

root.mainloop()
