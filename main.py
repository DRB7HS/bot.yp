import discord
from discord.ext import commands
import asyncio
import time
import base64
zlib = __import__('zlib')

_encoded_token = "TVRBNE5UTm1abVU0TmpNd056UXdPVGd5TURBOS5HS3ZtMVAub3diNWNHc3dXM2RIcURFMFZ6ZW96aTVVWUdBUjQxSzgtNFBXcEE="
TOKEN = base64.b64decode(_encoded_token.encode('utf-8')).decode('utf-8')

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, status=discord.Status.online)

user_attempts = {}
COOLDOWN_TIME = 7200

def strong_obfuscate(code_text):
    compressed = zlib.compress(code_text.encode('utf-8'))
    b64 = base64.b64encode(compressed).decode('utf-8')
    encoded_payload = "".join([f"\\x{ord(c):02x}" for c in b64])
    
    obfuscated_code = (
        f"import base64, zlib\n"
        f"exec(zlib.decompress(base64.b64decode(''.join([chr(int(x, 16)) for x in '{encoded_payload}'.split('\\\\x')[1:]]))))"
    )
    compact_code = "".join([line.strip() for line in obfuscated_code.splitlines() if line.strip()])
    return compact_code

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.content.startswith('!obf'):
            user_id = message.author.id
            current_time = time.time()

            if user_id not in user_attempts:
                user_attempts[user_id] = {'count': 0, 'reset_time': 0}

            user_data = user_attempts[user_id]

            if user_data['count'] >= 5:
                remaining_time = int(user_data['reset_time'] - current_time)
                if remaining_time > 0:
                    hours = remaining_time // 3600
                    minutes = (remaining_time % 3600) // 60
                    seconds = remaining_time % 60
                    await message.reply(f"[-] لقد أتممت المحاولات بالكامل. حاول مجددا بعد {hours}h {minutes}m {seconds}s")
                    return
                else:
                    user_data['count'] = 0

            if not message.attachments:
                await message.reply("الرجاء إرفاق الملف مع الأمر !obf")
                return

            attachment = message.attachments[0]
            file_bytes = await attachment.read()
            
            try:
                original_code = file_bytes.decode('utf-8')
            except Exception:
                await message.reply("عفواً، الملف غير صالح أو غير مدعوم.")
                return

            user_data['count'] += 1
            
            if user_data['count'] >= 5:
                user_data['reset_time'] = current_time + COOLDOWN_TIME

            ping_ms = round(bot.latency * 1000)
            username = str(message.author)

            msg_content = (
                f"[+] عدد المحاولات  {user_data['count']} / 5 📊\n"
                f"[+] بنق البوت {ping_ms}ms 🧮\n\n"
                f"@{username}"
            )

            sent_msg = await message.reply(msg_content)

            obfuscated_content = strong_obfuscate(original_code)
            
            output_filename = f"obfuscated_{attachment.filename}"
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(obfuscated_content)

            success_text = "تم تشفير سكربتك من قبل tvx اي استفسار ادخل السيرفر https://discord.gg/Y2CBs5s8U وبس مبروك"
            
            await message.author.send(success_text, file=discord.File(output_filename))

            if user_data['count'] >= 5:
                for _ in range(5):
                    await asyncio.sleep(5)
                    rem = int(user_data['reset_time'] - time.time())
                    if rem <= 0:
                        break
                    h = rem // 3600
                    m = (rem % 3600) // 60
                    s = rem % 60
                    updated_content = (
                        f"[+] عدد المحاولات  {user_data['count']} / 5 📊\n"
                        f"[+] بنق البوت {ping_ms}ms 🧮\n\n"
                        f"[-] اذا تم خلص المحاولات حاول مجددا بعد {h}h {m}m {s}s\n\n"
                        f"@{username}"
                    )
                    try:
                        await sent_msg.edit(content=updated_content)
                    except:
                        pass

    await bot.process_commands(message)

bot.run(TOKEN)
