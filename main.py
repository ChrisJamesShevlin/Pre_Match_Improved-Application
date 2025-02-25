import tkinter as tk
from tkinter import ttk
from math import exp, factorial

def poisson_probability(mean, k):
    return (exp(-mean) * (mean ** k)) / factorial(k)

def bivariate_poisson_probability(lambda1, lambda2, k1, k2, rho):
    prob = 0
    for i in range(min(k1, k2) + 1):
        prob += (poisson_probability(lambda1, k1 - i) *
                 poisson_probability(lambda2, k2 - i) *
                 poisson_probability(rho, i))
    return prob

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
        account_balance = float(entries["account_balance"].get())

        # Expected Goals Calculation with xG Factor
        lambda_home = (((avg_goals_home_scored + avg_goals_away_conceded) / 2) + avg_xg_home) * (1 - 0.05 * injuries_home) + form_home * 0.1 - position_home * 0.02
        lambda_away = (((avg_goals_away_scored + avg_goals_home_conceded) / 2) + avg_xg_away) * (1 - 0.05 * injuries_away) + form_away * 0.1 - position_away * 0.02

        # Correlation coefficient for bivariate Poisson
        rho = 0.1  # Assumed correlation, adjust as needed

        # Fair odds calculation using bivariate Poisson
        home_win_prob = sum(bivariate_poisson_probability(lambda_home, lambda_away, k1, k2, rho)
                            for k1 in range(10) for k2 in range(k1))
        away_win_prob = sum(bivariate_poisson_probability(lambda_home, lambda_away, k1, k2, rho)
                            for k2 in range(10) for k1 in range(k2))
        draw_prob = sum(bivariate_poisson_probability(lambda_home, lambda_away, k, k, rho) for k in range(10))

        # Normalize probabilities
        total_prob = home_win_prob + away_win_prob + draw_prob
        home_win_prob /= total_prob
        away_win_prob /= total_prob
        draw_prob /= total_prob

        # Calculate bookmaker implied probabilities
        implied_home_prob = 1 / bookmaker_odds_home
        implied_away_prob = 1 / bookmaker_odds_away
        implied_draw_prob = 1 / bookmaker_odds_draw
        total_implied_prob = implied_home_prob + implied_away_prob + implied_draw_prob
        implied_home_prob /= total_implied_prob
        implied_away_prob /= total_implied_prob
        implied_draw_prob /= total_implied_prob

        # Blend model probabilities with bookmaker implied probabilities
        blend_factor = 0.5  # Adjust this factor as needed (0.5 means equal weight to both model and bookmaker)
        home_win_prob = blend_factor * home_win_prob + (1 - blend_factor) * implied_home_prob
        away_win_prob = blend_factor * away_win_prob + (1 - blend_factor) * implied_away_prob
        draw_prob = blend_factor * draw_prob + (1 - blend_factor) * implied_draw_prob

        # Re-normalize blended probabilities
        total_blended_prob = home_win_prob + away_win_prob + draw_prob
        home_win_prob /= total_blended_prob
        away_win_prob /= total_blended_prob
        draw_prob /= total_blended_prob

        # Calculate fair odds from blended probabilities
        fair_home_odds = 1 / home_win_prob
        fair_away_odds = 1 / away_win_prob
        fair_draw_odds = 1 / draw_prob

        # Edge calculation
        edge_home = (home_win_prob - (1 / bookmaker_odds_home)) / (1 / bookmaker_odds_home)
        edge_away = (away_win_prob - (1 / bookmaker_odds_away)) / (1 / bookmaker_odds_away)
        edge_draw = (draw_prob - (1 / bookmaker_odds_draw)) / (1 / bookmaker_odds_draw)

        # Print debug information in tab-separated format for Excel
        print("Bet\tBookmaker Odds\tFair Odds\tEdge")
        print(f"Home\t{bookmaker_odds_home}\t{fair_home_odds:.2f}\t{edge_home:.4f}")
        print(f"Draw\t{bookmaker_odds_draw}\t{fair_draw_odds:.2f}\t{edge_draw:.4f}")
        print(f"Away\t{bookmaker_odds_away}\t{fair_away_odds:.2f}\t{edge_away:.4f}")

        # Best lay bet selection
        layable_edges = {
            "Home": (edge_home, fair_home_odds, bookmaker_odds_home),
            "Away": (edge_away, fair_away_odds, bookmaker_odds_away),
            "Draw": (edge_draw, fair_draw_odds, bookmaker_odds_draw)
        }
        valid_lay_bets = {k: v for k, v in layable_edges.items() if v[1] > v[2]}  # Only consider lay bets where fair odds > bookmaker odds

        if not valid_lay_bets:
            result_label["text"] = "No valid lay bets available where fair odds are higher than bookmaker odds."
            return

        best_lay = min(valid_lay_bets, key=lambda k: valid_lay_bets[k][0])  # Find the most negative edge
        best_edge, fair_odds, bookmaker_odds = valid_lay_bets[best_lay]

        # Kelly criterion stake calculation
        if bookmaker_odds < 2.0:
            kelly_fraction = 0.18
        elif bookmaker_odds < 8.0:
            kelly_fraction = 0.08
        else:
            kelly_fraction = 0.04

        stake = account_balance * kelly_fraction * abs(best_edge)  # Use absolute value of edge for stake calculation

        # Print recommended lay bet and stake in tab-separated format
        print("\nRecommended Bet\tStake\tOdds")
        print(f"{best_lay}\t£{stake:.2f}\t{bookmaker_odds}")

        # Display results
        result_label["text"] = (f"Fair Odds:\nHome: {fair_home_odds:.2f} | Away: {fair_away_odds:.2f} | Draw: {fair_draw_odds:.2f}\n"
                                f"Edges:\nHome: {edge_home:.4f} | Away: {edge_away:.4f} | Draw: {edge_draw:.4f}\n"
                                f"Best Bet: {best_lay} with Edge: {best_edge:.4f}\n"
                                f"Recommended Stake: £{stake:.2f} on {best_lay}")
    except ValueError:
        result_label["text"] = "Invalid input, please enter numerical values."

# UI Setup
root = tk.Tk()
root.title("Pre-Match Football Betting Model")

entries = {}
labels_text = [
    "Avg Goals Home Scored", "Avg Goals Away Conceded", "Avg Goals Away Scored", "Avg Goals Home Conceded",
    "Avg xG Home", "Avg xG Away", "Injuries Home", "Injuries Away", "Position Home", "Position Away", "Form Home", "Form Away",
    "Bookmaker Odds Home", "Bookmaker Odds Away", "Bookmaker Odds Draw", "Account Balance"
]

for i, label_text in enumerate(labels_text):
    label = tk.Label(root, text=label_text)
    label.grid(row=i, column=0, padx=5, pady=5, sticky="e")
    entry_key = label_text.lower().replace(" ", "_").replace(".", "_")
    entries[entry_key] = tk.Entry(root)
    entries[entry_key].grid(row=i, column=1, padx=5, pady=5)

# Buttons
result_label = tk.Label(root, text="", justify="left")
result_label.grid(row=len(labels_text) + 1, column=0, columnspan=2, padx=5, pady=5)

tk.Button(root, text="Calculate Fair Odds", command=calculate_fair_odds).grid(row=len(labels_text) + 2, column=0, columnspan=2, padx=5, pady=10)

tk.Button(root, text="Reset Fields", command=lambda: [entry.delete(0, tk.END) for entry in entries.values()]).grid(row=len(labels_text) + 3, column=0, columnspan=2, padx=5, pady=10)

root.mainloop()
