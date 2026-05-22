import os
from datetime import datetime

import discord
import anthropic

# ============================================================
# CONFIG
# ============================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Optional webhook variables. Aman dibiarkan kosong.
WEBHOOKS = {
    "live-report": os.getenv("WH_LIVE_REPORT"),
    "sales-report": os.getenv("WH_SALES_REPORT"),
    "campaign-plan": os.getenv("WH_CAMPAIGN_PLAN"),
    "campaign-ideas": os.getenv("WH_CAMPAIGN_IDEAS"),
    "general-chat": os.getenv("WH_GENERAL_CHAT"),
    "weekly-plan": os.getenv("WH_WEEKLY_PLAN"),
}

SYSTEM_PROMPT = """
Kamu adalah Pandara Marketing Bot, AI assistant internal untuk Marketing Pandara Group Indonesia.

Konteks bisnis:
- Pandara menaungi / mendistribusikan brand: Monbento, Marshmallow, JollyFun, Peugeot Saveurs, Remy Pan, Kvetna.
- Channel: Shopee, TikTok Shop, Tokopedia, Instagram, offline store, consignment, B2B/corporate gift.
- Tim memakai Discord untuk campaign, content, reporting, finance, reminder, weekly plan, B2B, UGC, Threads, dan design feedback.

Gaya jawaban:
- Bahasa Indonesia, kecuali user minta English.
- Profesional, to the point, actionable, tidak mengawang.
- Prioritaskan output yang bisa langsung dipakai tim kecil.
- Pakai format rapi: heading, bullet, tabel sederhana jika perlu.
- Jangan terlalu panjang jika tidak perlu. Maksimalkan clarity.
- Untuk strategi, selalu pikirkan: objective, audience, offer, channel, KPI, execution risk, next step.
- Untuk audit/review, jadilah critical strategist: sebutkan kelemahan, risiko gagal, bias asumsi, lalu berikan versi perbaikan.

Batasan:
- Jangan mengarang data angka jika user tidak memberi data.
- Jika data kurang, tetap berikan asumsi dan tulis asumsi secara jelas.
- Jangan minta user ulangi terlalu banyak; beri best effort.
""".strip()

# ============================================================
# VALIDATION
# ============================================================
if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN belum di-set di Railway Variables.")

if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY belum di-set di Railway Variables.")

# ============================================================
# CLIENTS
# ============================================================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================
# COMMAND DEFINITIONS
# ============================================================
COMMANDS = {
    "GENERAL": {
        "!help": "Tampilkan semua command",
        "!panduan": "Panduan cara pakai bot + contoh workflow",
        "!status": "Cek status bot, model Claude, dan webhook",
        "!tanya [pertanyaan]": "Tanya bebas soal marketing Pandara",
    },
    "CAMPAIGN": {
        "!ideas [topik]": "Generate ide campaign cepat",
        "!campaign-plan [brand/event/goal]": "Buat campaign plan lengkap",
        "!campaign-check [paste plan]": "Audit kelemahan campaign + improvement",
        "!campaign-report [data]": "Buat laporan campaign untuk owner",
        "!campaign-calendar [bulan/event]": "Buat kalender campaign bulanan",
    },
    "CONTENT": {
        "!brief [topik]": "Buat content brief lengkap",
        "!reels [produk/topik]": "Script Reels/TikTok 15-30 detik",
        "!caption [produk/topik]": "Caption IG/TikTok + hashtag",
        "!ugc [produk/brief]": "Brief UGC/KOL creator",
        "!threads [topik]": "Ide post Threads natural",
        "!review-content [paste konten]": "Audit caption/script/konten sebelum posting",
        "!design-feedback [brief/desain]": "Feedback untuk graphic designer",
        "!hook [produk/topik]": "Buat 20 hook konten pendek",
        "!story [produk/topik]": "Ide Instagram Story sequence",
        "!carousel [topik]": "Outline carousel edukasi/selling",
    },
    "LIVE & MARKETPLACE": {
        "!rekap-live [data]": "Rekap & analisis data live TikTok",
        "!live-script [produk]": "Script live selling produk",
        "!live-eval [data live]": "Evaluasi performa live",
        "!objection [produk/masalah]": "Jawaban objection customer",
        "!sku-push [data produk]": "Rekomendasi produk mana yang dipush",
    },
    "REPORTING": {
        "!analisis [data]": "Analisis data marketing umum",
        "!sales-eval [data sales]": "Analisis sales + action plan",
        "!store-report [data marketplace]": "Laporan performa toko marketplace",
        "!ads-report [data iklan]": "Analisis ads: ROAS, CTR, CVR, next action",
        "!weekly-report [data minggu ini]": "Buat weekly report untuk owner/team",
    },
    "PLANNING & OPS": {
        "!weekly-plan [goal]": "Weekly marketing plan",
        "!daily-task [prioritas]": "Task harian berdasarkan prioritas",
        "!meeting-summary [notes]": "Ubah notes meeting jadi action item",
        "!sop [proses]": "Buat SOP singkat untuk tim",
        "!priority [list task]": "Urutkan prioritas kerja",
    },
    "FINANCE": {
        "!harga-jual [modal/fee/margin]": "Hitung strategi harga jual marketplace",
        "!budget [campaign/budget/goal]": "Alokasi budget campaign",
        "!promo-math [harga/modal/promo]": "Cek apakah promo masih untung",
        "!margin-check [data]": "Audit margin dan red flag",
    },
    "B2B & CONSIGNMENT": {
        "!b2b [target]": "Pitch B2B general",
        "!b2b-pitch [target]": "Pitch B2B lebih lengkap",
        "!followup [target/status]": "Follow-up WA/email B2B",
        "!consignment [brand/target store]": "Pitch consignment",
        "!proposal [target/brand]": "Outline proposal kerja sama",
    },
}

