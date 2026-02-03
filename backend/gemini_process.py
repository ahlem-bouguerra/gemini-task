import asyncio
import os
import random
import time
import shutil
from playwright.async_api import async_playwright
import base64

# Configuration
USER_DATA_DIR = "/data/user_data"
IMAGE_PATH = os.environ.get("IMAGE_PATH", "/data/current_input.jpg")
GEMINI_URL = "https://gemini.google.com/app"

# قائمة الـ 50 Prompt - يختار واحد عشوائياً
PROMPT_LIST = [
    "اجعل هذا المنتج يظهر في صورة احترافية مع خلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية مع خلفية بيضاء نظيفة",
    "اجعل هذا المنتج يظهر في صورة احترافية بخلفية بيضاء وجودة عالية",
    "اجعل هذا المنتج يظهر في صورة احترافية على خلفية بيضاء نقية",
    "اجعل هذا المنتج يظهر في صورة احترافية مع خلفية بيضاء ساطعة",
    "اجعل هذا المنتج يظهر في صورة احترافية بخلفية بيضاء صافية",
    "اجعل هذا المنتج يظهر في صورة احترافية مع خلفية بيضاء تماماً",
    "اجعل هذا المنتج يظهر في صورة احترافية للتسويق بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية وخلفية بيضاء نظيفة",
    "اجعل هذا المنتج يظهر في صورة احترافية بخلفية بيضاء مثالية",
    "اجعل هذا المنتج يظهر في صورة احترافية مع خلفية بيضاء جذابة",
    "اجعل هذا المنتج يظهر في صورة احترافية بخلفية بيضاء واضحة",
    "اجعل هذا المنتج يظهر في صورة احترافية وإضاءة ممتازة مع خلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية بارزة على خلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية جاهزة للتسويق بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للمتجر بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية بخلفية بيضاء ناصعة",
    "اجعل هذا المنتج يظهر في صورة احترافية مميزة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية تجارية بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للبيع بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية كتالوج بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للنشر بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية مثل Amazon بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للمتجر الإلكتروني بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية نظيفة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية عالية الدقة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية مع خلفية بيضاء نقية تماماً",
    "اجعل هذا المنتج يظهر في صورة احترافية تسويقية بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية جذابة للعملاء بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للإعلانات بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية مشرقة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية واضحة المعالم بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية بجودة ممتازة وخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية أنيقة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية راقية بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية جاهزة للطباعة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للعرض بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية متميزة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية فاخرة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية عصرية بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية حديثة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية بسيطة وأنيقة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للسوشيال ميديا بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية للإنستغرام بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية مثل المحترفين بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية بتفاصيل واضحة بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية بإضاءة مثالية وخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية استديو بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية احترافية للبيع أونلاين بخلفية بيضاء",
    "اجعل هذا المنتج يظهر في صورة احترافية رائعة بخلفية بيضاء نظيفة"
]

async def wait_for_gemini_input(page, timeout_ms=120000):
    selectors = [
        'div[contenteditable="true"]',
        'div[role="textbox"]',
        'textarea',
    ]
    for sel in selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=timeout_ms, state="visible")
            if el:
                return el, sel
        except:
            continue
    raise TimeoutError("Gemini input not visible after login.")


async def cleanup_browser_locks():
    """نظف ملفات القفل الخاصة بالمتصفح"""
    lock_files = [
        os.path.join(USER_DATA_DIR, "SingletonLock"),
        os.path.join(USER_DATA_DIR, "SingletonSocket"),
        os.path.join(USER_DATA_DIR, "SingletonCookie"),
    ]
    
    for lock_file in lock_files:
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"🧹 Removed lock file: {lock_file}")
        except Exception as e:
            print(f"⚠️  Could not remove {lock_file}: {e}")

async def human_delay(min_sec=1, max_sec=3):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def random_mouse_movement(page):
    """تحريك الفأرة بشكل عشوائي لمحاكاة سلوك بشري"""
    try:
        x = random.randint(100, 1200)
        y = random.randint(100, 800)
        await page.mouse.move(x, y, steps=random.randint(5, 15))
        await asyncio.sleep(random.uniform(0.1, 0.3))
    except:
        pass

async def random_hover(page):
    """التوقف فوق عنصر عشوائي بدون نقر"""
    try:
        elements = await page.query_selector_all('div, button, span, p')
        if elements and len(elements) > 5:
            element = random.choice(elements[:20])
            box = await element.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                await page.mouse.move(x, y, steps=random.randint(10, 20))
                await asyncio.sleep(random.uniform(0.5, 1.5))
                print("🖱️  Hovering over random element...")
    except:
        pass

async def random_scroll(page):
    """التمرير العشوائي للأعلى والأسفل"""
    try:
        scroll_amount = random.randint(-200, 200)
        await page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")
        await asyncio.sleep(random.uniform(0.5, 1.0))
        print(f"📜 Scrolling {scroll_amount}px...")
    except:
        pass

