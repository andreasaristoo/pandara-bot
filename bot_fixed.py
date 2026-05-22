import os
from datetime import datetime

import discord
import anthropic

# ============================================================
# CONFIG
# ============================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Pakai model valid terbaru. Bisa override lewat Railway Variables:
# ANTHROPIC_MODEL=claude-sonnet-4-6
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

WEBHOOKS = {
    "live-report": os.getenv("WH_LIVE_REPORT"),
    "sales-report": os.getenv("WH_SALES_REPORT"),
    "campaign-plan": os.getenv("WH_CAMPAIGN_PLAN"),
    "campaign-ideas": os.getenv("WH_CAMPAIGN_IDEAS"),
    "general-chat": os.getenv("WH_GENERAL_CHAT"),
    "weekly-plan": os.getenv("WH_WEEKLY_PLAN"),
}

SYSTEM_PROMPT = """Kamu adalah AI marketing assistant untuk Pandara Indonesia.
Pandara mendistribusikan beberapa brand premium: Monbento, Marshmallow, JollyFun, Peugeot Saveurs, Remy Pan, dan Kvetna.
Channel penjualan: TikTok Shop, Shopee Mall, Tokopedia, Instagram Shop, dan offline store.
Tone: profesional, friendly, konkret, dan actionable. Jawab dalam Bahasa Indonesia kecuali diminta English.
Fokus bantu tim marketing untuk ide campaign, brief konten, caption, analisis performa, dan pitch B2B.
Jangan terlalu panjang kecuali user meminta detail. Beri output yang bisa langsung dieksekusi tim kecil."""

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
# HELPERS
# ============================================================
def ask_claude(prompt: str, context: str = "") -> str:
    full_prompt = f"{context}\n\n{prompt}" if context else prompt

    message = ai.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": full_prompt}
        ],
    )

    # Gabungkan semua text block agar aman kalau response punya beberapa block.
    texts = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            texts.append(block.text)

    return "\n".join(texts).strip() or "Tidak ada output dari Claude."


def split_message(text: str, limit: int = 1900) -> list[str]:
    """Split long messages for Discord's 2000 character limit."""
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


# ============================================================
# COMMANDS
# ============================================================
COMMANDS = {
    "!help": "Tampilkan semua command yang tersedia",
    "!tanya [pertanyaan]": "Tanya AI soal marketing Pandara",
    "!rekap-live [data]": "Buatkan rekap & analisis dari data live TikTok",
    "!ideas [topik]": "Generate campaign ideas. Contoh: !ideas back to school",
    "!brief [topik]": "Buatkan content brief. Contoh: !brief monbento reels",
    "!caption [produk]": "Buatkan caption Instagram. Contoh: !caption trolley marshmallow",
    "!analisis [data]": "Analisis data sales/performance yang kamu paste",
    "!b2b [target]": "Buatkan pitch B2B. Contoh: !b2b hotel bintang 5",
    "!status": "Cek status bot & connections",
}


async def cmd_help(message):
    lines = [
        "```",
        "🤖 PANDARA BOT — Available Commands",
        "─" * 48,
    ]

    for cmd, desc in COMMANDS.items():
        lines.append(f"{cmd:<28} {desc}")

    lines.extend([
        "─" * 48,
        "Prefix semua command dengan !",
        "```",
    ])

    await message.channel.send("\n".join(lines))


