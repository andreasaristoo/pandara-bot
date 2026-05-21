import discord
import anthropic
import os
import json
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

WEBHOOKS = {
    "live-report":      os.environ.get("WH_LIVE_REPORT"),
    "sales-report":     os.environ.get("WH_SALES_REPORT"),
    "campaign-plan":    os.environ.get("WH_CAMPAIGN_PLAN"),
    "campaign-ideas":   os.environ.get("WH_CAMPAIGN_IDEAS"),
    "general-chat":     os.environ.get("WH_GENERAL_CHAT"),
    "weekly-plan":      os.environ.get("WH_WEEKLY_PLAN"),
}

SYSTEM_PROMPT = """Kamu adalah Claude, AI marketing assistant untuk Pandara Indonesia (brand N.O.P).
Pandara mendistribusikan 6 brand premium: Monbento (bento box), Marshmallow (school bags/stationery), 
JollyFun (kids silicone coloring mats), Peugeot Saveurs (kitchen tools), Remy Pan (cookware), Kvetna (crystal).
Channel penjualan: TikTok Shop, Shopee Mall, Tokopedia, Instagram Shop, offline di KoKas & Plaza Indonesia.
Tone: profesional tapi friendly. Jawab dalam Bahasa Indonesia kecuali diminta English.
Selalu berikan jawaban yang actionable dan konkret untuk tim marketing."""

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================
# HELPERS
# ============================================================
def ask_claude(prompt, context=""):
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    message = ai.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": full_prompt}]
    )
    return message.content[0].text

def split_message(text, limit=1900):
    """Split long messages for Discord's 2000 char limit"""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunk = text[:limit]
        last_newline = chunk.rfind('\n')
        if last_newline > 0:
            chunk = text[:last_newline]
        chunks.append(chunk)
        text = text[len(chunk):].lstrip('\n')
    return chunks

# ============================================================
# COMMANDS
# ============================================================
COMMANDS = {
    "!help": "Tampilkan semua command yang tersedia",
    "!tanya [pertanyaan]": "Tanya Claude apapun soal marketing Pandara",
    "!rekap-live [data]": "Buatkan rekap & analisis dari data live TikTok",
    "!ideas [topik]": "Generate campaign ideas (contoh: !ideas back to school)",
    "!brief [topik]": "Buatkan content brief untuk konten (contoh: !brief monbento reels)",
    "!caption [produk]": "Buatkan caption Instagram (contoh: !caption trolley marshmallow)",
    "!analisis [data]": "Analisis data sales/performance yang kamu paste",
    "!b2b [target]": "Buatkan pitch B2B (contoh: !b2b hotel bintang 5)",
    "!status": "Cek status bot & connections",
}

async def cmd_help(message):
    lines = ["```", "🤖 CLAUDE x PANDARA — Available Commands", "─" * 40]
    for cmd, desc in COMMANDS.items():
        lines.append(f"{cmd:<30} {desc}")
    lines.append("─" * 40)
    lines.append("Prefix semua command dengan ! di channel manapun")
    lines.append("```")
    await message.channel.send("\n".join(lines))

