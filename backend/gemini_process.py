"""
gemini_session.py
-----------------
Toutes les images sont traitées dans UNE SEULE conversation Gemini.
Pas de new_chat, pas de reload entre les images.
On garde un set() des src déjà vues pour ne détécter que la nouvelle image.
"""

import asyncio
import os
import random
import time
import base64
from playwright.async_api import async_playwright, BrowserContext, Page

# ── Config ────────────────────────────────────────────────────────────────────
USER_DATA_DIR = "/data/user_data"
DOWNLOADS_DIR = "/data/downloads"
GEMINI_URL    = "https://gemini.google.com/app"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# ── 50 Prompts ────────────────────────────────────────────────────────────────
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
    "اجعل هذا المنتج يظهر في صورة احترافية رائعة بخلفية بيضاء نظيفة",
]


# ══════════════════════════════════════════════════════════════════════════════
# COMPORTEMENTS HUMAINS
# ══════════════════════════════════════════════════════════════════════════════

async def human_pause(min_s: float = 0.5, max_s: float = 2.0):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def thinking_pause():
    await asyncio.sleep(random.uniform(1.5, 4.0))

def _bezier(p0, p1, p2, t):
    return (
        (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0],
        (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1],
    )

async def move_mouse_naturally(page: Page, tx: float, ty: float, steps: int = 20):
    """Courbe Bézier — mouvement naturel, pas une ligne droite."""
    sx, sy = random.randint(200, 1100), random.randint(200, 700)
    cx = random.uniform(min(sx, tx) - 100, max(sx, tx) + 100)
    cy = random.uniform(min(sy, ty) - 80,  max(sy, ty) + 80)
    for i in range(1, steps + 1):
        x, y = _bezier((sx, sy), (cx, cy), (tx, ty), i / steps)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.02, 0.06))

async def click_naturally(page: Page, element):
    """Move vers l'élément puis click avec un petit offset aléatoire."""
    box = await element.bounding_box()
    if not box:
        await element.click()
        return
    x = box["x"] + box["width"]  * random.uniform(0.25, 0.75)
    y = box["y"] + box["height"] * random.uniform(0.25, 0.75)
    await move_mouse_naturally(page, x, y)
    await human_pause(0.1, 0.3)
    await page.mouse.click(x, y)

async def random_scroll(page: Page):
    amount = random.randint(-150, 150)
    await page.evaluate(f"window.scrollBy({{top: {amount}, behavior: 'smooth'}})")
    await human_pause(0.3, 0.8)
    print(f"    🖱️  Scroll {amount}px")

async def hover_random_element(page: Page):
    try:
        elements = await page.query_selector_all("div, span, p, button, a, h1, h2, h3")
        visible = []
        for el in elements[:30]:
            if await el.is_visible():
                box = await el.bounding_box()
                if box and box["width"] > 40 and box["height"] > 15:
                    visible.append(box)
        if visible:
            box = random.choice(visible)
            await move_mouse_naturally(page, box["x"] + box["width"]/2, box["y"] + box["height"]/2)
            await human_pause(0.4, 1.2)
            print("    👁️  Hover élément")
    except:
        pass

async def idle_behavior(page: Page):
    """1-3 actions aléatoires : scroll / hover / pause."""
    for _ in range(random.randint(1, 3)):
        r = random.random()
        if r < 0.35:
            await random_scroll(page)
        elif r < 0.7:
            await hover_random_element(page)
        else:
            await human_pause(0.8, 2.5)

