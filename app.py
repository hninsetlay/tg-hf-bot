import os, time, math, threading, logging, traceback
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from huggingface_hub import HfApi
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Configs
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
REPO_ID = os.environ.get("REPO_ID")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# Categories စာရင်း
CATEGORIES = [
    "ACDSee Photo Studio Ultimate", "Activator", "Adobe Acrobat Pro", "Adobe After Effects",
    "Adobe Animate", "Adobe Bridge", "Adobe Dimension", "Adobe Dreamweaver",
    "Adobe Illustrator", "Adobe InCopy", "Adobe InDesign", "Adobe Lightroom",
    "Adobe Media Encoder", "Adobe PageMaker", "Adobe Photoshop", "Adobe Premier Pro",
    "Adobe Premiere Elements", "Adobe Substance 3D Designer", "Adobe Substance 3D Modeler", "Adobe Substance 3D Painter",
    "Adobe Substance 3D Sampler", "Agisoft Metashape Pro", "Aiarty Image Enhancer", "AnyDesk",
    "AOMEI Backupper", "AOMEI Partition Assistant", "Auto CAD", "Bandicam",
    "Capture One", "CCleaner", "Clip Studio Paint EX", "CorelDRAW",
    "CyberLink AudioDirector Ultra", "CyberLink PhotoDirector Ultra", "CyberLink PowerDirector Ultimate", "DxO PhotoLab",
    "FL Studio", "Fox PDF Editor", "Internet Download Manager", "MiniTool Power Data Recovery",
    "MS-OFFICE", "O&O Defrag Professional", "PassFab Duplicate file delete", "PDF-XChange Editor Plus",
    "PDF-XChange PRO", "Perfectly Clear Workbench", "Photo Reducteur", "Photo Studio Ultimate",
    "PhotoScape X Pro", "Power ISO", "Reaconverter Pro", "Reg Organizer",
    "Resetter", "Revo Registry Cleaner", "Revo Uninstalle Pro", "SketchUp Pro",
    "Stellar Data Recovery Pro", "Teamviewer", "VueScan", "Win RAR",
    "Wondershare PDFelement", "wondershare Uniconverter"
]

app = Client("hf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=100)
api = HfApi()
user_data = {}

def run_health():
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Alive")
        def log_message(self, format, *args):
            pass  # log မထုတ်အောင် ပိတ်ထားတယ်

    # Render က PORT environment variable ကို ပေးတယ်၊ မရှိရင် 7860 ကို သုံးတယ်
    port = int(os.environ.get("PORT", 7860))
    HTTPServer(('0.0.0.0', port), H).serve_forever()

def humanbytes(size):
    if not size: return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

async def progress_bar(current, total, status_msg, start_time, fname, mid):
    if mid in user_data and user_data[mid].get("cancelled", False):
        raise Exception("USER_CANCELLED")

    if time.time() - getattr(progress_bar, "last_update", 0) < 4: return
    progress_bar.last_update = time.time()
    
    perc = current * 100 / total
    bar = "🟩" * int(perc / 10) + "⬜" * (10 - int(perc / 10))
    speed = current / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
    
    text = (f"⚡️ **TechNexus Myanmar**\n📄 `{fname}`\n\n"
            f"┌ {bar} {perc:.1f}%\n"
            f"├ 🚀 Speed: {humanbytes(speed)}/s\n"
            f"└ 📦 {humanbytes(current)} / {humanbytes(total)}")
    
    try:
        await status_msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🛑 Cancel", callback_data=f"no_{mid}")
        ]]))
    except: pass

