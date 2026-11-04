
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import date

# DATABASE
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT
)
""")
conn.commit()

CATEGORIES = [
    "Food", "Shopping", "Travel", "Education",
    "Bills", "Entertainment", "Health",
    "Rent", "Salary", "Other"
]

# MAIN WINDOW
root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("1050x700")
root.configure(bg="#f2f4f8")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", rowheight=28, font=("Arial", 10))
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

# VARIABLES
transaction_type = tk.StringVar(value="Expense")
category_var = tk.StringVar(value="Food")
filter_var = tk.StringVar(value="All")
date_var = tk.StringVar(value=str(date.today()))

selected_id = None

# SUMMARY
def get_totals():
    cursor.execute("""
        SELECT
        SUM(CASE WHEN transaction_type='Income' THEN amount ELSE 0 END),
        SUM(CASE WHEN transaction_type='Expense' THEN amount ELSE 0 END)
        FROM transactions
    """)
    income, expenses = cursor.fetchone()
    income = income or 0
    expenses = expenses or 0
    return income, expenses, income - expenses


def update_summary():
    income, expenses, balance = get_totals()
    income_label.config(text=f"₹ {income:,.2f}")
    expense_label.config(text=f"₹ {expenses:,.2f}")
    balance_label.config(text=f"₹ {balance:,.2f}")


# LOAD TRANSACTIONS
def load_transactions():
    for item in table.get_children():
        table.delete(item)

    if filter_var.get() == "All":
        cursor.execute("""
            SELECT * FROM transactions
            ORDER BY transaction_date DESC, id DESC
        """)
    else:
        cursor.execute("""
            SELECT * FROM transactions
            WHERE category=?
            ORDER BY transaction_date DESC, id DESC
        """, (filter_var.get(),))

    for row in cursor.fetchall():
        table.insert("", "end", values=row)

    update_summary()


# CLEAR FORM
def clear_fields():
    global selected_id
    selected_id = None

    date_var.set(str(date.today()))
    transaction_type.set("Expense")
    category_var.set("Food")
    amount_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)


# ADD TRANSACTION
def add_transaction():
    try:
        transaction_date = date_var.get().strip()
        date.fromisoformat(transaction_date)

        amount = float(amount_entry.get())

        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than zero")
            return

        cursor.execute("""
            INSERT INTO transactions
            (transaction_date, transaction_type, category, amount, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            transaction_date,
            transaction_type.get(),
            category_var.get(),
            amount,
            description_entry.get().strip()
        ))

        conn.commit()
        load_transactions()
        clear_fields()

        messagebox.showinfo("Success", "Transaction added successfully!")

    except ValueError:
        messagebox.showerror(
            "Invalid Input",
            "Enter a valid date (YYYY-MM-DD) and amount."
        )


# SELECT TRANSACTION
def select_transaction(event):
    global selected_id

    selected = table.selection()
    if not selected:
        return

    values = table.item(selected[0], "values")
    selected_id = values[0]

    date_var.set(values[1])
    transaction_type.set(values[2])
    category_var.set(values[3])

    amount_entry.delete(0, tk.END)
    amount_entry.insert(0, values[4])

    description_entry.delete(0, tk.END)
    description_entry.insert(0, values[5])


# UPDATE TRANSACTION
def update_transaction():
    if selected_id is None:
        messagebox.showwarning("Select", "Select a transaction first")
        return

    try:
        transaction_date = date_var.get().strip()
        date.fromisoformat(transaction_date)

        amount = float(amount_entry.get())

        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than zero")
            return

        cursor.execute("""
            UPDATE transactions
            SET transaction_date=?, transaction_type=?,
                category=?, amount=?, description=?
            WHERE id=?
        """, (
            transaction_date,
            transaction_type.get(),
            category_var.get(),
            amount,
            description_entry.get().strip(),
            selected_id
        ))

        conn.commit()
        load_transactions()
        clear_fields()

        messagebox.showinfo("Success", "Transaction updated!")

    except ValueError:
        messagebox.showerror("Error", "Enter a valid date and amount")


# DELETE TRANSACTION
def delete_transaction():
    if selected_id is None:
        messagebox.showwarning("Select", "Select a transaction first")
        return

    if messagebox.askyesno("Confirm", "Delete this transaction?"):
        cursor.execute(
            "DELETE FROM transactions WHERE id=?",
            (selected_id,)
        )
        conn.commit()
        load_transactions()
        clear_fields()
        messagebox.showinfo("Deleted", "Transaction deleted!")


# EXPORT CSV
def export_csv():
    cursor.execute("SELECT * FROM transactions")
    records = cursor.fetchall()

    if not records:
        messagebox.showwarning("Empty", "No transactions to export")
        return

    filename = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile="expense_report.csv"
    )

    if filename:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "ID", "Date", "Type",
                "Category", "Amount", "Description"
            ])
            writer.writerows(records)

        messagebox.showinfo("Success", "CSV report exported!")


# MONTHLY SUMMARY
def monthly_summary():
    month = date.today().strftime("%Y-%m")

    cursor.execute("""
        SELECT
        SUM(CASE WHEN transaction_type='Income' THEN amount ELSE 0 END),
        SUM(CASE WHEN transaction_type='Expense' THEN amount ELSE 0 END)
        FROM transactions
        WHERE transaction_date LIKE ?
    """, (month + "%",))

    income, expenses = cursor.fetchone()
    income = income or 0
    expenses = expenses or 0

    messagebox.showinfo(
        "Monthly Summary",
        f"Month: {month}\n\n"
        f"Income: ₹{income:,.2f}\n"
        f"Expenses: ₹{expenses:,.2f}\n"
        f"Balance: ₹{income-expenses:,.2f}"
    )