PROMPTS = {
    "!tanya": """Jawab pertanyaan user sebagai marketing strategist Pandara. Beri jawaban konkret, realistis, dan actionable.\n\nPertanyaan:\n{args}""",

    "!ideas": """Buatkan 5 ide campaign kreatif untuk Pandara berdasarkan topik: {args}\n\nFormat setiap ide:\n1. Nama campaign\n2. Brand yang cocok\n3. Big idea\n4. Target audience\n5. Hook utama\n6. Platform eksekusi\n7. Konten yang dibuat\n8. KPI\n9. Risiko gagal\n10. Next step""",

    "!campaign-plan": """Buat campaign plan lengkap untuk: {args}\n\nFormat:\n- Campaign name\n- Background problem/opportunity\n- Objective utama\n- Target audience\n- Core insight\n- Big idea\n- Offer/promo\n- Channel plan: IG, TikTok, Shopee/TikTok Shop, offline/B2B jika relevan\n- Content pillar\n- 14-day timeline\n- Asset yang dibutuhkan\n- PIC yang disarankan\n- KPI utama\n- Risiko execution\n- Checklist launch""",

    "!campaign-check": """Audit campaign plan berikut sebagai critical strategist. Jangan terlalu sopan. Cari kelemahan real yang bisa bikin campaign gagal.\n\nCampaign/data:\n{args}\n\nFormat:\n1. Diagnosis singkat\n2. 5 kelemahan terbesar\n3. Asumsi yang belum terbukti\n4. Risiko execution\n5. Apa yang harus dipotong/disederhanakan\n6. Versi campaign yang lebih kuat\n7. Action list 24 jam berikutnya""",

    "!campaign-report": """Buat laporan campaign untuk owner dari data berikut:\n{args}\n\nFormat:\n- Executive summary\n- Objective campaign\n- Hasil utama\n- Metrik penting\n- Apa yang berhasil\n- Apa yang kurang\n- Insight customer/content\n- Rekomendasi next campaign\n- Action items""",

    "!campaign-calendar": """Buat kalender campaign bulanan berdasarkan input: {args}\n\nFormat tabel mingguan:\n- Week\n- Theme/event\n- Brand focus\n- Offer\n- Konten utama\n- Asset needed\n- KPI\n- Notes""",

    "!brief": """Buat content brief lengkap untuk tim konten Pandara.\n\nTopik: {args}\n\nSertakan:\n- Objective konten\n- Target audience\n- Platform & format\n- Hook 3 detik\n- Key message\n- Shot list\n- Text overlay\n- Voice over/script\n- CTA\n- Visual direction\n- Caption\n- Hashtag\n- Checklist sebelum upload""",

    "!reels": """Buat script Reels/TikTok 15-30 detik untuk: {args}\n\nFormat:\n- Objective\n- Hook 0-3 detik\n- Scene breakdown per detik\n- Shot list\n- Text overlay\n- Voice over\n- Sound/music direction\n- CTA\n- Caption pendek\n- 3 variasi hook alternatif""",

    "!caption": """Buat 5 caption untuk: {args}\n\nBuat variasi angle:\n1. Soft selling\n2. Lifestyle\n3. Problem-solution\n4. Premium/value\n5. Gen-Z casual\n\nSetiap caption berisi hook, body singkat, CTA, dan hashtag.""",

    "!ugc": """Buat brief UGC/KOL creator untuk: {args}\n\nFormat:\n- Campaign objective\n- Creator profile yang cocok\n- Do's and don'ts\n- Key talking points\n- Script direction\n- Mandatory shots\n- Hook options\n- CTA\n- Deliverables\n- Deadline format\n- Evaluation criteria""",

    "!threads": """Buat 15 ide post Threads untuk: {args}\n\nStyle: natural, ringan, relatable, bukan hard selling.\nFormat:\n- 5 post conversation starter\n- 5 post soft selling\n- 5 post edukasi/relatable\nTambahkan CTA komentar yang natural.""",

    "!review-content": """Audit konten berikut sebelum diposting:\n{args}\n\nFormat:\n1. Skor 1-10\n2. Hook: kuat/lemah dan kenapa\n3. Message clarity\n4. Apakah terlalu jualan?\n5. Apakah CTA jelas?\n6. Risiko performa rendah\n7. Revisi versi lebih kuat\n8. 3 alternatif hook""",

    "!design-feedback": """Berikan feedback desain untuk brief/deskripsi ini:\n{args}\n\nFormat:\n- First impression\n- Masalah visual hierarchy\n- Masalah copy/text\n- Masalah komposisi\n- Apakah cocok untuk ads/catalog/social?\n- Revisi yang harus dilakukan designer\n- Versi arahan final yang bisa dicopy ke designer""",

    "!hook": """Buat 20 hook pendek untuk konten: {args}\n\nBagi menjadi:\n- Problem hook\n- Curiosity hook\n- Benefit hook\n- Contrarian hook\n- Lifestyle hook""",

    "!story": """Buat Instagram Story sequence untuk: {args}\n\nFormat 5-8 slide:\n- Slide number\n- Visual\n- Text overlay\n- Sticker/poll/question jika perlu\n- CTA""",

    "!carousel": """Buat outline carousel untuk: {args}\n\nFormat:\n- Cover title\n- Slide 1-8 isi\n- Visual direction tiap slide\n- Caption\n- CTA""",

    "!rekap-live": """Analisis data live TikTok berikut:\n{args}\n\nFormat:\n1. Ringkasan performa\n2. Metrik yang bagus/buruk\n3. Root cause conversion rendah/tinggi\n4. Produk yang harus dipush\n5. Script improvement\n6. Action untuk live berikutnya""",

    "!live-script": """Buat script live selling untuk produk: {args}\n\nFormat:\n- Opening 30 detik\n- Product introduction\n- 5 selling points\n- Demo angle\n- Objection handling\n- Promo wording\n- Urgency tanpa hard selling berlebihan\n- Closing\n- 10 kalimat filler saat live sepi""",

    "!live-eval": """Evaluasi data live berikut:\n{args}\n\nFormat:\n- Diagnosis singkat\n- Masalah traffic\n- Masalah conversion\n- Masalah product selection\n- Masalah script/host\n- Eksperimen live berikutnya\n- Action priority""",

    "!objection": """Buat jawaban objection customer untuk: {args}\n\nFormat:\n- Objection utama\n- Jawaban singkat untuk chat\n- Jawaban live selling\n- Jawaban premium/value\n- Cara closing halus""",

    "!sku-push": """Dari data produk berikut, rekomendasikan SKU mana yang harus dipush dan kenapa:\n{args}\n\nFormat:\n- SKU prioritas 1-5\n- Alasan\n- Channel push\n- Konten yang cocok\n- Promo yang aman\n- Red flag""",

    "!analisis": """Analisis data marketing berikut:\n{args}\n\nFormat:\n1. Key findings\n2. Apa yang bekerja\n3. Apa yang gagal/lemah\n4. Root cause\n5. Action plan prioritas\n6. Data tambahan yang perlu dikumpulkan""",

    "!sales-eval": """Analisis data sales berikut:\n{args}\n\nFormat:\n- Executive summary\n- Produk naik\n- Produk turun\n- Kemungkinan penyebab\n- Action marketplace\n- Action content\n- Action promo/pricing\n- Prioritas minggu ini""",

    "!store-report": """Buat laporan toko marketplace dari data berikut:\n{args}\n\nFormat:\n- Summary toko\n- GMV/sales/order jika ada\n- Traffic/conversion issue\n- Produk hero\n- Produk bermasalah\n- Kompetitor/price issue jika terlihat\n- Action plan 7 hari\n- Notes untuk owner""",

    "!ads-report": """Analisis data iklan berikut:\n{args}\n\nFormat:\n- Summary\n- ROAS/CTR/CVR/CPC/CPA jika tersedia\n- Campaign yang harus scale\n- Campaign yang harus stop\n- Creative insight\n- Budget reallocation\n- Next test""",

    "!weekly-report": """Buat weekly marketing report dari data berikut:\n{args}\n\nFormat:\n- Highlights minggu ini\n- KPI summary\n- Campaign progress\n- Content output\n- Sales/marketplace notes\n- Problem/blocker\n- Next week priority\n- Decision needed from owner""",

    "!weekly-plan": """Buat weekly marketing plan berdasarkan goal berikut:\n{args}\n\nFormat:\n- Goal minggu ini\n- 3 prioritas utama\n- Plan Senin-Jumat\n- Konten yang harus dibuat\n- Campaign yang harus jalan\n- Report yang harus dikumpulkan\n- PIC role yang disarankan\n- KPI minggu ini""",

    "!daily-task": """Buat task harian marketing berdasarkan prioritas berikut:\n{args}\n\nFormat:\n- Must do today\n- Should do\n- Can delay\n- Delegasi ke role: marketplace, B2B, talent, campaign, graphic design\n- Output yang harus selesai hari ini\n- Reminder follow-up""",

    "!meeting-summary": """Ubah notes meeting berikut menjadi action summary:\n{args}\n\nFormat:\n- Keputusan utama\n- Action items\n- PIC\n- Deadline\n- Risiko/blocker\n- Hal yang belum jelas\n- Follow-up message yang bisa dikirim""",

    "!sop": """Buat SOP singkat untuk proses berikut:\n{args}\n\nFormat:\n- Tujuan SOP\n- Step-by-step\n- Checklist kualitas\n- PIC\n- Tools yang dipakai\n- Output final\n- Common mistake""",

    "!priority": """Urutkan prioritas dari list task berikut menggunakan impact vs urgency:\n{args}\n\nFormat:\n- P0: harus hari ini\n- P1: penting minggu ini\n- P2: bisa nanti\n- Drop/delegate\n- Alasan prioritas\n- Jadwal eksekusi sederhana""",

    "!harga-jual": """Hitung strategi harga jual marketplace dari input berikut:\n{args}\n\nGunakan logika:\n- Harga minimum = modal / (1 - fee% - margin_bersih_target%) jika data memungkinkan\n- Pisahkan fee marketplace, diskon, subsidi, ads jika disebutkan\n\nFormat:\n- Asumsi angka\n- Harga minimum aman\n- Harga ideal\n- Harga promo terendah\n- Estimasi margin bersih\n- Red flag kalau margin terlalu tipis\n- Rekomendasi bundling/upsell""",

    "!budget": """Buat alokasi budget campaign dari input berikut:\n{args}\n\nFormat:\n- Objective\n- Total budget\n- Alokasi ads/content/KOL/UGC/promo\n- Target ROAS atau KPI minimum\n- Skenario konservatif vs agresif\n- Risk\n- Tracking yang wajib""",

    "!promo-math": """Audit promo berikut apakah masih menguntungkan:\n{args}\n\nFormat:\n- Asumsi\n- Harga normal vs promo\n- Fee dan biaya yang harus dihitung\n- Margin setelah promo\n- Break-even\n- Apakah promo layak?\n- Alternatif promo yang lebih aman""",

    "!margin-check": """Audit margin dari data berikut:\n{args}\n\nFormat:\n- Margin kotor\n- Estimasi margin bersih\n- Biaya yang sering kelupaan\n- Risiko cashflow\n- Produk yang harus dinaikkan harga/dibundling\n- Action pricing""",

    "!b2b": """Buat pitch B2B untuk target berikut:\n{args}\n\nFormat sebagai pesan/email siap kirim:\n- Opening\n- Value proposition\n- Brand/produk relevan\n- Benefit untuk target\n- Offer/next step\n- Closing""",

    "!b2b-pitch": """Buat pitch B2B lengkap untuk target berikut:\n{args}\n\nFormat:\n- Target profile\n- Pain point mereka\n- Produk Pandara yang cocok\n- Pitch WA singkat\n- Pitch email formal\n- Objection handling\n- Follow-up sequence 3 tahap\n- Proposal outline""",

    "!followup": """Buat follow-up WA/email untuk situasi berikut:\n{args}\n\nFormat:\n- Follow-up soft\n- Follow-up lebih direct\n- Follow-up terakhir\n- Versi WhatsApp\n- Versi email\n- Next action""",

    "!consignment": """Buat pitch consignment untuk:\n{args}\n\nFormat:\n- Target store fit\n- Produk yang cocok\n- Value untuk store\n- Term consignment yang disarankan\n- Pitch message\n- Objection handling\n- Next step""",

    "!proposal": """Buat outline proposal kerja sama untuk:\n{args}\n\nFormat:\n- Cover title\n- Background\n- Objective\n- Brand/product offering\n- Partnership model\n- Commercial terms\n- Activation idea\n- Timeline\n- KPI\n- Next step""",
}

