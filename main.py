import asyncio
import os
import flet as ft
from pyrogram import Client

# --- GİZLİ LİSANS LİSTELERİ (Kullanıcı bunları asla göremez) ---
_MONTHLY_KEYS = [
    "DRECLIPSE-M1-2026", "DRECLIPSE-M2-2026", "DRECLIPSE-M3-2026", 
    "DRECLIPSE-M4-2026", "DRECLIPSE-M5-2026", "DRECLIPSE-M6-2026", 
    "DRECLIPSE-M7-2026", "DRECLIPSE-M8-2026", "DRECLIPSE-M9-2026", 
    "DRECLIPSE-M10-2026", "DRECLIPSE-M11-2026", "DRECLIPSE-M12-2026", 
    "DRECLIPSE-M13-2026", "DRECLIPSE-M14-2026", "DRECLIPSE-M15-2026"
]

_LIFETIME_KEYS = [
    "DRECLIPSE-LIFE-01", "DRECLIPSE-LIFE-02", "DRECLIPSE-LIFE-03", 
    "DRECLIPSE-LIFE-04", "DRECLIPSE-LIFE-05"
]

# Telegram API Bilgileri (Kendi API ID ve Hash değerini buraya yazabilirsin)
API_ID = 1234567  
API_HASH = "your_api_hash_here" 

app_client = None

def main(page: ft.Page):
    page.title = "Dreclipse Core - Pro"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 750

    # 1. ADIM: TELEGRAM GİRİŞ EKRANI
    phone_input = ft.TextField(label="Telefon Numarası (+90...)", width=300)
    code_input = ft.TextField(label="Telegram Kod", width=300, password=True, visible=False)
    password_input = ft.TextField(label="2 Adımlı Doğrulama (Varsa)", width=300, password=True, visible=False)
    
    status_text = ft.Text("", color=ft.colors.RED)
    
    # 2. ADIM: KEY EKRANI (Sadece "KEY GİRİNİZ:" yazar)
    key_input = ft.TextField(label="KEY GİRİNİZ:", width=300, password=True)
    key_status = ft.Text("", color=ft.colors.RED)

    # 3. ADIM: ANA KONTROL PANELİ
    chat_dropdown = ft.Dropdown(label="Sohbet / Grup / Kanal Seç", width=300)
    msg_input = ft.TextField(label="Gönderilecek Mesaj", width=300, multiline=True)
    count_input = ft.TextField(label="Kaç Adet Gönderilsin?", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    delay_input = ft.TextField(label="Kaç Saniye Aralıkla? (Gecikme)", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    log_view = ft.ListView(expand=1, spacing=5, padding=10, auto_scroll=True)

    phone_hash_storage = {"phone_code_hash": None}

    def start_telegram_login(e):
        global app_client
        if not phone_input.value:
            status_text.value = "Lütfen telefon numarasını girin!"
            page.update()
            return
        
        try:
            session_name = "dreclipse_session"
            app_client = Client(session_name, api_id=API_ID, api_hash=API_HASH, in_memory=True)
            page.run_task(async_send_code, phone_input.value)
        except Exception as ex:
            status_text.value = f"Hata: {str(ex)}"
            page.update()

    async def async_send_code(phone):
        await app_client.connect()
        sent = await app_client.send_code(phone)
        phone_hash_storage["phone_code_hash"] = sent.phone_code_hash
        status_text.value = "Kod gönderildi! Lütfen Telegram'dan gelen kodu girin."
        code_input.visible = True
        verify_btn.visible = True
        send_code_btn.visible = False
        phone_input.disabled = True
        page.update()

    def verify_telegram_code(e):
        page.run_task(async_verify_code)

    async def async_verify_code(e=None):
        try:
            await app_client.sign_in(
                phone_input.value, 
                phone_hash_storage["phone_code_hash"], 
                code_input.value
            )
            show_key_screen()
        except Exception as ex:
            if "SessionPasswordNeeded" in str(ex):
                password_input.visible = True
                status_text.value = "2 Adımlı Doğrulama Şifrenizi Girin:"
                page.update()
            else:
                status_text.value = f"Giriş Başarısız: {str(ex)}"
                page.update()

    def show_key_screen():
        page.clean()
        page.add(
            ft.Text("Lisans Doğrulama", size=24, weight=ft.FontWeight.BOLD),
            ft.VerticalSpace(20),
            key_input,
            ft.VerticalSpace(10),
            ft.ElevatedButton("Onayla ve Başla", on_click=verify_key, color=ft.colors.WHITE, bgcolor=ft.colors.GREEN, width=300),
            key_status
        )

    def verify_key(e):
        user_key = key_input.value.strip()
        if user_key in _MONTHLY_KEYS or user_key in _LIFETIME_KEYS:
            show_main_panel()
        else:
            key_status.value = "Geçersiz Key!"
            page.update()

    def show_main_panel():
        page.clean()
        page.run_task(load_dialogs_async)
        
        page.add(
            ft.Text("Dreclipse Core - Kontrol Paneli", size=20, weight=ft.FontWeight.BOLD),
            ft.VerticalSpace(10),
            chat_dropdown,
            msg_input,
            count_input,
            delay_input,
            ft.VerticalSpace(10),
            ft.ElevatedButton("🚀 BOTU BAŞLAT", on_click=run_bot_task, color=ft.colors.WHITE, bgcolor=ft.colors.BLUE, width=300, height=50),
            ft.VerticalSpace(10),
            ft.Text("İşlem Logları:", weight=ft.FontWeight.BOLD),
            ft.Container(content=log_view, border=ft.border.all(1, ft.colors.GREY), border_radius=5, height=150, width=300)
        )

    async def load_dialogs_async():
        async for dialog in app_client.get_dialogs():
            chat_dropdown.options.append(ft.dropdown.Option(text=dialog.chat.title or dialog.chat.first_name, key=str(dialog.chat.id)))
        page.update()

    def run_bot_task(e):
        if not chat_dropdown.value or not msg_input.value or not count_input.value or not delay_input.value:
            log_view.controls.append(ft.Text("Lütfen tüm alanları doldurun!", color=ft.colors.RED))
            page.update()
            return
        
        page.run_task(execute_spam_logic, int(chat_dropdown.value), msg_input.value, int(count_input.value), int(delay_input.value))

    async def execute_spam_logic(chat_id, message, count, delay):
        log_view.controls.append(ft.Text(f"Bot başlatıldı. Toplam {count} mesaj gönderilecek...", color=ft.colors.GREEN))
        page.update()
        
        for i in range(1, count + 1):
            try:
                await app_client.send_message(chat_id, message)
                log_view.controls.append(ft.Text(f"[{i}/{count}] Mesaj başarıyla gönderildi."))
                page.update()
                await asyncio.sleep(delay)
            except Exception as ex:
                log_view.controls.append(ft.Text(f"Hata: {str(ex)}", color=ft.colors.RED))
                page.update()
                break
        
        log_view.controls.append(ft.Text("İşlem tamamlandı!", color=ft.colors.BLUE))
        page.update()

    verify_btn = ft.ElevatedButton("Kodu Doğrula", on_click=verify_telegram_code, visible=False)
    send_code_btn = ft.ElevatedButton("Kod Gönder", on_click=start_telegram_login)

    page.add(
        ft.Text("Dreclipse Core Giriş", size=22, weight=ft.FontWeight.BOLD),
        ft.VerticalSpace(20),
        phone_input,
        code_input,
        password_input,
        ft.VerticalSpace(10),
        send_code_btn,
        verify_btn,
        status_text
    )

ft.app(target=main)
