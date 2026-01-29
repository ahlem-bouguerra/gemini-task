import asyncio
import os
import random
import time
from playwright.async_api import async_playwright

import base64

# Configuration
USER_DATA_DIR = "/app/user_data"
IMAGE_PATH = "/app/WhatsApp Image 2026-01-22 at 22.24.34.jpeg"
PROMPT = "اجعل هذا المنتج يضهز في صورة احترافية مع خلفية بيضاء"
GEMINI_URL = "https://gemini.google.com/app"

async def human_delay(min_sec=1, max_sec=3):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def human_move_and_click(page, element):
    if not element:
        print("Error: Element is None")
        return
    
    # Ensure element is visible and stable
    await element.scroll_into_view_if_needed()
    
    # Get element bounding box
    box = await element.bounding_box()
    if not box:
        print(f"Error: Could not get bounding box for element. It might be hidden.")
        return
        
    # Find center with some randomness
    target_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
    target_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
    
    # Move mouse in steps
    print(f"Moving mouse to ({target_x}, {target_y})...")
    await page.mouse.move(target_x, target_y, steps=random.randint(10, 20))
    await human_delay(0.2, 0.5)
    await page.mouse.click(target_x, target_y)

async def human_type(page, selector, text):
    element = await page.wait_for_selector(selector)
    await human_move_and_click(page, element)
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.2))

async def apply_stealth(page):
    try:
        import playwright_stealth
        if hasattr(playwright_stealth, "stealth_async"):
            await playwright_stealth.stealth_async(page)
        elif hasattr(playwright_stealth, "stealth"):
            s = getattr(playwright_stealth, "stealth")
            if callable(s):
                await s(page)
    except Exception as e:
        print(f"Warning: Failed to apply stealth: {e}")

async def paste_image_to_clipboard(page, image_path):
    print(f"Encoding image {image_path} to base64...")
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Determine mime type
    mime_type = "image/jpeg"
    if image_path.lower().endswith(".png"):
        mime_type = "image/png"
        
    print("Writing image to clipboard via browser JS...")
    # Use evaluate to write to clipboard
    # Browsers often only support image/png for clipboard write
    # We convert the base64 (which might be jpeg) to png via canvas in the browser
    js_script = f"""
    async () => {{
        try {{
            // 1. Fetch the original image data
            const response = await fetch("data:{mime_type};base64,{encoded_string}");
            const originalBlob = await response.blob();
            
            // 2. Create an image bitmap
            const bitmap = await createImageBitmap(originalBlob);
            
            // 3. Draw to canvas
            const canvas = document.createElement('canvas');
            canvas.width = bitmap.width;
            canvas.height = bitmap.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(bitmap, 0, 0);
            
            // 4. Convert to PNG blob
            const pngBlob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
            
            // 5. Write to clipboard
            await navigator.clipboard.write([new ClipboardItem({{ 'image/png': pngBlob }})]);
            return "success";
        }} catch (error) {{
            return "error: " + error.message;
        }}
    }}
    """
    result = await page.evaluate(js_script)
    if result != "success":
         raise Exception(f"Clipboard JS failed: {result}")
    
    print("Image copied to clipboard (converted to PNG)!")