USAGE_EXAMPLES = {
    "!campaign-plan": "!campaign-plan Monbento back to school untuk naikkan sales Shopee",
    "!campaign-check": "!campaign-check paste campaign plan kamu di sini",
    "!reels": "!reels Remypan masak simple 20 detik untuk ibu muda",
    "!ugc": "!ugc Monbento lunch box untuk mom creator",
    "!harga-jual": "!harga-jual modal 120000, fee 15%, margin target 30%",
    "!weekly-plan": "!weekly-plan fokus naikkan sales Monbento dan Remypan minggu ini",
    "!meeting-summary": "!meeting-summary paste notes meeting di sini",
    "!followup": "!followup buyer hotel sudah dikirim katalog tapi belum balas 5 hari",
}

# ============================================================
# HELPERS
# ============================================================
def ask_claude(prompt: str) -> str:
    message = ai.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    texts = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            texts.append(block.text)
    return "\n".join(texts).strip() or "Tidak ada output dari Claude."


def split_message(text: str, limit: int = 1900) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        chunk = text[:limit]
        last_newline = chunk.rfind("\n")
        if last_newline > 300:
            chunk = chunk[:last_newline]
        chunks.append(chunk)
        text = text[len(chunk):].lstrip("\n")
    return chunks


async def send_long(channel, text: str):
    for chunk in split_message(text):
        await channel.send(chunk)


