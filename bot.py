#!/usr/bin/env python
# tweepy-bots/bots/autoreply.py

import tweepy
import logging
from config import create_api
import time
import cv2
import random
import requests 
import shutil 




def face_detect(img, cname):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_hist = cv2.equalizeHist(img_gray)
    face_cascade = cv2.CascadeClassifier(cname)
    faces = face_cascade.detectMultiScale(img_hist)
    return faces


def avax_hat(fname, cname):
    img = cv2.imread(fname)
    faces = face_detect(img, cname)
    hats = [cv2.imread(f'img/hats/hat_{i+1}.png', -1) for i in range(3)]
    for face in faces:
        hat = random.choice(hats) 
        scale = face[3] / hat.shape[0] * 2  
        hat = cv2.resize(hat, (0, 0), fx=scale, fy=scale) 
        x_offset = int(face[0] + face[2] / 2 - hat.shape[1] / 2) 
        y_offset = int(face[1] - hat.shape[0] / 2)  
        x1 = max(x_offset, 0)
        x2 = min(x_offset + hat.shape[1], img.shape[1])
        y1 = max(y_offset, 0)
        y2 = min(y_offset + hat.shape[0], img.shape[0])
        hat_x1 = max(0, -x_offset)
        hat_x2 = hat_x1 + x2 - x1
        hat_y1 = max(0, -y_offset)
        hat_y2 = hat_y1 + y2 - y1
        alpha_h = hat[hat_y1:hat_y2, hat_x1:hat_x2, 3] / 255
        alpha = 1 - alpha_h
        for c in range(3):
            img[y1:y2, x1:x2, c] = alpha_h * hat[hat_y1:hat_y2, hat_x1:hat_x2, c] + alpha * img[y1:y2, x1:x2, c]
        cv2.imwrite(f'{fname.split("/")[-1]}', img)


def transform(fname):
    cname = 'data/haarcascade_frontalface_alt.xml'
    avax_hat(fname, cname)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def check_mentions(api, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline,
        since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        f = open("lasttweet.log", "w")
        f.write(str(new_since_id))
        f.close()
        logger.info(f"Answering to {tweet.user.name}")
        usr = tweet.user
        
        image_url = usr.profile_image_url_https
      
        image_url = image_url.replace("_normal","")
        logger.info(image_url)
        filename = "test_1.jpg"

        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(image_url, stream = True)

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True
            
            # Open a local file with wb ( write binary ) permission.
            with open(filename,'wb') as f:
                shutil.copyfileobj(r.raw, f)
        
            logger.info("Image sucessfully Downloaded")
            transform(filename)
            status = "Here is your hat."
            imagemedia = api.media_upload(filename=filename)

            api.update_status(
              status=status,
              in_reply_to_status_id=tweet.id,
              media_ids=[imagemedia.media_id]
            )
            #api.update_with_media(filename, status, in_reply_to_status_id = new_since_id)
        else:
            logger.info("Image Couldn\'t be retrieved")
        
       
    return new_since_id

def main():
    api = create_api()
    f = open("lasttweet.log", "r")
    since_id = int(f.read())
    while True:
        since_id = check_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(15)

if __name__ == "__main__":
    main()
