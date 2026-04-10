import asyncio
from playwright.async_api import async_playwright

async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print("Navigating to http://localhost:8550/...")
        await page.goto("http://localhost:8550/")
        
        # Esperar a que cargue la app (quitando el splash)
        print("Waiting for app to load...")
        await page.wait_for_timeout(10000) 
        
        # Buscar el botón de búsqueda
        # En Flet, el botón de búsqueda tiene el icono SEARCH
        # Podemos intentar buscar por tooltip "Buscar datos históricos"
        print("Searching for search button...")
        search_btn = page.locator('button[title="Buscar datos históricos"]')
        if await search_btn.count() > 0:
            print("Clicking search button...")
            await search_btn.click()
            await asyncio.sleep(5)
            print("Test interaction complete.")
        else:
            print("Search button not found.")
            # Intentar clickear por el icono si el tooltip no funciona
            # Flet icon buttons often have the icon as text or in a span
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
