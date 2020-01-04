#!/usr/bin/python
# title                 : buteverywordisagoogleimage.py
# description           : This is just a script that automatically generate a video from a youtube music link that for each word said will download an image that correspond and put it in the video at the correct time.
# author                : Tutozz
# date                  : 2019/12/19
# version               : 1.0
# usage                 : python buteverywordisagoogleimage.py
# python_version        : 3.7
#==============================================================================

# coding: utf-8

import cv2
import shutil
import requests
import re
import youtube_dl
from os import walk, rename
from PIL import ImageFile, Image
from io import StringIO
from skimage import io, filters
from youtube_transcript_api import YouTubeTranscriptApi
from google_images_download import google_images_download
from moviepy.editor import *
from pyfiglet import Figlet


ImageFile.LOAD_TRUNCATED_IMAGES = True  # allow some minimal corruptions in images

# just initialise vars
words_infos = []  # array to store all words said with start time and duration
files = []  # array to store list of files in 'imgs' folder
whatsForbidden_regex = ["\[(.*?)\]", "\((.*?)\)"]  # regex for filtering all '()' and '[]'
whatsForbidden = [".", "!", ",", "-", "?", ";", ":", "♪ ", " ♪", "♪"]  # all special characters to filter out
video_title = ""  # to store the title of music
fps = 30  # to store at what frame rate to generate the video
video_resolution = [1280, 720]  # store the resolution for the video to generate
img_downloaded = []  # store all videos download during current session
lengthCredits = 2  # length of the beginning screen
ydl_opts = {'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192', }],
            'outtmpl': 'audio.%(ext)s'}  # options for the 'youtube_dl'


def format_name(toFormat):  # format name uniformly everywhere for filenames
    return toFormat.replace("*", "").replace("'", "").lower()


def scan_imgs_folder(output):  # scan imgs folder than redirect array to 'output' parameter
    for (dir_path, dir_names, names) in walk("imgs"):
        output.extend(names)
        break


def calc_dim(path):  # calculate height and width for images to fit correctly in the video
    width_source, height_source = Image.open(path).size
    x_video_res = video_resolution[0]
    y_video_res = video_resolution[1]
    img_height = 0
    img_width = 0

    if height_source >= width_source:
        img_height = y_video_res
        img_width = (y_video_res / height_source) * width_source
    if img_width > x_video_res:
        img_width = x_video_res
        img_height = (x_video_res / width_source) * height_source

    if width_source > height_source:
        img_width = x_video_res
        img_height = (x_video_res / width_source) * height_source
    if img_height > y_video_res:
        img_height = y_video_res
        img_width = (y_video_res / height_source) * width_source

    return img_width, img_height


def download_image(to_download):  # function for downloading the image with 'to_download' the word to search
    log_image = open(outDirectory + '/logs/images.log', 'w')
    sys.stdout = log_image  # redirect output to file for better looking return when running

    imgs_arr = []  # reset files array
    scan_imgs_folder(imgs_arr)  # put each images in files array

    formatted_name = format_name(to_download)
    if not any(formatted_name + "." in s for s in imgs_arr):  # if doesn't have the image in folder
        google_img = google_images_download.googleimagesdownload()  # create shortcut for 'googleimagelibrary'
        if len(formatted_name) > 1:  # define what to search
            search = formatted_name + " word image"
        else:
            search = formatted_name + " letter"
        google_img.download(
            {"keywords": search, "limit": 1, "no_directory": "1", "output_directory": "imgs",
             "prefix": formatted_name + ".", "silent_mode": 1})  # do the search

        sys.stdout = sys.__stdout__  # restore output to console

        imgs_arr = []  # reset files array
        scan_imgs_folder(imgs_arr)  # rescan imgs after download
        # checking all information related to the download image
        for image_filename in imgs_arr:
            if formatted_name + "." in image_filename:
                word_formatted = formatted_name[:-8] if "clipart" in formatted_name else formatted_name
                try:
                    # checking some extensions that are not usable
                    image_ext = image_filename[-5:] if "jpeg" in image_filename else image_filename[-4:]
                    if "gif" in image_ext or "GIF" in image_ext or "svg" in image_ext or "webp" in image_ext:
                        # if forbidden extension, delete image then re-download and add 'stock' to get different images
                        print(" - Wrong format", end="")
                        os.remove("imgs/" + image_filename)
                        download_image(word + " clipart")
                        break
                    else:
                        # image is good so rename it correctly
                        rename("imgs/" + image_filename, "imgs/" + word_formatted + image_ext)
                        img_downloaded.append(word)
                        break
                except (IOError, SyntaxError) as e:
                    # happen when file is corrupt or something like that
                    print("   ERROR, delete '" + image_filename + "'")
                    os.remove("imgs/" + image_filename)
                    break
    else:
        sys.stdout = sys.__stdout__  # restore output to console


