from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import time

TOKEN = "8739106463:AAE_CPDREovssnUPDTcJhyv2xJ_HseSB7ZQ"

users = {} # uid: {gender, looking, name}
waiting = [] # list of uid
pairs = {}
last_msg = {}
spam_count = {}
reports = {}

GENDER_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🙋‍♂️ Cowo", callback_data="gender_cowo"),
     InlineKeyboardButton("🙋‍♀️ Cewe", callback_data="gender_cewe")]
])
FILTER_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("👫 Semua", callback_data="filter_all"),
     InlineKeyboardButton("🙋‍♂️ Cowo aja", callback_data="filter_cowo"),
     InlineKeyboardButton("🙋‍♀️ Cewe aja", callback_data="filter_cewe")]
])

def get_user(uid, name="User"):
    if uid not in users:
        users[uid] = {"gender": None, "looking": "all", "name": name}
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    if not u["gender"]:
        await update.message.reply_text("Dulu bro, lu cowo apa cewe?", reply_markup=GENDER_KB)
    else:
        await update.message.reply_text(f"Bot ON bro! Gender lu: {u['gender']}\n/search = cari partner\n/next = ganti partner\n/filter = ganti filter\n/report = laporin partner toxic", reply_markup=FILTER_KB)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = get_user(uid)
    if q.data.startswith("gender_"):
        g = q.data.split("_")[1]
        u["gender"] = g
        await q.edit_message_text(f"Oke lu {g}! Sekarang lu mau cari apa?\nPilih filter:", reply_markup=FILTER_KB)
    elif q.data.startswith("filter_"):
        f = q.data.split("_")[1]
        u["looking"] = f
        await q.edit_message_text(f"Filter diset ke: {f}\nLangsung /search bro buat mulai!")

async def set_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Mau cari partner apa?", reply_markup=FILTER_KB)

def find_partner(uid):
    u = get_user(uid)
    for i, pid in enumerate(waiting):
        if pid == uid: continue
        p = get_user(pid)
        # cocok filter
        if u["looking"]!= "all" and p["gender"]!= u["looking"]: continue
        if p["looking"]!= "all" and u["gender"]!= p["looking"]: continue
        waiting.pop(i)
        return pid
    return None

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in pairs:
        await update.message.reply_text("Lu lagi chat, /stop dulu")
        return
    u = get_user(uid, update.effective_user.first_name)
    if not u["gender"]:
        await update.message.reply_text("Set gender dulu /start", reply_markup=GENDER_KB)
        return
    pid = find_partner(uid)
    if pid:
        pairs[uid]=pid; pairs[pid]=uid
        await context.bot.send_message(uid, f"Ketemu! Partner {get_user(pid)['gender']} - Chat aja! /next buat ganti /report kalo toxic")
        await context.bot.send_message(pid, f"Ketemu! Partner {u['gender']} - Chat aja! /next buat ganti /report kalo toxic")
    else:
        if uid not in waiting:
            waiting.append(uid)
        await update.message.reply_text(f"Nyari partner {u['looking']}... Sabar ya")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in pairs:
        pid = pairs.pop(uid); pairs.pop(pid, None)
        await update.message.reply_text("Udah di stop. /search lagi buat cari baru")
        try: await context.bot.send_message(pid, "Partner cabut (pake /next). /search lagi")
        except: pass
    elif uid in waiting:
        waiting.remove(uid)
        await update.message.reply_text("Batal nyari")
    else:
        await update.message.reply_text("Lu gak lagi nyari/chat")

async def next_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    await search(update, context)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in pairs:
        await update.message.reply_text("Lu gak lagi chat siapa2")
        return
    pid = pairs[uid]
    reports[pid] = reports.get(pid, 0) + 1
    await update.message.reply_text("Oke gua catet laporannya. Partner bakal gua putusin")
    await stop(update, context)
    if reports[pid] >= 3:
        await update.message.reply_text(f"User {pid} udah 3x di report, auto ban sementara")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    now = time.time()
    # anti spam
    if now - last_msg.get(uid, 0) < 0.7:
        spam_count[uid] = spam_count.get(uid,0)+1
        if spam_count[uid] > 5:
            await update.message.reply_text("Jangan spam bro! Slow dikit")
            return
    else:
        spam_count[uid]=0
    last_msg[uid]=now

    if uid in pairs:
        try:
            await context.bot.copy_message(pairs[uid], uid, update.message.id)
        except:
            pass
    else:
        await update.message.reply_text("Lu belum /search bro")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("search", search))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("next", next_cmd))
app.add_handler(CommandHandler("filter", set_filter))
app.add_handler(CommandHandler("report", report))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, chat))
print("Bot PRO Baleendah jalan!")
app.run_polling()