async def main():
    async with async_playwright() as p:
        print("Launching browser...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            permissions=["clipboard-read", "clipboard-write"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        page = await context.new_page()
        await apply_stealth(page)
        
        print(f"Navigating to {GEMINI_URL}...")
        try:
            await page.goto(GEMINI_URL, wait_until="load", timeout=60000)
        except Exception as e:
            print(f"Navigation warning: {e}")
        
        # Handle "Stay in the know" or other welcome modals
        try:
            print("Checking for popups...")
            stay_updated_btn = await page.wait_for_selector('button:has-text("Stay updated")', timeout=5000)
            not_now_btn = await page.wait_for_selector('button:has-text("Not now")', timeout=3000)
            
            if not_now_btn:
                print("Found 'Stay in the know' modal. Clicking 'Not now'...")
                await human_move_and_click(page, not_now_btn)
                await asyncio.sleep(2)
            elif stay_updated_btn:
                print("Found 'Stay updated' button. Looking for dismiss option...")
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)
        except:
            print("No blocking popups found.")
        
        # Initial login check
        if "accounts.google.com" in page.url or await page.query_selector('text="Sign in"'):
            print("--- LOGIN REQUIRED ---")
            print("Please log in to your Google account in the browser window.")
            print("The script will wait for you to reach the Gemini interface...")
            
            while "gemini.google.com" not in page.url:
                await asyncio.sleep(2)
            print("Login detected! Proceeding...")
        
        try:
            await page.wait_for_load_state("load", timeout=30000)
        except:
            pass # Continue if load state takes too long
        await human_delay(3, 5)

        # PASTE METHOD
        print("Method: Clipboard Paste (Base64)...")
        
        # Find the prompt area first to focus it
        prompt_selectors = [
                 'div[contenteditable="true"]',
                 'textarea[aria-label*="prompt"]',
                 'chat-input textarea',
                 'textarea'
        ]
        
        prompt_input = None
        for selector in prompt_selectors:
            try:
                print(f"Looking for prompt input: {selector}")
                # We need it visible to focus
                prompt_input = await page.wait_for_selector(selector, timeout=5000)
                if prompt_input:
                    print(f"Found prompt input. Focusing...")
                    await human_move_and_click(page, prompt_input)
                    await asyncio.sleep(1)
                    break
            except:
                continue
                
        if prompt_input:
            # Copy image to clipboard
            try:
                await paste_image_to_clipboard(page, IMAGE_PATH)
                await asyncio.sleep(1)
                
                print("Pasting image (Ctrl+V)...")
                await prompt_input.focus()
                await page.keyboard.press("Control+V")
                await asyncio.sleep(5) # Wait for image upload preview
                print("Paste command sent. Waiting for upload preview...")
                
                # Check if image appeared (optional but good for debug)
                # Usually an img tag or specific class appears in the input container
                
            except Exception as e:
                print(f"Clipboard paste failed: {e}")
            
            print("Typing prompt...")
            await human_type(page, selector, PROMPT)
            await human_delay(1, 2)

            print("Sending prompt (Pressing Enter)...")
            await page.keyboard.press("Enter")

            print("Task submitted! Waiting for Nano Banana to process...")
            
            # Wait for generation (can take 10-20 seconds)
            await asyncio.sleep(20)
            
            print("Looking for generated image...")
            download_success = False
            for attempt in range(10): # Try for ~1 minute
                print(f"Check attempt {attempt+1}/10...")
                images = await page.query_selector_all('img')
                # Filter images: We want large images, likely hosted on googleusercontent
                candidates = []
                for img in images:
                    src = await img.get_attribute('src')
                    if src and "googleusercontent" in src and "avatar" not in src:
                         # Check size to ensure it's not a thumbnail
                        box = await img.bounding_box()
                        if box and box['width'] > 200 and box['height'] > 200:
                            candidates.append((img, src))
                
                if candidates:
                    # The last one is likely the new result
                    target_img, target_src = candidates[-1]
                    print(f"Found candidate image: {target_src[:50]}...")
                    
                    try:
                        # Extract extension
                        ext = "jpg" 
                        if "png" in target_src: ext = "png"
                        if "webp" in target_src: ext = "webp"
                        
                        filename = f"/app/downloads/result_{int(time.time())}.{ext}"
                        print(f"Downloading to {filename}...")
                        
                        # Download using Playwright's APIRequestContext (shares cookies!)
                        response = await page.request.get(target_src)
                        img_bytes = await response.body()
                        
                        with open(filename, "wb") as f:
                            f.write(img_bytes)
                            
                        print("Download successful!")
                        download_success = True
                        break
                    except Exception as e:
                        print(f"Download failed: {e}")
                
                await asyncio.sleep(5)
            
            if not download_success:
                 print("Could not identify/download result image.")
                 
            await page.screenshot(path="/app/debug_result.png")
            
            print("Done! Check downloads folder or debug_result.png")
            print("Closing browser...")
            await asyncio.sleep(2)

        else:
             print("Could not find prompt input to paste into.")
             await page.screenshot(path="/app/debug_no_prompt.png")

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
