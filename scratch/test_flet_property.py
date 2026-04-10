import flet as ft
img = ft.Image(src="")
print(f"Has src_base64: {hasattr(img, 'src_base64')}")
try:
    img.src_base64 = "abc"
    print("Successfully set src_base64 property")
except Exception as e:
    print(f"Failed to set src_base64: {e}")
