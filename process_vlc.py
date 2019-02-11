import youtube_dl
import os
import threading
import logging
import json

logger = logging.getLogger("RaspberryCast")
volume = 0


def launchvideo(url, config, sub=False):
    setState("2")

    os.system("echo -n q > /tmp/cmd &")  # Kill previous instance of OMX

    if config["new_log"]:
        os.system("sudo fbi -T 1 -a --noverbose images/processing.jpg")

    thread = threading.Thread(target=play_with_vlc, args=(url, sub,),
                              kwargs=dict(width=config["width"], height=config["height"],
                                          new_log=config["new_log"]))
    thread.start()

    # os.system("echo . > /tmp/cmd &")  # Start signal for OMXplayer


def queuevideo(url, config, onlyqueue=False):
    logger.info('Adding to queue...')

    if getState() == "0" and not onlyqueue:
        logger.info('No video currently playing, playing video instead of \
adding to queue.')
        thread = threading.Thread(target=play_with_vlc, args=(url, False,),
                                  kwargs=dict(width=config["width"], height=config["height"],
                                              new_log=config["new_log"]))
        thread.start()
        # os.system("echo . > /tmp/cmd &")  # Start signal for OMXplayer
    else:
        if url is not None:
            with open('video.queue', 'a') as f:
                f.write(url + '\n')


def playlist(url, cast_now, config):
    logger.info("Processing playlist.")

    if cast_now:
        logger.info("Playing first video of playlist")
        launchvideo(url, config)  # Launch first video
    else:
        queuevideo(url, config)

    thread = threading.Thread(target=playlistToQueue, args=(url, config))
    thread.start()


def playlistToQueue(url, config):
    logger.info("Adding every videos from playlist to queue.")
    ydl = youtube_dl.YoutubeDL(
        {
            'logger': logger,
            'extract_flat': 'in_playlist',
            'ignoreerrors': True,
        })
    with ydl:  # Downloading youtub-dl infos
        result = ydl.extract_info(url, download=False)
        for i in result['entries']:
            logger.info("queuing video")
            if i != result['entries'][0]:
                queuevideo(i['url'], config)


def play_with_vlc(url, sub, width="", height="", new_log=False):
    logger.info("Starting VLC now.")

    setState("1")
    os.system("vlc " + url)

    if getState() != "2":  # In case we are again in the launchvideo function
        setState("0")
        with open('video.queue', 'r') as f:
            # Check if there is videos in queue
            first_line = f.readline().replace('\n', '')
            if first_line != "":
                logger.info("Starting next video in playlist.")
                with open('video.queue', 'r') as fin:
                    data = fin.read().splitlines(True)
                with open('video.queue', 'w') as fout:
                    fout.writelines(data[1:])
                thread = threading.Thread(
                    target=play_with_vlc, args=(first_line, False,),
                    kwargs=dict(width=width, height=height,
                                new_log=new_log),
                )
                thread.start()
                # os.system("echo . > /tmp/cmd &")  # Start signal for OMXplayer
            else:
                logger.info("Playlist empty, skipping.")
                if new_log:
                    os.system("sudo fbi -T 1 -a --noverbose images/ready.jpg")


def setState(state):
    # Write to file so it can be accessed from everywhere
    os.system("echo " + state + " > state.tmp")


def getState():
    with open('state.tmp', 'r') as f:
        return f.read().replace('\n', '')


def setVolume(vol):
    global volume
    if vol == "more":
        volume += 300
    if vol == "less":
        volume -= 300
