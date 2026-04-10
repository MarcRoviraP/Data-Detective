import flet as ft
img = ft.Image(src="")
attrs = dir(img)
for a in attrs:
    if "src" in a:
        print(a)
