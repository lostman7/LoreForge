import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Mocking the backend
        await page.route("**/config", lambda route: route.fulfill(status=200, body='{"ai": {"backend": "ollama"}, "tts": {"qwen3_model_size": "0.6B"}, "apis": {}}', content_type="application/json"))
        await page.route("**/presets", lambda route: route.fulfill(status=200, body='[]', content_type="application/json"))
        await page.route("**/persona", lambda route: route.fulfill(status=200, body='{"name": "Player"}', content_type="application/json"))
        await page.route("**/ai/models", lambda route: route.fulfill(status=200, body='["llama3.2:3b", "mistral"]', content_type="application/json"))

        await page.goto(f"file://{os.getcwd()}/index.html")

        # Click enter
        await page.click("#enter-sign")

        # Click settings button
        config_btn = page.locator("#config-btn")
        await config_btn.click()

        # Check if modal is visible
        modal = page.locator("#config-modal")
        is_visible = await modal.is_visible()
        print(f"Modal visible: {is_visible}")

        # Check z-index
        z_index = await modal.evaluate("el => getComputedStyle(document.getElementById('modal-overlay')).zIndex")
        print(f"Modal Overlay z-index: {z_index}")

        # Check if AI models are loaded
        model_select = page.locator("#model-select")
        # Wait for models to load (it's async in renderer.js)
        await asyncio.sleep(1)
        options_count = await model_select.locator("option").count()
        print(f"AI Model options count: {options_count}")

        # Select a model
        await model_select.select_option("mistral")
        selected_val = await model_select.input_value()
        print(f"Selected AI model: {selected_val}")

        # Check TTS model size
        tts_select = page.locator("#tts-model-size")
        await tts_select.select_option("1.6B")
        selected_tts = await tts_select.input_value()
        print(f"Selected TTS model size: {selected_tts}")

        # Take screenshot
        await page.screenshot(path="/home/jules/verification/settings_modal.png")

        await browser.close()

asyncio.run(run())