# begin
print("########################################################################")
print(Figlet(font='Small').renderText('butEveryWord\nIsAGoogleImage'))
print("########################################################################")

print("\nHello !\nWelcome to the 'butEveryWordIsAGoogleImage' generator")

video_link = input("Music's Link (Youtube link): ")  # ask for the youtube link
if video_link == "":
    video_link = "https://www.youtube.com/watch?v=X_nJ5ksFVbg"  # if no input set link to 'y2k & bbno$ - lalala' song
video_ID = video_link.split('=')[1]  # extract video id from url

sys.stdout = out = StringIO()  # disable output bc youtube_dl speak too much for nothing
video_infos = youtube_dl.YoutubeDL(ydl_opts).extract_info(video_link, download=False)
video_title = video_infos.get('title', None)  # extract video title from request
video_title.replace(" (", "(").replace(") ", ")")  # prepare title for removing all parentheses
for forbidden in whatsForbidden_regex:  # foreach forbidden characters
    video_title = re.sub(forbidden, "", video_title)  # remove
video_thumbnail = video_infos.get('thumbnail', None)  # extract link of the video's thumbnail
sys.stdout = sys.__stdout__  # re-enable output

title_song = input("Music's Title [" + video_title + "]: ")  # ask for title to show
if title_song == "":  # if no input put 'video_title' directly
    if video_title != "":
        title_song = video_title
    else:  # if by any chances cannot retrive video title
        title_song = "Unknown - Unknown"

fps = input("Video's fps [30]: ")  # ask for framerate
if fps == "":  # default 30fps
    fps = 30
else:
    fps = int(fps)

print("Resolution: ")
width = input("   width [1280] = ")  # ask for width
if width == "":
    width = 1280
else:
    width = int(width)
height = input("   height [720] = ")  # ask for height
if height == "":
    height = 720
else:
    height = int(height)

video_resolution[0] = width
video_resolution[1] = height

print("")  # presentation

# set vars additional vars in function of inputs
outDirectory = "outs/" + title_song
ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
            'preferredquality': '192', }], 'outtmpl': outDirectory + '/audio.%(ext)s'}

# if music directory exist ask for replace
if os.path.isdir(outDirectory):
    choice = input("'" + title_song + "' already exist. Erase and restart ? [Y/n]: ")
    if choice == "" or choice == "Y" or choice == "y":
        shutil.rmtree(outDirectory)
        os.mkdir(outDirectory)
        print("")
    else:
        print("Okay, no problem. Bye !")
        exit(0)
else:
    os.mkdir(outDirectory)
os.mkdir(outDirectory + "/logs")

# download original thumbnail
print("Getting original thumbnail...", end="")
with open(outDirectory + '/originalThumb_blur.jpg', 'wb') as handle:
    response = requests.get(video_thumbnail, stream=True)
    if not response.ok:
        print(response)
    for block in response.iter_content(1024):
        if not block:
            break
        handle.write(block)
