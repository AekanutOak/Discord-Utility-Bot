import asyncio
import discord
import gtts
import json
import os
import random

from typing import Dict, List
from discord.ext import commands
from pydub import AudioSegment

workspace = os.path.dirname(__file__)
resource_path = os.path.join(workspace,"resource")
utils_path = os.path.join(workspace,"utils")

with open(os.path.join(workspace, 'config.json'),"r",encoding="utf-8") as f:
    config = json.load(f)

token = config['token']
settings = config['settings']
member_dict = config["members"]
opennings = config["opennings"]
closings = config["closings"]
sound_desc = config["sound_description"]

# Initialize the bot
bot = commands.Bot(command_prefix="ดิน",intents=discord.Intents.all())
voice_client = None

def divide_groups(input_list, n):
    if len(input_list) < n:
        return []

    group_size = len(input_list) // n
    remainder = len(input_list) % n

    groups = []

    start = 0
    for i in range(n):
        group_end = start + group_size + (1 if i < remainder else 0)
        groups.append(input_list[start:group_end])
        start = group_end

    return groups

def search_for_id(input_name: str, name_dict: Dict[str, List[str]]) -> List[str]:
    id_result = [key for key, value in name_dict.items() if input_name in value]
    return id_result

def search_for_song(member_id: str,closing=False):
    if(member_id in member_dict):
        if(closing):
            if(member_id in closings):
                return random.choice(closings[member_id])
            
        else:
            if(member_id in opennings):
                return random.choice(opennings[member_id])
            
    return ""

def search_for_song_keyword(keyword: List[str], song_dict: Dict[str, List[str]]) -> List[str]:
    matching_songs = []

    for song_key, song_keywords in song_dict.items():
        # Check if all values in keyword list are in the song's keywords
        if all(kw in ' '.join(song_keywords) for kw in keyword):
            matching_songs.append(song_key)
    
    return matching_songs

async def speak(author_voice,channel,message):
    tts = gtts.gTTS(message, lang='th', tld='com',slow=False)
    tts_path = os.path.join(resource_path,"speak.mp3")
    tts.save(tts_path)

    audio = AudioSegment.from_mp3(tts_path)
    audio.speedup(playback_speed=1.2).export(tts_path,format="mp3")

    await play_sound(author_voice,channel,"speak.mp3")
    return

async def play_sound(author_voice,message_channel,sound):
    global voice_client
    
    if(author_voice == None):
        return
    
    if(voice_client == None or voice_client.channel.id != author_voice.channel.id):

        try: 
            voice_client = await voice_client.disconnect()
        except:
            voice_client = None
        finally:
            if(author_voice == None):
                default_channel = random.choice(settings["default_channel"])
                voice_client = await bot.get_channel(default_channel).connect()

            else:
                voice_client = await author_voice.channel.connect()

    sound_path = os.path.join(resource_path,sound)

    if(voice_client.is_playing()):
        voice_client.stop()

    voice_client.play(discord.FFmpegPCMAudio(sound_path))

    while voice_client.is_playing():
        await asyncio.sleep(0.5)

async def join(author_voice,message_channel):
    global voice_client

    if(author_voice == None):
        await message_channel.send(random.choice([
            "ให้เข้าห้องไหนหรือครับ",
            "อยู่ในห้องหรือเปล่าครับ",
            "อยู่ห้องไหนหรือครับ",
            "ห้องไหนครับ",
            "หาห้องไม่เจอครับ ห้องไหนหรือครับ"
        ]))
        return
                        
    else:
        if(voice_client == None or voice_client.channel.id != author_voice.channel.id):
            try: 
                voice_client = await voice_client.disconnect()
            except:
                pass
            finally:
                voice_client = await author_voice.channel.connect()
                                
                await message_channel.send(random.choice([
                    "เข้ามาแล้วครับ",
                    "เข้าแล้วครับ",
                    "โอเคครับ",
                    "อยู่ในห้องแล้วครับ",
                    "มีอะไรหรือเปล่าครับ",
                    "ครับ?"
                ]))
                return
                            
        else:
            await message_channel.send(random.choice([
                "อยู่ห้องเดียวกันอยู่แล้วครับ",
                "อยู่ในห้องอยู่แล้วนะครับ",
                "โอเคครับ",
                "ผมอยู่ในห้องอยู่แล้วครับ"
            ]))
            return
        
async def leave(message_channel):
    global voice_client
    if(voice_client == None):
        await message_channel.send(random.choice([
            "ไม่ได้เข้านะครับ",
            "ผมไม่ได้เข้าห้องเลยครับ",
            "ออกไปแล้วครับ",
            "อยู่ข้างนอกอยู่แล้วครับ",
            "ครับ"
        ]))
        return
    
    else:
        voice_client = await voice_client.disconnect()
        await message_channel.send(random.choice([
            "OK ครับ",
            "ออกมาแล้วครับ",
            "ครับ",
            "ได้ครับ",
        ]))
        return
    
