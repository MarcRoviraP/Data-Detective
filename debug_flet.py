"""
Debug script to verify Flet Container padding argument behavior.
"""
import flet as ft
try:
    c = ft.Container(padding=10)
    print("Success: Container created with padding=10")
except TypeError as e:
    print(f"TypeError: {e}")
except Exception as e:
    print(f"Error: {e}")