# blur it !
image = io.imread(fname=outDirectory + '/originalThumb_blur.jpg')
blurred = filters.gaussian(image, sigma=(5, 5), truncate=3.5, multichannel=True)
sys.stderr = errors = StringIO() # disable output bc warnings are ugly
io.imsave(outDirectory + '/originalThumb_blur.jpg', blurred)
sys.stderr = sys.__stderr__  # restore output
print("\rOriginal Thumbnail ✓")

# get subtitles from youtube with 'YouTubeTranscriptApi'
print("Getting subtitles...", end="")
subs = YouTubeTranscriptApi.get_transcript(video_ID, languages=['fr', 'fr - Français', 'en', "Anglais - en"])

# process each subtitles information and sort them in 'words_infos' array with 'duration, start, text'
print("\rProcessing subtitles...", end="")
for i in subs:
    duration = float(list(i.items())[2][1])
    start = list(i.items())[1][1]
    actualTime = 0
    sub_text = list(i.items())[0][1]
    # filter all forbidden characters
    for forbidden in whatsForbidden_regex:
        sub_text = re.sub(forbidden, "", sub_text)
    for forbidden in whatsForbidden:
        sub_text = sub_text.replace(forbidden, "")
    sub_text = sub_text.replace("\n", " ")
    # avoid all comments in subs such like parentheses
    if "(" in sub_text or ")" in sub_text:
        continue
    characters = len(sub_text.replace(" ", ""))
    if characters > 0:
        letterDuration = duration / characters  # calculate a letter duration
        # for each words add them to 'word_infos' array with start and calculated duration
        for word in sub_text.split():
            words_infos.append(word + ";" + str(letterDuration * len(word)) + ";" + str(start + actualTime))
            actualTime += letterDuration * len(word)
print("\rSubtitles ✓")

# download mp3 from youtube link with 'youtube_dl'
print("Downloading MP3...", end="")
fsock = open(outDirectory + '/logs/mp3.log', 'w')
sys.stdout = fsock  # redirect output to log file
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_link])
sys.stdout = sys.__stdout__  # restore output
fsock.close()
print("\rMP3 ✓")

# download all images needed for the music
print("Downloading Images", end="")
files_arr = []; scan_imgs_folder(files_arr)
words = []
for word in words_infos:  # extract each word from 'word_infos' to 'words' array
    words.append(word.split(';')[0].lower())
words_clean = list(dict.fromkeys(words))  # remove duplicates
i = 1
for word in words_clean:  # for each words said
    print("\rDownloading Images - " + str(i) + "/" + str(len(words_clean)) + " " + word, end=" ")
    download_image(word)  # execute function that download the image defined at the top
    i += 1
print("\rImages ✓")
if len(img_downloaded) > 0:  # if script download images
    if len(img_downloaded) <= 30:  # just decide in function of number of downloaded if showing the list
        print("   " + str(len(img_downloaded)) + " images downloaded - " + str(img_downloaded))
    else:
        print("   " + str(len(img_downloaded)) + " images downloaded. Note that there's more than 30. ", end="")
    pause = input("   Press Enter when you checked them...")
    print("\r", end="")


# calculate all elements properties
print("Preparing video...", end="")
audio = AudioFileClip(outDirectory + "/audio.mp3").set_start(lengthCredits)
musicLength = audio.duration
background = ColorClip(size=(video_resolution[0], video_resolution[1]), color=[0, 0, 0], duration=lengthCredits + musicLength).set_start(0)  # constant black bg
# copyrights
tutozz = ImageClip("res/tutozz.png").set_duration(musicLength).set_start(lengthCredits).set_pos(( video_resolution[0]*0.85 , video_resolution[1]*0.88)).resize(width=video_resolution[0]*0.11).set_opacity(0.6)
arobase_left = ImageClip("res/arobase_left.png").set_duration(musicLength).set_start(lengthCredits).set_pos((video_resolution[0]*0.09, video_resolution[1]*0.78)).resize(width=video_resolution[0]*0.156).set_opacity(0.3)
arobase_right = ImageClip("res/arobase_right.png").set_duration(musicLength).set_start(lengthCredits).set_pos((video_resolution[0]*0.73, video_resolution[0]*0.22)).resize(width=video_resolution[0]*0.156).set_opacity(0.3)
# start credits
silence = AudioFileClip("res/2secsilence.mp3").set_start(0)
x, y = calc_dim(outDirectory + "/originalThumb_blur.jpg")
xpos = (video_resolution[0] - x) / 2
thumbnail = ImageClip(outDirectory + "/originalThumb_blur.jpg").set_duration(lengthCredits).set_start(0).set_pos((xpos, 0)).resize(width=x, height=y).set_opacity(0.7)
overlay = ImageClip("res/credit.png").set_duration(lengthCredits).set_start(0).set_pos((0, 0)).resize(width=video_resolution[0]).set_opacity(1)
songTitle = TextClip(title_song, color="white", method='caption', align='center', font="AvantGarde-Demi",size=(video_resolution[0], video_resolution[1]*0.09)).set_duration(lengthCredits).set_start(0).set_pos((video_resolution[0]*0.014, video_resolution[1]*0.71))

