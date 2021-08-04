"""ambient_downloader.py - download an ambient XML file from ambient-mixer.com
 
Usage:
  ambient_downloader.py <url>
 
Options:
  <url>                 URL of the ambient mix.
  -h --help          Show this help message.
 
"""
__author__      = "Philooz"
__copyright__   = "2017 GPL"

import re, os

import requests
import untangle
import aiohttp
import aiofiles
import asyncio

template_url = "https://xml.ambient-mixer.com/audio-template?player=html5&id_template="
re_js_reg = re.compile(r"AmbientMixer.setup\(([0-9]+)\);")

def makedirs():
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
    if not os.path.exists("presets"):
        os.makedirs("presets")

async def download_file(url, save = False, filename = None):
    if(len(url.strip()) == 0):
        return
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        content = await response.read()
    if(save):
        if filename is None:
            filename = url.split('/')[-1]
        async with aiofiles.open(filename,"wb") as f:
            await f.write(content)
        print("Saved {} as {}.".format(url, filename))
    else:
        return await response.read()

async def get_correct_file(url, filename = None):
    if(filename is None):
        filename = url.split("/")[-1]
    print(url)
    if(not url.startswith(template_url)):
            page = await download_file(url)
            val = re_js_reg.findall(str(page))[0]
            url = template_url + val
    fname = os.path.join("presets", "{}.xml".format(filename))
    await download_file(url, True, fname)
    return fname

async def download_sounds(xml_file):
    obj = untangle.parse(xml_file)
    tasks = []
    for chan_num in range(1,9):
        channel = getattr(obj.audio_template, "channel{}".format(chan_num))
        new_filename = channel.id_audio.cdata
        url = channel.url_audio.cdata
        url_ogg = channel.url_audio.cdata.replace(".mp3",".ogg")
        ext = url.split('.')[-1]
        filename = os.path.join("sounds", new_filename + "." + ext)
        filename_ogg = os.path.join("sounds", new_filename + ".ogg")
        if not(os.path.exists(filename) or os.path.exists(filename_ogg)):
            tasks += [download_file(url, True, filename),download_file(url_ogg, True, filename_ogg)]
    await asyncio.gather(*tasks)

async def helper(arg):
    xml_file = await get_correct_file(arg)
    await download_sounds(xml_file)

from docopt import docopt
if __name__ == "__main__":
    arguments = docopt(__doc__, version = '0.1ß')
    makedirs()
    asyncio.get_event_loop().run_until_complete(helper(arguments.get('<url>')))
