# File: FITNZ/customer_ui.py
import tkinter as tk
from tkinter import ttk
from ttkbootstrap.dialogs import Messagebox
import ttkbootstrap as bs
from . import database as db
from datetime import date

class CartPage(bs.Toplevel):
    def _init_(self, parent, cart, customer):
        super()._init_(parent)
        self.parent = parent
        self.cart = cart
        self.customer = customer
        self.title("My Cart")
        self.geometry("600x500")
        
        # ... (UI setup code same as before) ...
        f = ttk.Frame(self, padding=20); f.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(f, columns=("name", "price"), show="headings")
        self.tree.heading("name", text="Item"); self.tree.heading("price", text="Price")
        self.tree.pack(fill="both", expand=True)
        for item in cart: self.tree.insert("", "end", values=(item.name, f"${item.price:.2f}"))
        
        self.total_lbl = ttk.Label(f, text="", font="bold"); self.total_lbl.pack(pady=10)
        self.update_total()
        
        ttk.Button(f, text="Checkout & Pay", command=self.open_checkout, bootstyle="success").pack(fill="x")

    def update_total(self):
        t = sum(i.price for i in self.cart)
        self.total_lbl.config(text=f"Total: ${t:.2f}")

    def open_checkout(self):
        CheckoutPage(self, self.cart, self.customer)

class CheckoutPage(bs.Toplevel):
    def _init_(self, parent, cart, customer):
        super()._init_(parent)
        self.parent = parent # CartPage
        self.main_app = parent.parent # MainAppPage
        self.cart = cart
        self.customer = customer
        self.title("Checkout")
        self.geometry("400x300")
        
        f = ttk.Frame(self, padding=20); f.pack(fill="both")
        ttk.Label(f, text="Payment Details", font="bold").pack(pady=10)
        ttk.Entry(f).pack(fill="x", pady=5) # Card number dummy
        
        ttk.Button(f, text="Confirm Payment", command=self.pay, bootstyle="success").pack(pady=20)

    # --- NEW: Receipt Generation Logic ---
    def pay(self):
        # 1. Process Sale in DB
        db.process_sale(self.customer, self.cart, 0, False, date.today())
        
        # 2. Generate Receipt Text
        receipt_text = "--- FIT NZ RECEIPT ---\n"
        receipt_text += f"Date: {date.today()}\n"
        receipt_text += f"Customer: {self.customer.get_name()}\n"
        receipt_text += "----------------------\n"
        total = 0
        for item in self.cart:
            receipt_text += f"{item.name}: ${item.price:.2f}\n"
            total += item.price
        receipt_text += "----------------------\n"
        receipt_text += f"TOTAL PAID: ${total:.2f}\n"
        receipt_text += "----------------------\n"
        receipt_text += "Thank you for shopping with Fit NZ!"
        
        # 3. Save to File
        filename = f"receipt_{self.customer.get_name()}_{date.today()}.txt"
        with open(filename, "w") as f:
            f.write(receipt_text)
            
        Messagebox.show_info(f"Payment Successful!\nReceipt saved to {filename}", "Success", parent=self)
        
        # 4. Cleanup
        self.main_app.clear_cart()
        self.parent.destroy()
        self.destroy()

class MembershipPage(bs.Toplevel):
    # ... (Same as previous version) ...
    def _init_(self, parent, customer):
        super()._init_(parent); self.parent=parent; self.cust=customer
        f=ttk.Frame(self, padding=20); f.pack()
        ttk.Button(f, text="Upgrade Gold", command=lambda: self.up("Gold")).pack()
    def up(self, l):
        db.update_customer_membership(self.cust._customer_id, l)
        self.parent.update_customer_info(); self.destroy()