# create list for elements and adding basics stuff
elements = [background, thumbnail, overlay, songTitle]

files = []; scan_imgs_folder(files)  # get all imgs that I already have in list

i = 1
missingWords = []
for word_infos in words_infos:  # for each words to process
    # extract infos of word_infos
    word = word_infos.split(';')[0];
    duration = float(word_infos.split(';')[1]);
    start = float(word_infos.split(';')[2])
    filename = format_name(word)
    print("\rCreating video - " + str(i) + "/" + str(len(words)) + " - '" + filename + "'", end=" ")
    # if image is missing try to download it again
    if filename+".jpg" not in files:
        download_image(format_name(word))

    img = ImageClip("imgs/blank.png").set_duration(duration).set_start(lengthCredits + start).set_pos(("center", "center"))  # set default img in case of
    try:
        missingWords.append(filename)
        for file in files:  # for each image in folder
            if filename + "." in file and filename + "." not in file[1:]:  # if find corresponding
                x, y = calc_dim("imgs/" + file)  # calc dimensions
                img = ImageClip("imgs/" + file).set_duration(duration).set_start(lengthCredits + start).set_pos(("center", "center")).resize(height=y, width=x)
                missingWords.remove(filename)
                break
    except (ValueError) as e:
        print("Error while reading: " + str(e))
        missingWords.append(filename)

    elements.append(img)  # add image to array of video elements
    i += 1

# adding copyright elements at end for being on top of everything
elements.extend([tutozz, arobase_left, arobase_right])

# compose element in finalclip
video = CompositeVideoClip(elements)
final_audio = CompositeAudioClip([silence, audio])
final_clip = video.set_audio(final_audio)

# check if while adding it's missing words
missingWords = list(dict.fromkeys(missingWords))
if len(missingWords) >= 1:
    print("")
    print("   It miss words: " + str(missingWords), end="")
    pause = input("   Press enter to continue...")
print("\rVideo ✓")


# do the export
print("Exporting...", end="")

# redirect all errors and basic outputs stuff to vars
sys.stderr = errors = StringIO()
sys.stdout = out = StringIO()

