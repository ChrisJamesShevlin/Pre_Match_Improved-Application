import tkinter as tk
from tkinter import ttk
from math import exp, factorial

def poisson_probability(mean, k):
    return (exp(-mean) * (mean ** k)) / factorial(k)

def zero_inflated_poisson_probability(lam, k, p_zero=0.06):
    if k == 0:
        return p_zero + (1 - p_zero) * exp(-lam)
    return (1 - p_zero) * ((lam ** k) * exp(-lam)) / factorial(k)

def calculate_fair_odds():
    try:
        # Inputs
        avg_goals_home_scored = float(entries["avg_goals_home_scored"].get())
        avg_goals_away_conceded = float(entries["avg_goals_away_conceded"].get())
        avg_goals_away_scored = float(entries["avg_goals_away_scored"].get())
        avg_goals_home_conceded = float(entries["avg_goals_home_conceded"].get())
        avg_xg_home = float(entries["avg_xg_home"].get())
        avg_xg_away = float(entries["avg_xg_away"].get())
        injuries_home = int(entries["injuries_home"].get())
        injuries_away = int(entries["injuries_away"].get())
        position_home = int(entries["position_home"].get())
        position_away = int(entries["position_away"].get())
        form_home = int(entries["form_home"].get())
        form_away = int(entries["form_away"].get())
        bookmaker_odds_home = float(entries["bookmaker_odds_home"].get())
        bookmaker_odds_away = float(entries["bookmaker_odds_away"].get())
        bookmaker_odds_draw = float(entries["bookmaker_odds_draw"].get())

        # Expected Goals Calculation with xG Factor
        lambda_home = (((avg_goals_home_scored + avg_goals_away_conceded) / 2) + avg_xg_home) * (1 - 0.05 * injuries_home) + form_home * 0.1 - position_home * 0.02
        lambda_away = (((avg_goals_away_scored + avg_goals_home_conceded) / 2) + avg_xg_away) * (1 - 0.05 * injuries_away) + form_away * 0.1 - position_away * 0.02
        
        # Goal probabilities
        goal_range = 10
        home_goal_probs = [zero_inflated_poisson_probability(lambda_home, i) for i in range(goal_range)]
        away_goal_probs = [zero_inflated_poisson_probability(lambda_away, i) for i in range(goal_range)]
        
        draw_prob = sum(home_goal_probs[i] * away_goal_probs[i] for i in range(goal_range))
        home_win_prob = sum(sum(home_goal_probs[i] * away_goal_probs[j] for j in range(i)) for i in range(goal_range))
        away_win_prob = sum(sum(home_goal_probs[j] * away_goal_probs[i] for j in range(i)) for i in range(goal_range))
        
        # Normalize probabilities
        total_prob = home_win_prob + away_win_prob + draw_prob
        home_win_prob /= total_prob
        away_win_prob /= total_prob
        draw_prob /= total_prob
        
        # Fair odds calculation
        fair_home_odds = 1 / home_win_prob
        fair_away_odds = 1 / away_win_prob
        fair_draw_odds = 1 / draw_prob
        
        # Edge calculation
        edge_home = (home_win_prob - (1 / bookmaker_odds_home)) / (1 / bookmaker_odds_home)
        edge_away = (away_win_prob - (1 / bookmaker_odds_away)) / (1 / bookmaker_odds_away)
        edge_draw = (draw_prob - (1 / bookmaker_odds_draw)) / (1 / bookmaker_odds_draw)
        
        # Best lay bet selection
        layable_edges = {"Home": edge_home, "Away": edge_away, "Draw": edge_draw}
        best_lay = min(layable_edges, key=layable_edges.get)
        best_edge = layable_edges[best_lay]
        
        # Display results
        result_label["text"] = (f"Fair Odds:\nHome: {fair_home_odds:.2f} | Away: {fair_away_odds:.2f} | Draw: {fair_draw_odds:.2f}\n"
                                f"Edges:\nHome: {edge_home:.4f} | Away: {edge_away:.4f} | Draw: {edge_draw:.4f}\n"
                                f"Best Lay Bet: {best_lay} with Edge: {best_edge:.4f}")
    except ValueError:
        result_label["text"] = "Invalid input, please enter numerical values."

# UI Setup
root = tk.Tk()
root.title("Pre-Match Football Betting Model")

entries = {}
labels_text = [
    "Avg Goals Home Scored", "Avg Goals Away Conceded", "Avg Goals Away Scored", "Avg Goals Home Conceded",
    "Avg xG Home", "Avg xG Away", "Injuries Home", "Injuries Away", "Position Home", "Position Away", "Form Home", "Form Away",
    "Bookmaker Odds Home", "Bookmaker Odds Away", "Bookmaker Odds Draw"
]

for i, label_text in enumerate(labels_text):
    label = tk.Label(root, text=label_text)
    label.grid(row=i, column=0, padx=5, pady=5, sticky="e")
    entry_key = label_text.lower().replace(" ", "_").replace(".", "_")
    entries[entry_key] = tk.Entry(root)
    entries[entry_key].grid(row=i, column=1, padx=5, pady=5)

# Buttons
result_label = tk.Label(root, text="", justify="left")
result_label.grid(row=len(labels_text), column=0, columnspan=2, padx=5, pady=5)

tk.Button(root, text="Calculate Fair Odds", command=calculate_fair_odds).grid(row=len(labels_text) + 1, column=0, columnspan=2, padx=5, pady=10)

tk.Button(root, text="Reset Fields", command=lambda: [entry.delete(0, tk.END) for entry in entries.values()]).grid(row=len(labels_text) + 2, column=0, columnspan=2, padx=5, pady=10)

root.mainloop()