@app.on_message((filters.document | filters.video | filters.audio) & filters.user(ADMIN_ID))
async def on_file(client, message):
    mid = str(message.id)
    user_data[mid] = {"m": message, "step": "select_category", "cancelled": False}
    
    buttons = []
    for i in range(0, len(CATEGORIES), 2):
        row = []
        for cat in CATEGORIES[i:i+2]:
            row.append(InlineKeyboardButton(f"📁 {cat}", callback_data=f"idx_{mid}_{i + CATEGORIES[i:i+2].index(cat)}"))
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton("➕ စာရိုက်ပြီး အသစ်ထည့်မည်", callback_data=f"custom_{mid}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data=f"no_{mid}")])
    
    await message.reply_text("📂 **သိမ်းဆည်းမည့် Category (Folder) ကို ရွေးချယ်ပေးပါ...**", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.text & filters.user(ADMIN_ID))
async def on_custom_text(client, message):
    for mid in list(user_data.keys()):
        if user_data[mid].get("step") == "typing_custom":
            folder = message.text.replace(" ", "_")
            user_data[mid]["folder"] = folder
            user_data[mid]["step"] = "confirm"
            
            await message.reply_text(f"📁 Folder အသစ် `{folder}` ထဲ တင်ရန် အတည်ပြုပါသလား?", 
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Confirm & Start", callback_data=f"go_{mid}"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"no_{mid}")
                ]]))
            return

@app.on_callback_query()
async def on_cb(client, cb: CallbackQuery):
    if cb.data.startswith("idx_"):
        _, mid, idx = cb.data.split("_", 2)
        if mid not in user_data: 
            return await cb.answer("❌ Session သက်တမ်းကုန်သွားပါပြီ။ ဖိုင်ပြန်ပို့ပေးပါ။", show_alert=True)
            
        folder = CATEGORIES[int(idx)].replace(" ", "_")
        user_data[mid]["folder"] = folder
        user_data[mid]["step"] = "confirm"
        
        await cb.message.edit_text(f"📁 Folder `{folder}` ထဲ တင်ရန် အတည်ပြုပါသလား?", 
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Confirm & Start", callback_data=f"go_{mid}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"no_{mid}")
            ]]))
            
    elif cb.data.startswith("custom_"):
        mid = cb.data.replace("custom_", "")
        if mid not in user_data: return await cb.answer("❌ Session သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)
        
        user_data[mid]["step"] = "typing_custom"
        await cb.message.edit_text("✍️ **သိမ်းဆည်းလိုသည့် Folder/Category အမည်ကို စာရိုက်ပြီး ပို့ပေးပါ...**")

    elif cb.data.startswith("go_"):
        mid = cb.data.replace("go_", "")
        if mid not in user_data: return await cb.answer("❌ Session သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)
        
        data = user_data[mid]
        msg = data["m"]
        folder = data["folder"]
        path = None
        
        try:
            file_obj = getattr(msg, msg.media.value)
            fname = file_obj.file_name if hasattr(file_obj, "file_name") else "uploaded_file"
            
            status_msg = await cb.message.edit_text(f"⏳ **{fname}** ကို စတင်နေပါပြီ...")
            
            start_time = time.time()
            path = await msg.download(progress=progress_bar, progress_args=(status_msg, start_time, fname, mid))
            
            if mid in user_data and user_data[mid].get("cancelled", False):
                if path and os.path.exists(path): os.remove(path)
                return

            if path:
                await status_msg.edit_text(f"🚀 **{fname}** ကို Hugging Face သို့ တင်နေပါသည်...\n📂 Folder: `{folder}`")
                api.upload_file(
                    path_or_fileobj=path,
                    path_in_repo=f"{folder}/{fname}",
                    repo_id=REPO_ID,
                    repo_type="dataset",
                    token=HF_TOKEN
                )
                duration = int(time.time() - start_time)
                await status_msg.edit_text(f"✅ **အောင်မြင်စွာ တင်ပြီးပါပြီ!**\n📁 Folder: `{folder}`\n📄 File: `{fname}`\n⏱ ကြာချိန်: `{duration} s`")
            
        except Exception as e:
            if str(e) == "USER_CANCELLED":
                logger.info(f"Session {mid} was cancelled by user.")
            else:
                logger.error(f"Error: {traceback.format_exc()}")
                await cb.message.edit_text(f"❌ အမှားတက်သွားပါသည်: {str(e)}")
        
        finally:
            if path and os.path.exists(path): os.remove(path)
            if mid in user_data: del user_data[mid]

    elif cb.data.startswith("no_"):
        mid = cb.data.replace("no_", "")
        await cb.message.edit_text("❌ ဖျက်သိမ်းလိုက်ပါပြီ။")
        if mid in user_data:
            user_data[mid]["cancelled"] = True

if __name__ == "__main__":
    threading.Thread(target=run_health, daemon=True).start()
    app.run()