async def human_move_and_click(page, element):
    if not element:
        print("Error: Element is None")
        return
    
    try:
        await element.scroll_into_view_if_needed()
        box = await element.bounding_box()
        if not box:
            print(f"Error: Could not get bounding box for element.")
            return
        
        target_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
        target_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
        
        await page.mouse.move(target_x, target_y, steps=random.randint(10, 20))
        await human_delay(0.2, 0.5)
        await page.mouse.click(target_x, target_y)
    except Exception as e:
        print(f"Error in human_move_and_click: {e}")

async def human_type(element, text):
    """Type text slowly with human-like delays"""
    try:
        await element.focus()
        await asyncio.sleep(0.3)
        
        base_speed = random.uniform(0.05, 0.15)
        for i, char in enumerate(text):
            await element.type(char)
            await asyncio.sleep(base_speed + random.uniform(0, 0.1))
            
            # Occasional thinking pause
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(0.3, 1.0))
    except Exception as e:
        print(f"Error in human_type: {e}")

async def paste_image_to_clipboard(page, image_path):
    print(f"📎 Encoding image {image_path} to base64...")
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    
    mime_type = "image/jpeg"
    if image_path.lower().endswith(".png"):
        mime_type = "image/png"
    elif image_path.lower().endswith(".webp"):
        mime_type = "image/webp"
        
    print("📋 Writing image to clipboard...")
    js_script = f"""
    async () => {{
        try {{
            const response = await fetch("data:{mime_type};base64,{encoded_string}");
            const originalBlob = await response.blob();
            const bitmap = await createImageBitmap(originalBlob);
            const canvas = document.createElement('canvas');
            canvas.width = bitmap.width;
            canvas.height = bitmap.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(bitmap, 0, 0);
            const pngBlob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
            await navigator.clipboard.write([new ClipboardItem({{ 'image/png': pngBlob }})]);
            return "success";
        }} catch (error) {{
            return "error: " + error.message;
        }}
    }}
    """
    result = await page.evaluate(js_script)
    if result != "success":
        raise Exception(f"Clipboard failed: {result}")
    
    print("✅ Image copied to clipboard!")

async def find_prompt_input_smart(page):
    """🎯 Recherche intelligente du champ de saisie"""
    print("\n🔍 Searching for prompt input field...")
    
    # Attendre que la page soit complètement chargée
    await page.wait_for_load_state("networkidle", timeout=15000)
    await asyncio.sleep(2)
    
    # Liste de sélecteurs à essayer dans l'ordre
    selectors = [
        'div.ql-editor[contenteditable="true"]',  # Éditeur Quill
        'div[role="textbox"]',
        'div[contenteditable="true"]',
        'textarea[placeholder*="Enter"]',
        'textarea[aria-label*="prompt"]',
        'textarea',
    ]
    
    for selector in selectors:
        try:
            print(f"  Trying: {selector}")
            elements = await page.query_selector_all(selector)
            
            for element in elements:
                # Vérifier si l'élément est visible
                is_visible = await element.is_visible()
                if not is_visible:
                    continue
                
                # Vérifier la taille (doit être assez grand pour être un champ de saisie)
                box = await element.bounding_box()
                if box and box['width'] > 100 and box['height'] > 30:
                    print(f"  ✅ Found visible input: {selector}")
                    return element, selector
                    
        except Exception as e:
            continue
    
    # Si rien trouvé, essayer JavaScript
    print("  🔍 Trying JavaScript search...")
    try:
        js_element = await page.evaluate('''() => {
            const editables = document.querySelectorAll('[contenteditable="true"], textarea');
            for (let el of editables) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 100 && rect.height > 30 && rect.top < window.innerHeight) {
                    el.setAttribute('data-found-by-js', 'true');
                    return true;
                }
            }
            return false;
        }''')
        
        if js_element:
            element = await page.query_selector('[data-found-by-js="true"]')
            if element:
                print("  ✅ Found via JavaScript!")
                return element, 'javascript-found'
    except:
        pass
    
    return None, None

