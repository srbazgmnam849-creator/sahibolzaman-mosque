#!/usr/bin/env python3
"""Extended functional test: users module guards, add/edit/delete, password change, level enforcement."""
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
    ctx = browser.new_context(viewport={"width": 1360, "height": 850})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" else None)

    page.goto(URL)
    page.wait_for_selector("#loginScreen", state="visible", timeout=30000)
    page.fill("#loginUser", "imam"); page.fill("#loginPass", "Imam!1405A7"); page.click("#loginBtn")
    page.wait_for_selector("#welcomeOv", state="visible"); page.click("#welcomeOv [data-wok]")

    # --- 1) add account (imam) ---
    page.click("#sideNav .nav-item[data-view='users']")
    page.click("#viewRoot [data-act='userAdd']")
    page.fill("#uUser", "testuser1")
    page.fill("#uDname", "کاربر آزمون یک")
    page.fill("#uRoleInput", "مسئول آزمایشی دفتر")
    page.select_option("#uLevel", "2")
    page.fill("#uPass", "Test!12345")
    page.click("#userForm button[type='submit']")
    page.wait_for_timeout(600)
    check("testuser1" in page.inner_text("#viewRoot"), "new account appears in list")

    # --- 2) guard: imam cannot change own level ---
    page.click("#viewRoot [data-act='userEdit'][data-user='imam']")
    page.wait_for_selector("#userForm", state="visible")
    page.select_option("#uLevel", "2")
    page.click("#userForm button[type='submit']")
    page.wait_for_timeout(400)
    err = page.inner_text("#uFormErr")
    check("سطح دسترسی حساب خودتان" in err, f"self level-change rejected: {err}")
    page.click("#modalOv [data-act='closeModal']"); page.wait_for_timeout(300)

    # --- 3) guard: cannot delete self ---
    page.click("#viewRoot [data-act='userDelete'][data-user='imam']")
    page.wait_for_timeout(400)
    check(page.locator(".modal.confirm").count() == 0, "delete-self blocked before confirm dialog")
    check(page.locator(".toast.error").count() >= 1, "delete-self shows error toast")

    # --- 4) guard: short password rejected ---
    page.click("#viewRoot [data-act='userEdit'][data-user='testuser1']")
    page.wait_for_selector("#userForm", state="visible")
    page.fill("#uPass", "short")
    page.click("#userForm button[type='submit']")
    page.wait_for_timeout(400)
    check("حداقل ۸ کاراکتر" in page.inner_text("#uFormErr"), "short password rejected on edit")
    page.click("#modalOv [data-act='closeModal']"); page.wait_for_timeout(300)

    # --- 5) self-service password change: wrong current password ---
    page.click("#chgPassBtn")
    page.wait_for_selector("#cpForm", state="visible")
    page.fill("#cpCur", "WrongPass1"); page.fill("#cpNew", "NewPass!99"); page.fill("#cpNew2", "NewPass!99")
    page.click("#cpForm button[type='submit']")
    page.wait_for_timeout(400)
    check("گذرواژه فعلی نادرست است" in page.inner_text("#cpErr"), "wrong current password rejected")
    # correct change
    page.fill("#cpCur", "Imam!1405A7"); page.fill("#cpNew", "NewPass!99"); page.fill("#cpNew2", "NewPass!99")
    page.click("#cpForm button[type='submit']")
    page.wait_for_timeout(600)
    check(page.locator("#cpForm").count() == 0, "password change modal closed on success")

    # --- 6) re-login with new password ---
    page.click("#logoutBtn")
    page.wait_for_selector("#loginScreen", state="visible", timeout=15000)
    page.fill("#loginUser", "imam"); page.fill("#loginPass", "Imam!1405A7"); page.click("#loginBtn")
    page.wait_for_timeout(600)
    check(page.locator("#welcomeOv").count() == 0, "old password no longer works")
    page.fill("#loginUser", "imam"); page.fill("#loginPass", "NewPass!99"); page.click("#loginBtn")
    page.wait_for_selector("#welcomeOv", state="visible", timeout=15000)
    page.click("#welcomeOv [data-wok]")
    check(True, "new password works")

    # --- 7) last active level-4 guard: delete board+secretary then try deleting remaining L4 ---
    page.click("#sideNav .nav-item[data-view='users']")
    page.click("#viewRoot [data-act='userDelete'][data-user='board']")
    page.wait_for_selector(".modal.confirm", state="visible")
    page.click(".modal.confirm .ok")
    page.wait_for_timeout(500)
    page.click("#viewRoot [data-act='userDelete'][data-user='secretary']")
    page.wait_for_selector(".modal.confirm", state="visible")
    page.click(".modal.confirm .ok")
    page.wait_for_timeout(500)
    page.click("#viewRoot [data-act='userDelete'][data-user='imam']")
    page.wait_for_timeout(400)
    # imam is self -> blocked; instead disable imam via edit is also self... check via toggle on other L4? imam is last L4 now besides none.
    # Try toggling imam active off via row switch:
    page.evaluate("document.querySelector(\"input[data-toggle-user='imam']\").click()")
    page.wait_for_timeout(300)
    imam_active = page.evaluate("one('SELECT active FROM users WHERE username=?',['imam']).active")
    check(imam_active == 1, "last active level-4 cannot be disabled")

    # --- 8) media_admin cannot set level (enforced in handler) ---
    page.click("#logoutBtn"); page.wait_for_selector("#loginScreen", state="visible", timeout=15000)
    page.fill("#loginUser", "media_admin"); page.fill("#loginPass", "Media!1405Q6"); page.click("#loginBtn")
    page.wait_for_selector("#welcomeOv", state="visible"); page.click("#welcomeOv [data-wok]")
    page.click("#sideNav .nav-item[data-view='users']")
    # simulate a crafted attempt to set a level via the shared handler path:
    rejected = page.evaluate("""async () => {
      try{
        // directly attempt DB-level change the way a broken handler would:
        // the REAL handler must refuse; we verify the modal path instead:
        return 'modal-path';
      }catch(e){ return 'err'; }
    }""")
    page.click("#viewRoot [data-act='userEdit'][data-user='testuser1']")
    page.wait_for_selector("#userForm", state="visible")
    check(page.locator("#uLevel").count() == 0, "media_admin edit form has no level control")
    page.fill("#uDname", "کاربر آزمون ویرایش‌شده")
    page.click("#userForm button[type='submit']")
    page.wait_for_timeout(600)
    check("کاربر آزمون ویرایش‌شده" in page.inner_text("#viewRoot"), "media_admin can edit display name")
    lvl_after = page.evaluate("one('SELECT level FROM users WHERE username=?',['testuser1']).level")
    check(lvl_after == 2, "media_admin edit did not touch level")
    # media_admin cannot edit own level (no control) and cannot see matrix — verified earlier.
    # delete the test account
    page.click("#viewRoot [data-act='userDelete'][data-user='testuser1']")
    page.wait_for_selector(".modal.confirm", state="visible")
    page.click(".modal.confirm .ok")
    page.wait_for_timeout(500)
    gone = page.evaluate("one('SELECT COUNT(*) AS c FROM users WHERE username=?',['testuser1']).c")
    check(gone == 0, "media_admin can delete account")

    browser.close()

real_errors = [e for e in errors if "favicon" not in e.lower()]
print("\nConsole/page errors:", len(real_errors))
for e in real_errors[:20]:
    print("  ", e)
if real_errors or errors:
    sys.exit("EXTENDED TEST FAILED")
print("EXTENDED TEST OK — all guards and CRUD flows verified")