def build_help_text() -> str:
    lines = [
        "🤖 PANDARA BOT — COMMAND LIST",
        "=" * 42,
        "Cara pakai: ketik command + instruksi/data.",
        "Contoh: !reels Remypan masak simple 20 detik",
        "",
    ]
    for category, commands in COMMANDS.items():
        lines.append(f"[{category}]")
        for cmd, desc in commands.items():
            lines.append(f"{cmd:<38} {desc}")
        lines.append("")
    lines.append("Ketik !panduan untuk contoh workflow lengkap.")
    return "```" + "\n".join(lines) + "```"


def build_guide_text() -> str:
    return """```md
# PANDUAN PANDARA BOT

## 1. Cara pakai basic
Format:
!command instruksi kamu

Contoh:
!tanya ide campaign untuk Remypan bulan ini
!reels Monbento tumbler pink untuk katalog lifestyle
!harga-jual modal 120000 fee 15% margin target 30%

## 2. Workflow campaign
1) !campaign-plan [brand/event/goal]
2) !campaign-check [paste hasil plan]
3) !brief [konten pertama]
4) !reels [produk/topik]
5) !campaign-report [paste hasil performa]

## 3. Workflow content harian
1) !weekly-plan [goal minggu ini]
2) !daily-task [prioritas hari ini]
3) !brief [topik]
4) !caption [produk]
5) !review-content [paste draft]

## 4. Workflow marketplace/sales
1) !sales-eval [paste data sales]
2) !sku-push [paste data produk]
3) !harga-jual [modal/fee/margin]
4) !promo-math [harga/modal/promo]
5) !store-report [paste data toko]

## 5. Workflow live TikTok
1) !live-script [produk]
2) !objection [produk/masalah customer]
3) !rekap-live [paste data live]
4) !live-eval [paste hasil live]

## 6. Workflow B2B/consignment
1) !b2b-pitch [target]
2) !proposal [target/brand]
3) !followup [status prospek]
4) !consignment [brand/target store]

## 7. Tips supaya output bagus
- Sebut brand: Monbento / Remypan / Marshmallow / JollyFun / Peugeot / Kvetna.
- Sebut channel: Shopee, TikTok Shop, IG, offline, B2B.
- Masukkan angka kalau ada: budget, sales, ROAS, fee, margin, order.
- Paste data mentah tidak masalah; bot akan rapikan.

## 8. Command paling sering dipakai
!weekly-plan
!daily-task
!campaign-plan
!campaign-check
!reels
!caption
!review-content
!sales-eval
!harga-jual
!followup
```"""

