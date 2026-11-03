#!/usr/bin/env python3
"""Playwright smoke test for deploy/index.html (fully offline single file)."""
import sys
from playwright.sync_api import sync_playwright

URL = "file:///home/z/my-project/deploy/index.html"
errors = []

def check(cond, msg):
    print(("PASS: " if cond else "FAIL: ") + msg)
    if not cond:
        errors.append(msg)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1360, "height": 850})
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

    page.goto(URL)
    page.wait_for_selector("#loginScreen", state="visible", timeout=30000)
    check(True, "boot completed -> login screen visible")

    # --- login as imam ---
    page.fill("#loginUser", "imam")
    page.fill("#loginPass", "Imam!1405A7")
    page.click("#loginBtn")
    page.wait_for_selector("#welcomeOv", state="visible", timeout=15000)
    check(True, "welcome modal shown after login")
    body_txt = page.inner_text("#welcomeOv")
    check("خوش آمدید" in body_txt and "امام جماعت" in body_txt, "welcome modal has greeting + role")
    check(page.locator("#welcomeOv img").count() == 1, "welcome modal contains logo img")

    # dashboard rendered behind modal
    page.wait_for_selector("#appShell", state="visible", timeout=10000)
    check(True, "app shell visible (dashboard)")

    # --- close welcome modal via primary button ---
    page.click("#welcomeOv [data-wok]")
    page.wait_for_selector("#welcomeOv", state="detached", timeout=5000)
    check(True, "welcome modal closed via «متوجه شدم»")

    # --- notifications panel quick check (imam) ---
    page.click("#bellBtn")
    page.wait_for_selector("#notifPanel", state="visible", timeout=5000)
    check(True, "notifications panel opens")
    if page.locator("#notifPanel [data-act='markAllRead']").count():
        page.click("#notifPanel [data-act='markAllRead']")
        page.wait_for_timeout(400)
        badge_hidden = page.evaluate("document.getElementById('notifBadge').hidden")
        check(badge_hidden, "mark-all-read clears badge")
    page.keyboard.press("Escape")
    check(page.evaluate("document.getElementById('notifPanel').hidden"), "Escape closes notifications panel")

    # --- open users module (imam) ---
    page.click("#sideNav .nav-item[data-view='users']")
    page.wait_for_timeout(600)
    h2 = page.inner_text("#viewRoot .page-head h2")
    check("مدیریت کاربران و دسترسی‌ها" in h2, f"users module head (imam): {h2}")
    check(page.locator("#viewRoot [data-act='userAdd']").count() == 1, "imam: add-account button present")
    check(page.locator("#viewRoot [data-act='userEdit']").count() >= 5, "imam: edit buttons present")
    check(page.locator("#viewRoot [data-act='userDelete']").count() >= 5, "imam: delete buttons present")
    check("ماتریس سطوح دسترسی" in page.inner_text("#viewRoot"), "imam: permission matrix kept")
    # imam add modal contains level select
    page.click("#viewRoot [data-act='userAdd']")
    page.wait_for_selector("#userForm", state="visible")
    check(page.locator("#uLevel").count() == 1, "imam: add form has permission-level select")
    page.click("#modalOv [data-act='closeModal']")
    page.wait_for_timeout(300)
    # self-service password change entry
    page.click("#chgPassBtn")
    page.wait_for_selector("#cpForm", state="visible")
    check(True, "sidebar «تغییر گذرواژه» opens password form")
    page.click("#modalOv [data-act='closeModal']")
    page.wait_for_timeout(300)
    page.screenshot(path="/home/z/my-project/deploy/_assets/test-imam.png", full_page=False)
    check(True, "screenshot saved: test-imam.png")

    # --- logout ---
    page.click("#logoutBtn")
    page.wait_for_selector("#loginScreen", state="visible", timeout=15000)
    check(True, "logout returns to login screen")

    # --- login as media_admin, dismiss welcome via Escape ---
    page.fill("#loginUser", "media_admin")
    page.fill("#loginPass", "Media!1405Q6")
    page.click("#loginBtn")
    page.wait_for_selector("#welcomeOv", state="visible", timeout=15000)
    page.keyboard.press("Escape")
    page.wait_for_selector("#welcomeOv", state="detached", timeout=5000)
    check(True, "media_admin welcome modal closes via Escape")

    # --- users module for media_admin ---
    page.wait_for_selector("#sideNav .nav-item[data-view='users']", timeout=10000)
    check(True, "media_admin sees users nav entry")
    page.click("#sideNav .nav-item[data-view='users']")
    page.wait_for_timeout(600)
    banner = page.inner_text("#viewRoot")
    check("این پنل فقط مدیریت حساب‌ها را انجام می‌دهد" in banner, "media_admin: restriction banner shown")
    check(page.locator("#viewRoot [data-act='userAdd']").count() == 1, "media_admin: account management available")
    check("ماتریس سطوح دسترسی" not in banner, "media_admin: permission matrix hidden")
    page.click("#viewRoot [data-act='userAdd']")
    page.wait_for_selector("#userForm", state="visible")
    check(page.locator("#uLevel").count() == 0, "media_admin: add form has NO permission-level select")
    page.click("#modalOv [data-act='closeModal']")
    page.wait_for_timeout(300)
    page.screenshot(path="/home/z/my-project/deploy/_assets/test-media.png", full_page=False)
    check(True, "screenshot saved: test-media.png")

    browser.close()

real_errors = [e for e in errors if "favicon" not in e.lower()]
print("\nConsole/page errors:", len(real_errors))
for e in real_errors[:20]:
    print("  ", e)
if real_errors:
    sys.exit("SMOKE TEST FAILED — console errors found")
if errors:
    sys.exit("SMOKE TEST FAILED — assertion errors: " + "; ".join(errors))
print("SMOKE TEST OK — all assertions passed, no console errors")