async def main():
    # Nettoyer les verrous
    await cleanup_browser_locks()
    await asyncio.sleep(1)
    
    # Sélectionner un prompt aléatoire
    PROMPT = random.choice(PROMPT_LIST)
    print(f"📝 Selected Prompt: {PROMPT}")
    print("-" * 60)
    
    async with async_playwright() as p:
        print("🚀 Launching browser...")
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                permissions=["clipboard-read", "clipboard-write"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
        except Exception as e:
            print(f"❌ Failed to launch: {e}")
            print("🔄 Cleaning user_data and retrying...")
            shutil.rmtree(USER_DATA_DIR, ignore_errors=True)
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            await asyncio.sleep(2)
            
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                permissions=["clipboard-read", "clipboard-write"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
        
        # Utiliser la première page existante ou en créer une nouvelle

        page = await context.new_page()

        
        print(f"🌐 Navigating to {GEMINI_URL}...")
        await page.goto(GEMINI_URL, wait_until="load", timeout=60000)
        await asyncio.sleep(3)
        
        # Gérer les popups
        try:
            print("🔍 Checking for popups...")
            not_now_btn = await page.wait_for_selector('button:has-text("Not now")', timeout=3000)
            if not_now_btn:
                print("Closing popup...")
                await human_move_and_click(page, not_now_btn)
                await asyncio.sleep(2)
        except:
            print("✅ No blocking popups")
        
        # Vérification de connexion avec timeout étendu
        if "accounts.google.com" in page.url or await page.query_selector('text="Sign in"'):
            print("\n" + "="*60)
            print("🔐 LOGIN REQUIRED")
            print("Please log in to Google in the browser window")
            print("You have 10 MINUTES to complete the login")
            print("Script will wait patiently...")
            print("="*60 + "\n")
            
            # Attendre jusqu'à 10 minutes (600 secondes)
            max_wait_time = 600  # 10 minutes
            elapsed_time = 0
            check_interval = 3  # Vérifier toutes les 3 secondes
            
            while "gemini.google.com" not in page.url and elapsed_time < max_wait_time:
                await asyncio.sleep(check_interval)
                elapsed_time += check_interval
                
                # Afficher le temps restant toutes les 30 secondes
                if elapsed_time % 30 == 0:
                    remaining = (max_wait_time - elapsed_time) // 60
                    print(f"⏰ Still waiting for login... {remaining} minutes remaining")
            
            if "gemini.google.com" in page.url:
                print("✅ Login detected! Continuing...")
                await asyncio.sleep(5)
            else:
                print("❌ Login timeout after 10 minutes. Please try again.")
                await context.close()
                return
        
        # Attendre le chargement complet
        
        await asyncio.sleep(2)
        prompt_input, used_selector = await wait_for_gemini_input(page, timeout_ms=120000)
        print(f"✅ Input ready: {used_selector}")
        
        # Comportement humain léger
        if random.random() < 0.5:
            await random_scroll(page)
        await asyncio.sleep(1)
        
        
        if not prompt_input:
            print("\n❌ FAILED: Could not find prompt input field!")
            await page.screenshot(path="/app/debug_no_input.png", full_page=True)
            await context.close()
            return
        
        print(f"✅ SUCCESS: Found input field with: {used_selector}\n")
        
        # Copier et coller l'image
        try:
            await paste_image_to_clipboard(page, IMAGE_PATH)
            await asyncio.sleep(1)
            
            print("📎 Pasting image (Ctrl+V)...")
            await prompt_input.focus()
            await asyncio.sleep(0.5)
            await page.keyboard.press("Control+V")
            await asyncio.sleep(4)
            print("✅ Image pasted!")
            
        except Exception as e:
            print(f"⚠️  Paste failed: {e}")
        
        # Taper le prompt
        print("⌨️  Typing prompt...")
        await human_type(prompt_input, PROMPT)
        await asyncio.sleep(2)
        
        # Envoyer
        print("📤 Sending (Enter)...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)
        
        print("\n⏳ Waiting for Gemini to process (20s)...")
        await asyncio.sleep(20)
        
        # Recherche de l'image résultat
        print("🔍 Looking for generated image...")
        download_success = False
        
        for attempt in range(10):
            print(f"  Attempt {attempt+1}/10...")
            
            images = await page.query_selector_all('img')
            candidates = []
            
            for img in images:
                src = await img.get_attribute('src')
                if src and "googleusercontent" in src and "avatar" not in src:
                    box = await img.bounding_box()
                    if box and box['width'] > 200 and box['height'] > 200:
                        candidates.append((img, src))
            
            if candidates:
                target_img, target_src = candidates[-1]
                print(f"  ✅ Found candidate image!")
                
                try:
                    ext = "jpg"
                    if ".png" in target_src or "png" in target_src:
                        ext = "png"
                    elif "webp" in target_src:
                        ext = "webp"
                    
                    filename = f"/data/downloads/result_{int(time.time())}.{ext}"
                    print(f"  💾 Downloading to {filename}...")
                    
                    response = await page.request.get(target_src)
                    img_bytes = await response.body()
                    
                    os.makedirs("/data/downloads", exist_ok=True)
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    
                    print(f"  ✅ Download successful! ({len(img_bytes)} bytes)")
                    download_success = True
                    break
                    
                except Exception as e:
                    print(f"  ❌ Download failed: {e}")
            
            await asyncio.sleep(5)
        
        if not download_success:
            print("\n❌ No result image found")
            await page.screenshot(path="/data/debug_no_result.png", full_page=True)
        else:
            print("\n✅ ✅ ✅ SUCCESS! Check /data/downloads/ folder ✅ ✅ ✅")
        
        await asyncio.sleep(2)
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())