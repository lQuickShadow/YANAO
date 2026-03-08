from tkinter import *
from tkinter import ttk

class RegView(Tk):
    def __init__(self):
        super().__init__()
        self.title("Регистрация")
        self.geometry("500x500")
        self.resizable(width=False, height=False)



if __name__ ==  "__main__":
    win = RegView()
    win.mainloop()