# HEADING
tk.Label(
    root,
    text="PERSONAL EXPENSE TRACKER",
    font=("Arial", 22, "bold"),
    bg="#f2f4f8",
    fg="#243b64"
).pack(pady=15)


# SUMMARY CARDS
summary_frame = tk.Frame(root, bg="#f2f4f8")
summary_frame.pack(fill="x", padx=20)


def create_card(parent, title, color):
    frame = tk.Frame(parent, bg="white", padx=15, pady=12)
    frame.pack(side="left", expand=True, fill="x", padx=8)

    tk.Label(
        frame, text=title,
        font=("Arial", 11, "bold"),
        bg="white", fg="#555"
    ).pack()

    label = tk.Label(
        frame, text="₹ 0.00",
        font=("Arial", 19, "bold"),
        bg="white", fg=color
    )
    label.pack(pady=5)
    return label


income_label = create_card(summary_frame, "TOTAL INCOME", "#198754")
expense_label = create_card(summary_frame, "TOTAL EXPENSES", "#dc3545")
balance_label = create_card(summary_frame, "BALANCE", "#2457a6")


# INPUT FORM
form = tk.LabelFrame(
    root,
    text=" Add Transaction ",
    font=("Arial", 12, "bold"),
    bg="white",
    padx=15,
    pady=12
)
form.pack(fill="x", padx=28, pady=15)

tk.Label(form, text="Date (YYYY-MM-DD)", bg="white").grid(
    row=0, column=0, sticky="w", pady=5
)
tk.Entry(form, textvariable=date_var, width=22).grid(
    row=1, column=0, padx=8, pady=5
)

tk.Label(form, text="Type", bg="white").grid(
    row=0, column=1, sticky="w", pady=5
)
ttk.Combobox(
    form,
    textvariable=transaction_type,
    values=["Income", "Expense"],
    state="readonly",
    width=19
).grid(row=1, column=1, padx=8, pady=5)

tk.Label(form, text="Category", bg="white").grid(
    row=0, column=2, sticky="w", pady=5
)
ttk.Combobox(
    form,
    textvariable=category_var,
    values=CATEGORIES,
    state="readonly",
    width=19
).grid(row=1, column=2, padx=8, pady=5)

tk.Label(form, text="Amount (₹)", bg="white").grid(
    row=2, column=0, sticky="w", pady=5
)
amount_entry = tk.Entry(form, width=22)
amount_entry.grid(row=3, column=0, padx=8, pady=5)

tk.Label(form, text="Description", bg="white").grid(
    row=2, column=1, sticky="w", pady=5
)
description_entry = tk.Entry(form, width=45)
description_entry.grid(
    row=3, column=1, columnspan=2, padx=8, pady=5, sticky="w"
)


# BUTTONS
button_frame = tk.Frame(root, bg="#f2f4f8")
button_frame.pack(pady=5)


def make_button(text, command, color):
    return tk.Button(
        button_frame,
        text=text,
        command=command,
        bg=color,
        fg="white",
        font=("Arial", 10, "bold"),
        width=15,
        pady=7,
        relief="flat",
        cursor="hand2"
    )


make_button("Add", add_transaction, "#198754").pack(side="left", padx=5)
make_button("Update", update_transaction, "#2457a6").pack(side="left", padx=5)
make_button("Delete", delete_transaction, "#dc3545").pack(side="left", padx=5)
make_button("Clear", clear_fields, "#6c757d").pack(side="left", padx=5)


# FILTER AND REPORTS
filter_frame = tk.Frame(root, bg="#f2f4f8")
filter_frame.pack(fill="x", padx=30, pady=10)

tk.Label(
    filter_frame,
    text="Filter by Category:",
    bg="#f2f4f8",
    font=("Arial", 10, "bold")
).pack(side="left")

filter_box = ttk.Combobox(
    filter_frame,
    textvariable=filter_var,
    values=["All"] + CATEGORIES,
    state="readonly",
    width=18
)
filter_box.pack(side="left", padx=8)
filter_box.bind(
    "<<ComboboxSelected>>",
    lambda e: load_transactions()
)

tk.Button(
    filter_frame,
    text="Monthly Summary",
    command=monthly_summary,
    bg="#6f42c1",
    fg="white",
    padx=10
).pack(side="right", padx=5)

tk.Button(
    filter_frame,
    text="Export CSV",
    command=export_csv,
    bg="#198754",
    fg="white",
    padx=10
).pack(side="right", padx=5)


# TRANSACTION TABLE
table_frame = tk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=28, pady=10)

columns = (
    "ID", "Date", "Type",
    "Category", "Amount", "Description"
)

table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings"
)

for col in columns:
    table.heading(col, text=col)
    table.column(col, width=130, anchor="center")

table.column("Description", width=200)

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=table.yview
)

table.configure(yscrollcommand=scrollbar.set)

table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

table.bind("<<TreeviewSelect>>", select_transaction)


# START APPLICATION
load_transactions()


def close_app():
    conn.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