async def cmd_status(message):
    wh_status = "\n".join([f"  {'✅' if v else '❌'} #{k}" for k, v in WEBHOOKS.items()])
    embed = discord.Embed(
        title="🤖 Claude x Pandara — Status",
        color=0x57F287,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Claude API", value="✅ Connected", inline=True)
    embed.add_field(name="Discord Bot", value="✅ Online", inline=True)
    embed.add_field(name="Webhooks", value=f"```\n{wh_status}\n```", inline=False)
    await message.channel.send(embed=embed)

async def cmd_tanya(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!tanya [pertanyaan kamu]`")
        return
    async with message.channel.typing():
        response = ask_claude(args)
    for chunk in split_message(response):
        await message.channel.send(chunk)

async def cmd_rekap_live(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!rekap-live [paste data live di sini]`")
        return
    async with message.channel.typing():
        prompt = f"""Analisis data live TikTok berikut dan buatkan rekap terstruktur:

DATA:
{args}

Buatkan rekap dalam format:
1. Ringkasan metrik (impressions, views, komentar, followers, GMV)
2. Analisis performa (bagus/buruk di mana)
3. Root cause kalau conversion rendah
4. 3 rekomendasi konkret untuk live berikutnya"""
        response = ask_claude(prompt)
    embed = discord.Embed(
        title="📊 Rekap Live TikTok",
        description=response[:2000],
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Claude x Pandara")
    await message.channel.send(embed=embed)

async def cmd_ideas(message, args):
    topic = args if args else "general campaign Pandara"
    async with message.channel.typing():
        prompt = f"""Buatkan 3 campaign ideas kreatif untuk Pandara Indonesia dengan topik: {topic}

Untuk setiap idea berikan:
- Nama campaign yang catchy
- Konsep singkat (2-3 kalimat)
- Brand yang terlibat
- Platform eksekusi
- Estimasi budget (low/medium/high)
- KPI yang diukur
- 1 hook/angle yang membedakan dari kompetitor

Format yang menarik, actionable, bisa langsung dieksekusi tim kecil."""
        response = ask_claude(prompt)
    for chunk in split_message(f"💡 **Campaign Ideas — {topic.title()}**\n\n{response}"):
        await message.channel.send(chunk)

async def cmd_brief(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!brief [topik konten]`")
        return
    async with message.channel.typing():
        prompt = f"""Buatkan content brief lengkap untuk tim konten Pandara Indonesia:

Topik: {args}

Sertakan:
- Objective konten
- Target audience spesifik
- Platform & format (Reels/TikTok/Static/Carousel)
- Hook line (3 opsi)
- Key message (1 kalimat)
- Struktur konten (opening → isi → CTA)
- Visual direction
- Caption ready-to-use (English, cold luxury tone)
- Hashtag set
- Metrik sukses"""
        response = ask_claude(prompt)
    for chunk in split_message(response):
        await message.channel.send(chunk)

async def cmd_caption(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!caption [nama produk]`")
        return
    async with message.channel.typing():
        prompt = f"""Buatkan 3 variasi caption Instagram untuk produk Pandara: {args}

Style: Cold luxury, minimal, confident. English-first.
Format per caption:
- Hook line (1 baris)
- Body (1-2 baris)
- CTA subtle
- Hashtag set (10-15 tags)

Buat 3 variasi: storytelling / product-focus / lifestyle angle."""
        response = ask_claude(prompt)
    for chunk in split_message(response):
        await message.channel.send(chunk)

async def cmd_analisis(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!analisis [paste data di sini]`")
        return
    async with message.channel.typing():
        prompt = f"""Analisis data marketing berikut dari Pandara Indonesia:

{args}

Berikan:
1. Key findings (3-5 poin terpenting)
2. Apa yang bekerja dengan baik
3. Apa yang perlu diperbaiki
4. Rekomendasi aksi konkret (prioritas tinggi ke rendah)
5. Red flags yang perlu diperhatikan"""
        response = ask_claude(prompt)
    for chunk in split_message(f"📊 **Analisis Data**\n\n{response}"):
        await message.channel.send(chunk)

async def cmd_b2b(message, args):
    target = args if args else "retailer premium"
    async with message.channel.typing():
        prompt = f"""Buatkan pitch B2B untuk Pandara Indonesia kepada: {target}

Pitch harus mencakup:
- Opening hook (1-2 kalimat yang menarik perhatian)
- Value proposition utama
- Brand yang relevan untuk target ini
- Why now (urgensi)
- Commercial terms yang bisa ditawarkan (konsinyasi/beli putus/dll)
- Next step yang jelas

Format: pitch email yang langsung bisa dikirim. Profesional, percaya diri."""
        response = ask_claude(prompt)
    for chunk in split_message(response):
        await message.channel.send(chunk)

# ============================================================
# EVENT HANDLERS
# ============================================================
@client.event
async def on_ready():
    print(f"✅ {client.user} is online!")
    print(f"Connected to {len(client.guilds)} server(s)")
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Marketing Pandara | !help"
        )
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not message.content.startswith("!"):
        return

    content = message.content.strip()
    parts = content.split(" ", 1)
    cmd = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message.author}: {content[:60]}")

    try:
        if cmd == "!help":
            await cmd_help(message)
        elif cmd == "!status":
            await cmd_status(message)
        elif cmd == "!tanya":
            await cmd_tanya(message, args)
        elif cmd == "!rekap-live":
            await cmd_rekap_live(message, args)
        elif cmd == "!ideas":
            await cmd_ideas(message, args)
        elif cmd == "!brief":
            await cmd_brief(message, args)
        elif cmd == "!caption":
            await cmd_caption(message, args)
        elif cmd == "!analisis":
            await cmd_analisis(message, args)
        elif cmd == "!b2b":
            await cmd_b2b(message, args)
    except Exception as e:
        await message.channel.send(f"❌ Error: {str(e)[:100]}")
        print(f"ERROR: {e}")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("🚀 Starting Claude x Pandara Bot...")
    client.run(DISCORD_TOKEN)