@bot.event
async def on_ready():
    global voice_client

    default_channel = random.choice(settings["default_channel"])
    voice_client = await bot.get_channel(default_channel).connect()
    print(f"Logged in as {bot.user.name}")
    return voice_client

@bot.event
async def on_message(message):

    global voice_client
    # Don't reply itself
    if message.author == bot.user:
        return
    
    msg = message.content.lower() 
    text_channel_process = message.channel.id
    channel = message.channel

    # For DM channel  
    if isinstance(message.channel, discord.DMChannel):
        return await message.author.send("มีอะไรครับ")
    
    # For server channel
    elif text_channel_process not in settings["ignore_channel"]:

        author_voice = message.author.voice
        
        if(text_channel_process in settings["tts_channel"]):
            await speak(author_voice,channel,msg)
            return
        
        else:
            for ref in settings["self_reference"]:
                if ref in msg:
                    
                    if("เข้า" in msg or "จอย" in msg or "มา" in msg) and ("ห้อง" in msg or "ดิส" in msg or "discord" in msg):
                        await join(author_voice,channel)
                        return
                    
                    elif("ออก" in msg and "หน่อย" in msg) or ("ออก" in msg and ("ห้อง" in msg or "ดิส" in msg or "discord" in msg)):
                        await leave(channel)
                        return
                    
                    elif("เปิด" in msg or "เล่น" in msg or "ขอ" in msg) and ("เพลง" in msg or "เสียง" in msg):
                        keyword = msg.split()
                        song_keyword = keyword[1:]
                        song = search_for_song_keyword(song_keyword,sound_desc)
                        print(song)
                        if(song == []):
                                await channel.send(random.choice([
                                "ไม่ได้บันทึกไว้ในคอมครับ",
                                "หาไม่เจอครับ",
                                "ไม่ได้โหลดไว้ครับ",
                                "ผมไม่ได้เซฟเอาไว้ครับ"]
                            ))

                        else:
                            await play_sound(author_voice,channel,random.choice(song))
                        return
                    
                    elif("แบ่ง" in msg) and ("ทีม" in msg or "กลุ่ม" in msg):
                        member_ids = ["<@"+str(member.id)+">" for member in author_voice.channel.members]

                        if("<@1144605142692417546>" in member_ids):
                            member_ids.remove("<@1144605142692417546>")

                        try:
                            team_nums = int(msg.split()[1])
                            result = divide_groups(member_ids,team_nums)
                            if(result == []):
                                await channel.send("คนในห้องไม่พอครับ")
                            else:
                                for i in range(len(result)):
                                    message = f"กลุ่มที่ {i+1} ได้แก่ "
                                    for element in result[i]:
                                        message+=(element+" ")

                                    await channel.send(message)
                            return
                        except:
                            await channel.send("กรุณาพิมพ์ว่า คุณดินแบ่งทีม จำนวนทีมที่เป็นตัวเลข")
                            
                        return
                    
                    elif ("เรียก" in msg or "คุย" in msg) and ("ยังไง" in msg or "ไง" in msg or "อย่างไร" in msg):
                        message = "ให้พิมพ์ข้อความที่มีคำต่อไปนี้ครับ: "
                        for i in settings["self_reference"]:
                            message+=(i+" ")

                        await channel.send(message)
                        return
                    
                    elif "ลบคำเรียกคำว่า" in msg or "ลบคำเรียก" in msg:
                        msg = msg.split()
                        try:
                            reference_to_del = msg[1]

                            if reference_to_del in settings["self_reference"]:
                                settings["self_reference"].remove(reference_to_del)
                                with open(os.path.join(workspace, 'config.json'),"w",encoding="utf-8") as f:
                                    f.write(json.dumps(config,ensure_ascii=False))
                            
                                await channel.send("ลบคำเรียกคำว่า "+reference_to_del+" เรียบร้อยครับ")
                            else:
                                await channel.send("ไม่รู้จักคำเรียกนี้นะครับ")
                        
                        except IndexError as e:
                            await channel.send("เว้นวรรคก่อนจะพิมพ์คำที่จะลบด้วยครับเช่น ลบคำเรียกคำว่า din")

                        return
                    
                    elif "เพิ่มคำเรียกคำว่า" in msg or "เพิ่มคำเรียก" in msg:
                        msg = msg.split()
                        try:
                            reference_to_add = msg[1]

                            if reference_to_add not in settings["self_reference"]:
                                settings["self_reference"].append(reference_to_add)

                                with open(os.path.join(workspace, 'config.json'),"w",encoding="utf-8") as f:
                                    f.write(json.dumps(config,ensure_ascii=False))
                            
                                await channel.send("เพิ่มคำเรียกคำว่า "+reference_to_add+" เรียบร้อยครับ")
                            else:
                                await channel.send("เอ่อ คำเรียกนี้มีอยู่แล้วนะครับ")

                        except IndexError as e:
                            await channel.send("เว้นวรรคก่อนจะพิมพ์คำที่จะลบด้วยครับเช่น เพิ่มคำเรียกคำว่า din")

                        return
                    
                    elif "เรียก" in msg or "แทก" in msg or "แท็ก" in msg:
                        if "<@" in msg:
                            user_id = msg[msg.find("<"):msg.find(">")+1]
                            message = user_id + (random.choice([
                                "มาหน่อยครับ",
                                "เข้าดิสหน่อยครับ",
                                "ต้องการตัวครับ"
                            ]))

                            await channel.send(message)

                        else:
                            msg = msg.replace("พี่","")
                            msg = msg.replace("น้อง","")
                            msg = msg.replace("ไอ","")
                            msg = msg.replace("ไอ้","")
                            msg = msg.replace("คุณ","")
                            msg = msg.split()
                            try:
                                name_to_call = msg[1]
                                member_id = search_for_id(name_to_call,member_dict)
                                if member_id:
                                    message = ""
                                    for id in member_id:
                                        message += f"<@{id}> "

                                    message+=(random.choice([
                                            "มาหน่อยครับ",
                                            "เข้าดิสหน่อยครับ",
                                            "ต้องการตัวครับ"
                                        ]))

                                    await channel.send(message)

                                else:
                                    await channel.send("ไม่รู้จักคนชื่อ"+name_to_call)

                            except IndexError as e:
                                await channel.send("โปรดเว้นช่องว่างระหว่างชื่อคนด้วยครับเช่น เรียก พี่ไบค์ ให้หน่อย")

                        return
                    
                    elif ("ตอบ" in msg or "คุย" in msg) and "อะไร" in msg:
                        msg = ""
                        index = 1
                        for i in settings["normal_response"]:
                            msg+=(f"{index} "+i+"\n")
                            index+=1

                        msg = "ผมจะสุ่มตอบด้วยคำว่า\n"+msg
                        await channel.send(msg)
                        return 
                    
                    elif ("ตอบ" in msg or "คุย" in msg) and "ลบ" in msg:
                        message_content = msg.split()
                        try:
                            to_remove = message_content[1]
                            try:
                                response_remove = settings["normal_response"][(int(to_remove))-1]
                                settings["normal_response"].pop(int(to_remove)-1)

                                with open(os.path.join(workspace, 'config.json'),"w",encoding="utf-8") as f:
                                    f.write(json.dumps(config,ensure_ascii=False))
                                
                                await channel.send("ลบคำตอบกลับ "+response_remove+" เรียบร้อยครับ")
                            
                            except IndexError as e:
                                await channel.send("ใส่เลขไม่ถูกหรือเปล่าครับ")

                        except IndexError as e:
                            await channel.send("เว้นวรรคตัวเลขด้วยครับ เช่น ลบคำที่ 5 หน่อย")

                        return

                    elif ("ตอบ" in msg or "คุย" in msg) and "เพิ่ม" in msg:
                        message_content = msg.split()
                        try:
                            to_add = message_content[1]
                            to_add = to_add.replace("\"","")
                            settings["normal_response"].append(to_add)

                            with open(os.path.join(workspace, 'config.json'),"w",encoding="utf-8") as f:
                                f.write(json.dumps(config,ensure_ascii=False))
                                
                                await channel.send("เพิ่มคำตอบกลับ "+to_add+" เรียบร้อยครับ")
                            
                        except IndexError as e:
                            await channel.send("เว้นวรรคำที่จะเพิ่มด้วยครับ เช่น เพิ่มคำตอบ \"สวัสดีครับ\" หน่อย")

                        return
                    
                    elif ("หวย" in msg) or ("งวด" in msg and "หน้า" in msg):
                        random_integer = random.randint(0, 999)
                        formatted_integer = f"คิดว่าเป็น {random_integer:03} นะครับ"
                        result = random.choices([True,False],[0.7,0.3],k=1)[0]
                        if(result):
                            await channel.send(random.choice(settings["normal_response"]))
                        
                        else:
                            await channel.send(formatted_integer)

                        return
                    
                    else:
                        await channel.send(random.choice(
                            settings["normal_response"]
                        ))
                        return
                return

@bot.event
async def on_voice_state_update(entity,before,after):
    global voice_client
    if(before.channel != after.channel):
        if(after.channel == None):
            sound = search_for_song(str(entity.id),True)
            if(sound != ""):
                try:
                    voice_client = await voice_client.disconnect()
                except:
                    voice_client = None
                voice_client = await before.channel.connect()
                await play_sound(before,"on_voice_state_update",sound)

        else:
            sound = search_for_song(str(entity.id))
            if(sound != ""):
                try:
                    voice_client = await voice_client.disconnect()
                except:
                    voice_client = None
                voice_client = await after.channel.connect()
                await play_sound(after,"on_voice_state_update",sound)

            else:
                song = search_for_song_keyword(["สวัสดี"],sound_desc)
                await play_sound(after,"on_voice_state_update",random.choice(song))
            
#bot.run(token)
        