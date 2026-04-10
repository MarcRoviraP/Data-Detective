import flet as ft
img = ft.Image(src="")
attrs = dir(img)
for a in attrs:
    if "base64" in a.lower():
        print(a)