# ============================================================
# COMMAND HANDLERS
# ============================================================
async def cmd_help(message):
    await send_long(message.channel, build_help_text())


async def cmd_panduan(message):
    await send_long(message.channel, build_guide_text())


async def cmd_status(message):
    wh_status = "\n".join([f"{'✅' if value else '❌'} {name}" for name, value in WEBHOOKS.items()])
    embed = discord.Embed(
        title="🤖 Pandara Bot Status",
        color=0x57F287,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Discord Bot", value="✅ Online", inline=True)
    embed.add_field(name="Claude API", value=f"✅ Connected\nModel: `{ANTHROPIC_MODEL}`", inline=True)
    embed.add_field(name="Webhooks", value=f"```\n{wh_status}\n```", inline=False)
    await message.channel.send(embed=embed)


async def run_prompt_command(message, cmd: str, args: str):
    if not args and cmd not in ["!ideas"]:
        example = USAGE_EXAMPLES.get(cmd, f"{cmd} [isi instruksi/data]")
        await message.channel.send(f"❌ Usage: `{example}`")
        return

    if not args:
        args = "general marketing Pandara"

    prompt_template = PROMPTS.get(cmd)
    if not prompt_template:
        await message.channel.send("❌ Command belum punya prompt template.")
        return

    prompt = prompt_template.format(args=args)

    async with message.channel.typing():
        response = ask_claude(prompt)

    title = cmd.replace("!", "").replace("-", " ").title()
    await send_long(message.channel, f"**{title}**\n\n{response}")

# ============================================================
# EVENTS
# ============================================================
@client.event
async def on_ready():
    print(f"✅ {client.user} is online.")
    print(f"Connected to {len(client.guilds)} server(s).")
    print(f"Anthropic model: {ANTHROPIC_MODEL}")
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Marketing Pandara | !help",
        )
    )


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.content.startswith("!"):
        return

    content = message.content.strip()
    parts = content.split(" ", 1)
    cmd = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message.author}: {content[:160]}")

    try:
        if cmd == "!help":
            await cmd_help(message)
        elif cmd == "!panduan":
            await cmd_panduan(message)
        elif cmd == "!status":
            await cmd_status(message)
        elif cmd in PROMPTS:
            await run_prompt_command(message, cmd, args)
        else:
            await message.channel.send("❌ Command tidak dikenal. Ketik `!help` untuk melihat daftar command.")

    except anthropic.NotFoundError as e:
        await message.channel.send(
            "❌ Model Claude tidak ditemukan. Cek Railway Variable `ANTHROPIC_MODEL`. "
            "Pakai: `claude-sonnet-4-6`"
        )
        print(f"ANTHROPIC NotFoundError: {e}")

    except anthropic.AuthenticationError as e:
        await message.channel.send("❌ Anthropic API key salah/expired. Cek Railway Variable `ANTHROPIC_API_KEY`.")
        print(f"ANTHROPIC AuthenticationError: {e}")

    except anthropic.RateLimitError as e:
        await message.channel.send("❌ Claude API rate limit/quota habis. Cek billing Anthropic atau coba lagi nanti.")
        print(f"ANTHROPIC RateLimitError: {e}")

    except Exception as e:
        await message.channel.send(f"❌ Error internal: `{str(e)[:300]}`")
        print(f"ERROR: {type(e).__name__}: {e}")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("🚀 Starting Pandara Bot...")
    client.run(DISCORD_TOKEN)