async def cmd_status(message):
    wh_status = "\n".join(
        [f"{'✅' if value else '❌'} {name}" for name, value in WEBHOOKS.items()]
    )

    embed = discord.Embed(
        title="🤖 Pandara Bot Status",
        color=0x57F287,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Discord Bot", value="✅ Online", inline=True)
    embed.add_field(name="Claude API", value=f"✅ Connected\nModel: `{ANTHROPIC_MODEL}`", inline=True)
    embed.add_field(name="Webhooks", value=f"```\n{wh_status}\n```", inline=False)

    await message.channel.send(embed=embed)


async def cmd_tanya(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!tanya [pertanyaan kamu]`")
        return

    async with message.channel.typing():
        response = ask_claude(args)

    await send_long(message.channel, response)


async def cmd_rekap_live(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!rekap-live [paste data live di sini]`")
        return

    prompt = f"""Analisis data live TikTok berikut dan buatkan rekap terstruktur:

DATA:
{args}

Format:
1. Ringkasan metrik
2. Analisis performa
3. Root cause jika conversion rendah
4. 3 rekomendasi konkret untuk live berikutnya
5. Prioritas action untuk tim"""

    async with message.channel.typing():
        response = ask_claude(prompt)

    await send_long(message.channel, f"📊 **Rekap Live TikTok**\n\n{response}")


async def cmd_ideas(message, args):
    topic = args or "general campaign Pandara"

    prompt = f"""Buatkan 3 campaign ideas kreatif untuk Pandara Indonesia dengan topik: {topic}

Untuk setiap ide berikan:
- Nama campaign yang catchy
- Konsep singkat
- Brand yang terlibat
- Platform eksekusi
- Estimasi budget: low/medium/high
- KPI yang diukur
- Hook/angle pembeda dari kompetitor
- Step eksekusi 3 langkah"""

    async with message.channel.typing():
        response = ask_claude(prompt)

    await send_long(message.channel, f"💡 **Campaign Ideas — {topic.title()}**\n\n{response}")


async def cmd_brief(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!brief [topik konten]`")
        return

    prompt = f"""Buatkan content brief lengkap untuk tim konten Pandara Indonesia.

Topik: {args}

Sertakan:
- Objective konten
- Target audience spesifik
- Platform & format
- 3 hook line
- Key message
- Struktur konten: opening → isi → CTA
- Visual direction
- Caption ready-to-use
- Hashtag set
- Metrik sukses"""

    async with message.channel.typing():
        response = ask_claude(prompt)

    await send_long(message.channel, response)


async def cmd_caption(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!caption [nama produk]`")
        return

    prompt = f"""Buatkan 3 variasi caption Instagram untuk produk Pandara: {args}

Style: premium, minimal, confident, tapi tetap natural.
Format per caption:
- Hook line
- Body 1-2 baris
- CTA subtle
- Hashtag set 10-15 tag

Buat 3 angle:
1. storytelling
2. product-focus
3. lifestyle"""

    async with message.channel.typing():
        response = ask_claude(prompt)

    await send_long(message.channel, response)


async def cmd_analisis(message, args):
    if not args:
        await message.channel.send("❌ Usage: `!analisis [paste data di sini]`")
        return

    prompt = f"""Analisis data marketing berikut dari Pandara Indonesia:

{args}

Berikan:
1. Key findings
2. Apa yang bekerja dengan baik
3. Apa yang perlu diperbaiki
4. Rekomendasi aksi konkret, urut dari prioritas tinggi ke rendah
5. Red flags yang perlu diperhatikan"""

    async with message.channel.typing():
        response = ask_claude(prompt)

    await send_long(message.channel, f"📊 **Analisis Data**\n\n{response}")


async def cmd_b2b(message, args):
    target = args or "retailer premium"

    prompt = f"""Buatkan pitch B2B untuk Pandara Indonesia kepada: {target}

Pitch harus mencakup:
- Opening hook
- Value proposition utama
- Brand yang relevan untuk target ini
- Why now
- Commercial terms yang bisa ditawarkan
- Next step yang jelas

Format: pitch email profesional yang langsung bisa dikirim."""

    async with message.channel.typing():
        response = ask_claude(prompt)

    await send_long(message.channel, response)


# ============================================================
# EVENT HANDLERS
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

    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message.author}: {content[:120]}")

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
        else:
            await message.channel.send("❌ Command tidak dikenal. Ketik `!help` untuk melihat daftar command.")

    except anthropic.NotFoundError as e:
        await message.channel.send(
            "❌ Model Claude tidak ditemukan. Cek Railway Variable `ANTHROPIC_MODEL`. "
            "Pakai: `claude-sonnet-4-6`"
        )
        print(f"ANTHROPIC NotFoundError: {e}")

    except anthropic.AuthenticationError as e:
        await message.channel.send(
            "❌ Anthropic API key salah/expired. Cek Railway Variable `ANTHROPIC_API_KEY`."
        )
        print(f"ANTHROPIC AuthenticationError: {e}")

    except anthropic.RateLimitError as e:
        await message.channel.send(
            "❌ Claude API sedang rate limit / quota habis. Cek billing Anthropic atau coba lagi nanti."
        )
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
