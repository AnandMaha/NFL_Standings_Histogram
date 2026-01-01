import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import numpy as np

class NFLStandingsHistogram:
    def __init__(self, csv_file):
        # Load the CSV data
        self.df = pd.read_csv(csv_file)
        
        # Clean the team names (remove leading/trailing spaces)
        self.df['NFL Team'] = self.df['NFL Team'].str.strip()
        
        # Extract unique years for the dropdown
        self.years = sorted(self.df['Year'].unique())
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("NFL Standings Histogram")
        self.root.geometry("1600x1000")  # Increased height
        
        # Make the program terminate when window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create dropdown for year selection
        self.year_var = tk.StringVar()
        self.year_var.set(str(self.years[0]))
        
        # Create frame for controls
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        tk.Label(control_frame, text="Select Year:").pack(side=tk.LEFT, padx=(20, 10))
        self.year_dropdown = ttk.Combobox(control_frame, textvariable=self.year_var, 
                                         values=[str(year) for year in self.years],
                                         state="readonly", width=10)
        self.year_dropdown.pack(side=tk.LEFT)
        self.year_dropdown.bind("<<ComboboxSelected>>", self.update_histogram)
        
        # Create frame for the plot
        self.plot_frame = tk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Initialize figure and canvas
        self.fig, self.ax = plt.subplots(figsize=(16, 10))  # Increased height
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create initial histogram
        self.update_histogram()
        
        # Start the GUI loop
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing - terminate the program"""
        self.root.quit()
        self.root.destroy()
        plt.close('all')
    
    def get_win_loss_record(self, row):
        """Extract win-loss-tie record from a row"""
        w = int(row['W'])
        l = int(row['L'])
        t = int(row['T'])
        
        if t == 0:
            return f"{w}-{l}"
        else:
            return f"{w}-{l}-{t}"
    
    def calculate_total_games(self, row):
        """Calculate total games played by a team"""
        return int(row['W']) + int(row['L']) + int(row['T'])
    
    def generate_all_possible_records(self, total_games):
        """Generate all possible win-loss-tie combinations in order from 0-X to X-0"""
        records = []
        
        # Generate in order: from 0 wins to total_games wins
        for w in range(total_games + 1):
            for l in range(total_games - w + 1):
                t = total_games - w - l
                if t == 0:
                    records.append(f"{w}-{l}")
                else:
                    records.append(f"{w}-{l}-{t}")
        
        return records
    
    def sort_records_worst_to_best(self, records_dict):
        """Sort records from worst to best based on wins"""
        # Convert to list of tuples (record, count)
        records_list = list(records_dict.items())
        
        # Sort by wins (ascending) then by losses (descending) for same wins
        def record_sort_key(item):
            record = item[0]
            # Parse the record
            if '-' in record:
                parts = record.split('-')
                if len(parts) == 2:  # w-l
                    w = int(parts[0])
                    l = int(parts[1])
                    t = 0
                else:  # w-l-t
                    w = int(parts[0])
                    l = int(parts[1])
                    t = int(parts[2])
                # Sort by wins (ascending), then losses (descending), then ties (ascending)
                return (w, -l, t)
            return (0, 0, 0)
        
        # Sort from worst to best
        sorted_records = sorted(records_list, key=record_sort_key)
        return sorted_records
    
    def update_histogram(self, event=None):
        """Update the histogram based on selected year"""
        # Clear the previous plot
        self.ax.clear()
        
        # Get selected year
        selected_year = int(self.year_var.get())
        
        # Filter data for selected year
        year_data = self.df[self.df['Year'] == selected_year].copy()
        
        if len(year_data) == 0:
            self.ax.text(0.5, 0.5, f"No data available for {selected_year}", 
                        ha='center', va='center', transform=self.ax.transAxes, fontsize=16)
            self.canvas.draw()
            return
        
        # Calculate total games
        first_team_games = self.calculate_total_games(year_data.iloc[0])
        
        # Get all possible records for this number of games IN ORDER
        all_records = self.generate_all_possible_records(first_team_games)
        
        # Get actual records for all teams
        year_data['Record'] = year_data.apply(self.get_win_loss_record, axis=1)
        record_counts = year_data['Record'].value_counts()
        
        # Sort records from worst to best for the right-side list
        sorted_records = self.sort_records_worst_to_best(record_counts.to_dict())
        
        # Create data for histogram - include ALL possible records in order
        records_list = all_records
        counts_list = [record_counts.get(record, 0) for record in all_records]
        
        # Create the histogram
        x_pos = np.arange(len(records_list))
        
        # Calculate bar width
        if len(records_list) <= 20:
            bar_width = 0.7
        elif len(records_list) <= 40:
            bar_width = 0.6
        elif len(records_list) <= 60:
            bar_width = 0.5
        else:
            bar_width = 0.4
        
        # Color bars: blue for records with teams, light gray for records with 0 teams
        colors = []
        for count in counts_list:
            if count > 0:
                colors.append('steelblue')
            else:
                colors.append('lightgray')
        
        # Create ALL bars including empty ones
        bars = self.ax.bar(x_pos, counts_list, width=bar_width,
                          color=colors, edgecolor='black', alpha=0.8)
        
        # Set x-ticks at the position of each bar
        self.ax.set_xticks(x_pos)
        
        # Create x-axis labels: only show records with teams > 0
        tick_labels = []
        for record, count in zip(records_list, counts_list):
            if count > 0:
                # Two-line label for records with teams
                team_word = "team" if count == 1 else "teams"
                tick_labels.append(f"{record}\n{count} {team_word}")
            else:
                # Empty label for records with 0 teams
                tick_labels.append("")
        
        # Apply labels with 45-degree angle (bottom-left to top-right)
        num_records = len(records_list)
        rotation = 45  # 45 degrees as requested
        
        # Adjust font size based on number of records
        if num_records <= 30:
            font_size = 10
        elif num_records <= 60:
            font_size = 9
        else:
            font_size = 8
        
        # Use right alignment for 45-degree labels
        ha = 'right'
        va = 'top'
        
        # Set the tick labels with 45-degree rotation
        self.ax.set_xticklabels(tick_labels, rotation=rotation, fontsize=font_size, 
                               ha=ha, va=va)
        
        # Set y-axis to show integer values only
        max_count = max(counts_list) if counts_list else 1
        self.ax.set_ylim(0, max_count + 0.5)
        self.ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        # Add horizontal grid
        self.ax.grid(True, axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Add light vertical grid lines at each x-tick
        for x in x_pos:
            self.ax.axvline(x=x, color='lightgray', linestyle=':', alpha=0.2, linewidth=0.5)
        
        # Adjust x-axis limits to add padding
        padding = bar_width * 1.3
        self.ax.set_xlim(x_pos[0] - padding, x_pos[-1] + padding)
        
        # Add axis labels and title with increased labelpad for xlabel
        self.ax.set_xlabel(f'Win-Loss-Tie Records ({first_team_games} games)', 
                          fontsize=12, fontweight='bold', labelpad=20)  # Increased labelpad
        self.ax.set_ylabel('Number of Teams', fontsize=12, fontweight='bold')
        self.ax.set_title(f'NFL Standings Distribution - {selected_year} Season', 
                         fontsize=18, fontweight='bold', pad=25)
        
        # Add a subtle background color
        self.ax.set_facecolor('#f8f9fa')
        
        # Adjust subplot parameters - increased bottom margin for 45-degree labels
        # and to make room for right-side list
        bottom_margin = 0.25 if num_records <= 30 else 0.3
        if num_records > 60:
            bottom_margin = 0.35
        elif num_records > 100:
            bottom_margin = 0.4
        
        self.fig.subplots_adjust(left=0.08, right=0.70, top=0.92, bottom=bottom_margin)
        
        # Create right-side list of records from worst to best
        if sorted_records:
            # Create text for the list
            list_text = "Records (worst to best):\n"
            for record, count in sorted_records:
                team_word = "team" if count == 1 else "teams"
                list_text += f"{record}; {count} {team_word}\n"
            
            # Add the list to the right of the plot
            self.ax.text(1.05, 0.95, list_text, transform=self.ax.transAxes,
                        fontsize=10, va='top', ha='left',
                        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", 
                                 edgecolor="gray", alpha=0.9),
                        fontfamily='monospace')
        
        # Add summary at the bottom - position it lower to account for 45-degree labels
        total_teams = len(year_data)
        nonzero_records = sum(1 for count in counts_list if count > 0)
        
        # Find most common record(s)
        if not record_counts.empty:
            max_count_val = record_counts.max()
            most_common_records = record_counts[record_counts == max_count_val].index.tolist()
            most_common_text = ', '.join(most_common_records[:3])
            if len(most_common_records) > 3:
                most_common_text += f" (+{len(most_common_records)-3} more)"
            most_common_stats = f"Most Common: {most_common_text} ({max_count_val} teams)"
        else:
            most_common_stats = ""
        
        summary_text = f"Total Teams: {total_teams} | Records with teams: {nonzero_records}/{len(records_list)}"
        if most_common_stats:
            summary_text += f" | {most_common_stats}"
        
        # Position summary lower to account for 45-degree labels
        summary_y_position = -0.25 if num_records <= 60 else -0.3
        if num_records > 100:
            summary_y_position = -0.35
        
        self.ax.text(0.02, summary_y_position, summary_text,
                    transform=self.ax.transAxes, fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        
        # Update the canvas
        self.canvas.draw()

# Main execution
if __name__ == "__main__":
    # Replace with your actual CSV file path
    csv_file = "C:/Users/Anand/Programming/PersonalProjects/NFL_Standings/nfl_standings.csv"
    
    # Create and run the application
    app = NFLStandingsHistogram(csv_file)