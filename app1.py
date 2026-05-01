import tkinter as tk

# Function to handle button clicks
def click(value):
    entry.insert(tk.END, value)

# Function to evaluate expression
def calculate():
    try:
        result = eval(entry.get())
        entry.delete(0, tk.END)
        entry.insert(tk.END, result)
    except:
        entry.delete(0, tk.END)
        entry.insert(tk.END, "Error")

# Function to clear screen
def clear():
    entry.delete(0, tk.END)

# Main window
root = tk.Tk()
root.title("Calculator")
root.geometry("300x400")

# Entry field
entry = tk.Entry(root, font=("Arial", 18), bd=5, relief=tk.RIDGE, justify='right')
entry.pack(fill=tk.BOTH, ipadx=8, ipady=15, padx=10, pady=10)

# Buttons layout (with decimal support)
buttons = [
    ['7','8','9','/'],
    ['4','5','6','*'],
    ['1','2','3','-'],
    ['0','.','=','+'],
    ['C']
]

# Create buttons
for row in buttons:
    frame = tk.Frame(root)
    frame.pack(expand=True, fill="both")

    for btn in row:
        if btn == '=':
            action = calculate
        elif btn == 'C':
            action = clear
        else:
            action = lambda x=btn: click(x)

        tk.Button(frame, text=btn, font=("Arial", 14), command=action)\
            .pack(side="left", expand=True, fill="both")

# Run app
root.mainloop()