async def read_page_behavior(page: Page):
    """Comme quelqu'un qui lit la page avant d'agir."""
    print("    📖 Reading page...")
    await hover_random_element(page)
    await human_pause(0.5, 1.5)
    if random.random() < 0.5:
        await random_scroll(page)
    await hover_random_element(page)
    await thinking_pause()


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════
class GeminiSession:
    def __init__(self):
        self._playwright      = None
        self._browser_context: BrowserContext | None = None
        self._page: Page | None       = None
        self._is_ready                = False

        # ── CRUCIAL : mémoire des images déjà vues dans la conversation ──
        # On stocke les src de chaque image googleusercontent qu'on a déjà
        # détectée. Comme ça, après chaque envoi on ne cherche que les
        # NOUVELLES src qui n'étaient pas là avant.
        self._seen_image_srcs: set = set()

    # ── LIFECYCLE ─────────────────────────────────────────────────────────

    async def start(self):
        print("🚀 [GeminiSession] Launching persistent Chromium...")
        self._playwright = await async_playwright().start()

        try:
            self._browser_context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                permissions=["clipboard-read", "clipboard-write"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
        except Exception as e:
            print(f"⚠️  Launch failed ({e}), cleaning profile and retrying...")
            import shutil
            shutil.rmtree(USER_DATA_DIR, ignore_errors=True)
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            await asyncio.sleep(2)
            self._browser_context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                permissions=["clipboard-read", "clipboard-write"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

        self._page = await self._browser_context.new_page()

        print("🌐 [GeminiSession] Navigating to Gemini...")
        await self._page.goto(GEMINI_URL, wait_until="load", timeout=60_000)
        await asyncio.sleep(3)

        await self._dismiss_popups()
        await self._wait_for_login()

        # On "regarde" la page comme un humain
        await read_page_behavior(self._page)

        await self._wait_for_input()

        # Snapshot des images déjà présentes sur la page (avatars etc)
        # pour ne pas les confondre avec les résultats
        await self._snapshot_existing_images()

        self._is_ready = True
        print("✅ [GeminiSession] Browser ready — une seule conversation pour tout!\n")

    async def close(self):
        print("\n🔒 [GeminiSession] Closing browser...")
        try:
            if self._browser_context:
                await self._browser_context.close()
        except:
            pass
        try:
            if self._playwright:
                await self._playwright.stop()
        except:
            pass
        self._is_ready = False
        print("✅ [GeminiSession] Done.\n")

    # ── TRAITEMENT D'UNE IMAGE ────────────────────────────────────────────
    # Appelé N fois. PAS de new_chat. Tout dans la même conversation.

    async def process_image(self, image_path: str) -> dict:
        if not self._is_ready:
            return {"success": False, "result_path": None, "error": "Session not ready"}

        prompt = random.choice(PROMPT_LIST)
        print(f"\n📝 Prompt: {prompt}")

        try:
            # Pause naturelle entre les messages — comme quelqu'un qui
            # prépare la prochaine image
            await human_pause(2.0, 4.0)

            # On "regarde" la page / la conversation avant d'agir
            await read_page_behavior(self._page)

            # Scroll en bas pour être au bas de la conversation
            await self._page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
            await human_pause(0.8, 1.5)

            # Coller l'image
            await self._paste_image(image_path)

            # Pause "on réfléchit à quoi écrire"
            await thinking_pause()

            # Taper le prompt
            await self._type_prompt(prompt)

            # Pause "on relit avant d'envoyer"
            await human_pause(0.8, 2.0)

            # Envoyer
            await self._send()

            # On attend — comportements idle pendant la génération
            print("  ⏳ Waiting for Gemini to generate...")
            await idle_behavior(self._page)
            await human_pause(4.0, 7.0)
            await idle_behavior(self._page)

            # Scroll en bas pour "voir" la réponse
            print("  📜 Scrolling to see response...")
            await self._page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
            await human_pause(1.0, 2.5)

            # On "lit" la réponse
            await read_page_behavior(self._page)

            # Chercher la NOUVELLE image (pas les anciennes)
            result_path = await self._wait_for_new_image()

            if result_path:
                print(f"✅ Success → {result_path}")
                return {"success": True, "result_path": result_path, "error": None}
            else:
                print("❌ No new result image found")
                return {"success": False, "result_path": None, "error": "No new result image found"}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"success": False, "result_path": None, "error": str(e)}

    # ── DÉTECTION D'IMAGE — LE TRUC CENTRAL ──────────────────────────────

    async def _snapshot_existing_images(self):
        """
        Parcourt toutes les images googleusercontent actuellement dans le DOM
        et les ajoute à _seen_image_srcs.
        On appelle ça avant chaque envoi pour "marquer" ce qui existe déjà.
        """
        images = await self._page.query_selector_all("img")
        for img in images:
            src = await img.get_attribute("src") or ""
            if "googleusercontent" in src:
                self._seen_image_srcs.add(src)
        print(f"    📸 Snapshot : {len(self._seen_image_srcs)} images déjà vues")

    async def _wait_for_new_image(self, max_wait: int = 120, poll_interval: int = 5) -> str | None:
        """
        Cherche une image googleusercontent qui N'ÉTAIT PAS dans _seen_image_srcs.
        Quand elle est trouvée, on la télécharge et on met à jour le set.
        """
        print("  🔍 Looking for NEW image...")
        start = time.time()

        while time.time() - start < max_wait:
            await asyncio.sleep(poll_interval)

            # Comportement idle pendant l'attente
            if random.random() < 0.35:
                await idle_behavior(self._page)

            images = await self._page.query_selector_all("img")
            new_candidates = []

            for img in images:
                src = await img.get_attribute("src") or ""

                # Filtres de base
                if not src or "googleusercontent" not in src or "avatar" in src:
                    continue

                # C'est une image on a déjà vue → skip
                if src in self._seen_image_srcs:
                    continue

                # Vérifie la taille (image générée = grande)
                box = await img.bounding_box()
                if box and box["width"] > 200 and box["height"] > 200:
                    new_candidates.append((img, src, box))

            if not new_candidates:
                elapsed = int(time.time() - start)
                print(f"    ⏳ No new image yet ({elapsed}s)...")
                continue

            # Prend la dernière nouvelle image trouvée
            target_img, target_src, target_box = new_candidates[-1]
            print("  ✅ New image found!")

            # On "la regarde" avec la souris avant de télécharger
            await move_mouse_naturally(
                self._page,
                target_box["x"] + target_box["width"] / 2,
                target_box["y"] + target_box["height"] / 2,
            )
            await human_pause(1.0, 2.5)

            # Télécharger
            try:
                ext = "jpg"
                if ".png" in target_src or "format=png" in target_src:
                    ext = "png"
                elif "webp" in target_src:
                    ext = "webp"

                filename = os.path.join(DOWNLOADS_DIR, f"result_{int(time.time())}.{ext}")
                response = await self._page.request.get(target_src)
                img_bytes = await response.body()

                with open(filename, "wb") as f:
                    f.write(img_bytes)

                print(f"  💾 Saved → {filename} ({len(img_bytes)} bytes)")

                # IMPORTANT : marquer cette image comme vue
                self._seen_image_srcs.add(target_src)

                # Pause après — "on vérifie le résultat"
                await human_pause(1.0, 2.0)
                return filename

            except Exception as e:
                print(f"  ⚠️  Download error: {e}")
                # On marque quand même comme vue pour ne pas reessayer
                self._seen_image_srcs.add(target_src)

        # Timeout
        print("  ⏱️  Timeout — no new image appeared")
        try:
            await self._page.screenshot(path="/data/debug_timeout.png", full_page=True)
        except:
            pass
        return None

    # ── HELPERS ───────────────────────────────────────────────────────────

    async def _dismiss_popups(self):
        try:
            btn = await self._page.wait_for_selector('button:has-text("Not now")', timeout=3_000)
            if btn:
                await click_naturally(self._page, btn)
                await human_pause(0.5, 1.5)
                print("  ✖ Dismissed popup")
        except:
            pass

    async def _wait_for_login(self):
        if "gemini.google.com" in self._page.url:
            print("✅ Already logged in")
            return

        print("\n" + "=" * 60)
        print("🔐  LOGIN REQUIRED — connectez-vous dans la fenêtre")
        print("    Vous avez 10 MINUTES.")
        print("=" * 60 + "\n")

        for _ in range(200):  # 200 × 3s = 10 min
            await asyncio.sleep(3)
            if "gemini.google.com" in self._page.url:
                print("✅ Login detected!")
                await asyncio.sleep(5)
                return
        raise TimeoutError("Login timeout after 10 minutes.")

    async def _wait_for_input(self, timeout_ms: int = 30_000):
        selectors = [
            'div[contenteditable="true"]',
            'div[role="textbox"]',
            'textarea',
        ]
        for sel in selectors:
            try:
                el = await self._page.wait_for_selector(sel, timeout=timeout_ms, state="visible")
                if el:
                    print(f"  ✅ Input trouvé : {sel}")
                    return el
            except:
                continue
        raise TimeoutError("Input field not found.")

    async def _paste_image(self, image_path: str):
        print(f"  📎 Encoding {os.path.basename(image_path)}...")

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        mime = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mime = "image/png"
        elif image_path.lower().endswith(".webp"):
            mime = "image/webp"

        # Écriture clipboard via JS
        js = f"""
        async () => {{
            const resp  = await fetch("data:{mime};base64,{b64}");
            const blob  = await resp.blob();
            const bmp   = await createImageBitmap(blob);
            const canvas = document.createElement('canvas');
            canvas.width  = bmp.width;
            canvas.height = bmp.height;
            canvas.getContext('2d').drawImage(bmp, 0, 0);
            const png = await new Promise(r => canvas.toBlob(r, 'image/png'));
            await navigator.clipboard.write([new ClipboardItem({{'image/png': png}})]);
            return "ok";
        }}
        """
        result = await self._page.evaluate(js)
        if result != "ok":
            raise RuntimeError(f"Clipboard write failed: {result}")

        # Click naturel sur l'input
        input_el = await self._wait_for_input(timeout_ms=10_000)
        await click_naturally(self._page, input_el)
        await human_pause(0.3, 0.8)

        # Ctrl+V
        print("  📋 Pasting (Ctrl+V)...")
        await self._page.keyboard.press("Control+V")
        await human_pause(2.0, 4.0)
        print("  ✅ Image pasted")

        # Snapshot avant d'envoyer — marque les images actuelles comme "déjà vues"
        await self._snapshot_existing_images()

    async def _type_prompt(self, prompt: str):
        print("  ⌨️  Typing prompt...")
        input_el = await self._wait_for_input(timeout_ms=10_000)
        await click_naturally(self._page, input_el)
        await human_pause(0.3, 0.7)

        base_speed = random.uniform(0.04, 0.14)
        words = prompt.split(" ")

        for word_idx, word in enumerate(words):
            for char in word:
                await input_el.type(char)
                await asyncio.sleep(base_speed + random.uniform(0, 0.07))

            if word_idx < len(words) - 1:
                await input_el.type(" ")
                await asyncio.sleep(random.uniform(0.1, 0.35))
                # 10% de chance de pause "réflexion" entre les mots
                if random.random() < 0.10:
                    await human_pause(0.5, 1.5)

        print("  ✅ Prompt typed")

    async def _send(self):
        print("  📤 Sending...")
        # Petit mouvement de souris avant Enter
        await move_mouse_naturally(self._page, random.randint(300, 900), random.randint(400, 600), steps=8)
        await human_pause(0.2, 0.5)
        await self._page.keyboard.press("Enter")
        await human_pause(1.0, 2.0)