try:
    final_clip.write_videofile(outDirectory + "/video.mp4", fps=fps, verbose=False)  # magic command for the export

    # restore output and errors to default
    sys.stdout = sys.__stdout__;
    sys.stderr = sys.__stderr__

    # write out outputs to log files
    f = open(outDirectory + "/logs/export.log", "w"); f.write(out.getvalue()); f.close()
    f = open(outDirectory + "/logs/export.log", "a"); f.write(errors.getvalue()); f.close()
    print("\rExported ✓")

    # generate thumbnail by picking the first frame of the video
    print("Generating Thumbnail...", end="")
    video = cv2.VideoCapture(outDirectory + "/video.mp4")
    success, image = video.read()
    while success:
        filename = outDirectory + '/thumbnail.jpg';
        cv2.imwrite(filename, image)
        break
    video.release()
    print("\rThunmbail ✓")

    # generate text file for speeding up uploads on different platforms
    print("Generating text...", end="")
    infos = \
        "########################################################################" + \
        Figlet(font='Small').renderText('butEveryWord\nIsAGoogleImage') + \
        "########################################################################" + \
        "\n" + \
        "Video Link: " + video_link + "\n\n" + \
        "Title: " + str(title_song) + " but every word is a google image\n\n" + \
        "   Description: \nJust '" + str(title_song) + "' but every word is a google image\nFeel free to post in comments what song you would like to see\n\nGenerated by the 'But Every Word Is A Google Image' bot created by Tutozz\n\nOfficial Twitter: https://www.twitter.com/butEveryWord\nOfficial Instagram: https://www.instagram.com/butEveryWord\n\n" + \
        "   Tags:\n" + str(title_song) + ", But every word is a google image, ButEveryWordIsAGoogleImage, image, lyrics, tutozz\n\n"
    f = open(outDirectory + "/infos.txt", "w"); f.write(infos); f.close()  # write out to file
    print("\rText ✓")

    shutil.rmtree(outDirectory + "/logs")  # remove log folder bc it ended correctly

except ValueError as e:  # in case of error (often during export)
    # reset default outputs
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    # write all logs
    h = open(outDirectory + "/logs/export.log", "w"); h.write(out.getvalue()); h.close()
    f = open(outDirectory + "/logs/export.log", "a"); f.write(errors.getvalue()); f.close()

    # extract last progress status from logs
    f1 = open(outDirectory + "/logs/export.log", "r"); status_last = f1.readlines()[-1]; f1.close()
    status_last = status_last.split("|")[0] + " |" + re.sub('\d', '-',status_last.split("|")[1].replace(" ", "-")) + "|" + status_last.split("|")[2]
    print("\n   ERROR at -> " + status_last[4:-35])  # print

    # extract infos
    frames = int(status_last.split("|")[2].split("/")[1].split(" ")[0])
    current_frames = int(status_last.split("|")[2].split("/")[0].split(" ")[1])
    video_length = musicLength + lengthCredits
    current_timestamp = (video_length / frames) * current_frames

    i = 0
    for word_infos in words_infos: # test for each word if they correspond to timing calculated
        word = word_infos.split(';')[0]
        start_word = float(word_infos.split(';')[2])
        if start_word >= current_timestamp:
            for e in subs:  # for each subtitles
                duration_sub = float(list(e.items())[2][1])
                start_sub = list(e.items())[1][1]
                end_sub = start_sub + duration_sub
                if start_sub <= start_word <= end_sub:  # if word in sub alias 'e'
                    sentence = list(e.items())[0][1]  # extract text
                    # remove all forbidden characters
                    for forbidden in whatsForbidden_regex:
                        sentence = re.sub(forbidden, "", sentence)
                    for forbidden in whatsForbidden:
                        sentence = sentence.replace(forbidden, "")
                    sentence = sentence.replace("\n", " ")
                    break

            next_word = words_infos[i + 1].split(';')[0]  # get next word
            next_start = float(words_infos[i + 1].split(';')[2])  # get next word start

            if i > 0:  # if problem doesn't come from the first word
                previous_word = words_infos[i - 1].split(';')[0]  # get word before
                previous_word = float(words_infos[i - 1].split(';')[2])  # get before word start
                print("   Maybe it comes from '" + str(previous_word) + "','" + str(word) + "' or '" + str(next_word) + "' in sentence \n      '" + sentence + "'")
            else:
                print("   Maybe it comes from '" + str(word) + "' or '" + str(next_word) + "' in sentence \n      '" + sentence + "'")

            print("      errorTime = " + str(round(current_timestamp, 2)) +
                  " | previous_word:" + str(round(float(previous_word), 2)) +
                  " | current_word:" + str(round(float(start_word), 2)) +
                  " | next_word:" + str(round(float(next_start), 2)))
            break
        i += 1

print("")


# Thanks to everybody who read to this
# © Tutozz | Written in end of 2019
