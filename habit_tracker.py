import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import datetime
import mysql.connector

# ---------- DATABASE SETUP ----------
def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",        # Change as needed
            password="root"     # Change as needed
        )
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS habit_tracker_db")
        conn.commit()
        conn.close()

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="habit_tracker_db"
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                mon BOOLEAN DEFAULT FALSE,
                tue BOOLEAN DEFAULT FALSE,
                wed BOOLEAN DEFAULT FALSE,
                thu BOOLEAN DEFAULT FALSE,
                fri BOOLEAN DEFAULT FALSE,
                sat BOOLEAN DEFAULT FALSE,
                sun BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error connecting to MySQL: {err}")
        raise SystemExit

# ---------- HABIT TRACKER APP ----------
class HabitTrackerApp:
    def __init__(self, root):
        self.root = root
        root.title("Habit Tracker")
        root.geometry("850x500")
        root.resizable(False, False)

        self.conn = connect_db()
        self.cursor = self.conn.cursor()
        self.habits = self.load_habits_from_db()

        # Left Frame
        left_frame = ttk.Frame(root, padding=(10, 10))
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left_frame, text="Your Habits", font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        self.habits_listbox = tk.Listbox(left_frame, width=35, height=18)
        self.habits_listbox.pack(pady=(5, 5))

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Add Habit", command=self.add_habit).grid(row=0, column=0, padx=2)
        ttk.Button(btn_frame, text="Mark Today", command=self.mark_today_done).grid(row=0, column=1, padx=2)
        ttk.Button(btn_frame, text="Reset Habit", command=self.reset_habit).grid(row=0, column=2, padx=2)
        ttk.Button(btn_frame, text="Delete Habit", command=self.delete_habit).grid(row=0, column=3, padx=2)

        # Right Frame
        right_frame = ttk.Frame(root, padding=(10, 10))
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(right_frame, text="Weekly Streak", font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        self.streak_display = tk.Text(right_frame, height=15, width=60, wrap=tk.WORD)
        self.streak_display.pack(pady=(5, 5))
        self.streak_display.config(state=tk.DISABLED)

        self.progress_label = ttk.Label(right_frame, text="")
        self.progress_label.pack(anchor=tk.W, pady=(5, 0))

        self.refresh_habits_list()

    # ---------- DATABASE FUNCTIONS ----------
    def load_habits_from_db(self):
        self.cursor.execute("SELECT * FROM habits")
        rows = self.cursor.fetchall()
        habits = []
        for row in rows:
            habits.append({
                "id": row[0],
                "name": row[1],
                "days": [row[2], row[3], row[4], row[5], row[6], row[7], row[8]]
            })
        return habits

    def save_habit_to_db(self, name):
        self.cursor.execute(
            "INSERT INTO habits (name) VALUES (%s)", (name,)
        )
        self.conn.commit()

    def update_habit_in_db(self, habit):
        query = """
            UPDATE habits SET mon=%s, tue=%s, wed=%s, thu=%s,
                              fri=%s, sat=%s, sun=%s
            WHERE id=%s
        """
        vals = (*habit["days"], habit["id"])
        self.cursor.execute(query, vals)
        self.conn.commit()

    def delete_habit_from_db(self, habit_id):
        self.cursor.execute("DELETE FROM habits WHERE id=%s", (habit_id,))
        self.conn.commit()

    # ---------- UI FUNCTIONS ----------
    def add_habit(self):
        name = simpledialog.askstring("New Habit", "Enter habit name:")
        if not name or name.strip() == "":
            return
        self.save_habit_to_db(name.strip())
        self.habits = self.load_habits_from_db()
        self.refresh_habits_list()

    def mark_today_done(self):
        sel = self.habits_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a habit first.")
            return
        index = sel[0]
        day_index = datetime.datetime.now().weekday()  # 0=Mon, 6=Sun
        self.habits[index]["days"][day_index] = True
        self.update_habit_in_db(self.habits[index])
        self.refresh_habits_list()

    def reset_habit(self):
        sel = self.habits_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a habit first.")
            return
        index = sel[0]
        self.habits[index]["days"] = [False]*7
        self.update_habit_in_db(self.habits[index])
        self.refresh_habits_list()

    def delete_habit(self):
        sel = self.habits_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a habit first.")
            return
        index = sel[0]
        habit_id = self.habits[index]["id"]
        self.delete_habit_from_db(habit_id)
        self.habits = self.load_habits_from_db()
        self.refresh_habits_list()

    def refresh_habits_list(self):
        self.habits_listbox.delete(0, tk.END)
        for i, h in enumerate(self.habits):
            streak = sum(h["days"])
            self.habits_listbox.insert(tk.END, f"{i+1}. {h['name']} ({streak}/7)")
        self.update_streak_display()

    def update_streak_display(self):
        self.streak_display.config(state=tk.NORMAL)
        self.streak_display.delete("1.0", tk.END)

        if not self.habits:
            self.streak_display.insert(tk.END, "No habits added yet.")
        else:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for h in self.habits:
                self.streak_display.insert(tk.END, f"{h['name']}\n")
                streak_line = ""
                for i, done in enumerate(h["days"]):
                    symbol = "🔵" if done else "⚪"
                    streak_line += f"{days[i]} {symbol}  "
                self.streak_display.insert(tk.END, streak_line + "\n\n")

        total_done = sum(sum(h["days"]) for h in self.habits)
        total_possible = len(self.habits) * 7
        if total_possible > 0:
            percent = (total_done / total_possible) * 100
            text = f"Overall progress: {percent:.0f}% of weekly habits done."
        else:
            text = "No data yet."
        self.progress_label.config(text=text)

        self.streak_display.config(state=tk.DISABLED)


# ---------- MAIN ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = HabitTrackerApp(root)
    root.mainloop()
