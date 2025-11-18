# File: FITNZ/auth_ui.py
import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from .database import authenticate_user, add_user

class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        
        login_frame = ttk.Frame(self)
        login_frame.grid(row=0, column=0)
        
        ttk.Label(login_frame, text="Fit NZ POS", font=("Helvetica", 36, "bold"), bootstyle="primary").pack(pady=20)
        
        # Role Selection
        role_frame = ttk.Labelframe(login_frame, text="Select Role", padding=15, bootstyle="info")
        role_frame.pack(pady=10, fill="x")
        self.selected_role = tk.StringVar()
        # Added Customer back to roles
        roles = ["Employee", "Manager", "Developer", "Customer"] 
        self.role_combobox = ttk.Combobox(role_frame, textvariable=self.selected_role, values=roles, state="readonly")
        self.role_combobox.set("Employee")
        self.role_combobox.pack(padx=10, pady=5, fill="x")
        
        # Credentials
        entry_frame = ttk.Frame(login_frame); entry_frame.pack(pady=10, padx=40, fill="x")
        ttk.Label(entry_frame, text="Username").pack(anchor="w")
        self.username_entry = ttk.Entry(entry_frame, font=("Helvetica", 12)); self.username_entry.pack(pady=(0, 10), fill="x")
        ttk.Label(entry_frame, text="Password").pack(anchor="w")
        self.password_entry = ttk.Entry(entry_frame, font=("Helvetica", 12), show="*"); self.password_entry.pack(pady=(0, 10), fill="x")
        
        # Login Button
        login_btn = ttk.Button(login_frame, text="Login", command=self.attempt_login, bootstyle="success-lg")
        login_btn.pack(pady=10, ipady=8, fill="x", padx=40)

        # --- NEW: Sign Up Button ---
        signup_btn = ttk.Button(login_frame, text="Create Account (Customer)", command=self.open_signup, bootstyle="link")
        signup_btn.pack(pady=5)
        
        # Exit
        ttk.Button(login_frame, text="Exit", command=self.controller.confirm_exit, bootstyle="danger-outline").pack(pady=5)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.selected_role.get()
        
        if not all([username, password, role]):
            Messagebox.show_error("Credentials required.", "Login Failed", parent=self)
            return
            
        user = authenticate_user(username, password, role)
        if user:
            self.controller.show_main_app(user)
        else:
            Messagebox.show_error("Invalid credentials.", "Login Failed", parent=self)

    def open_signup(self):
        SignupPage(self)

# --- NEW: Signup Page Class ---
class SignupPage(bs.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Customer Sign Up")
        self.geometry("400x450")
        
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Join Fit NZ", font=("Helvetica", 20, "bold"), bootstyle="primary").pack(pady=10)
        
        ttk.Label(frame, text="Full Name:").pack(anchor="w")
        self.name_entry = ttk.Entry(frame); self.name_entry.pack(fill="x", pady=5)
        
        ttk.Label(frame, text="Contact (Email/Phone):").pack(anchor="w")
        self.contact_entry = ttk.Entry(frame); self.contact_entry.pack(fill="x", pady=5)
        
        ttk.Label(frame, text="Delivery Address:").pack(anchor="w")
        self.address_entry = ttk.Entry(frame); self.address_entry.pack(fill="x", pady=5)
        
        ttk.Label(frame, text="Username:").pack(anchor="w")
        self.user_entry = ttk.Entry(frame); self.user_entry.pack(fill="x", pady=5)

        ttk.Label(frame, text="Password:").pack(anchor="w")
        self.pass_entry = ttk.Entry(frame, show="*"); self.pass_entry.pack(fill="x", pady=5)
        
        ttk.Button(frame, text="Create Account", command=self.create_account, bootstyle="success").pack(fill="x", pady=20)

    def create_account(self):
        name = self.name_entry.get()
        contact = self.contact_entry.get()
        address = self.address_entry.get()
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if not all([name, contact, address, username, password]):
            Messagebox.show_error("All fields are required.", "Error", parent=self)
            return

        if add_user(name, contact, username, password, "Customer", address):
            Messagebox.show_info("Account created! You can now login.", "Success", parent=self)
            self.destroy()
        else:
            Messagebox.show_error("Username already exists.", "Error", parent=self)
