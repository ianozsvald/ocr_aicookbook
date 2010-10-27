#!/usr/local/bin/python2.5
# File: /var/www/yourapp/app.wsgi

# VERY hacky bottle.py server for ocr.aicookbook.com
# it'll read an image and return English and French text and mp3s

import os
import urllib
import urllib2
import random
import md5
from PIL import Image
import json
# Change working directory so relative paths (and template lookup) work again
if os.uname()[1].find('webfaction.com') > -1:
    # need to play with path names to make it deploy remotely
    os.chdir(os.path.dirname(__file__))

import bottle
from bottle import route, run, request, send_file

def get_url(URL, fileid, filename_tif):
    """Retrieve URL, save as .tif file"""
    filename = os.path.join('data', fileid + '.jpg')
    urllib.urlretrieve(URL, filename)
    im = Image.open(filename)
    im.save(filename_tif, 'TIFF')
    os.remove(filename)
    return filename_tif

@route('/upload', method='POST')
def do_upload():
    data = request.files.get('data')
    if data.file:
    	fileid = 'img_%s' % (md5.md5(data.filename).hexdigest())		
	filename_tif = os.path.join('data', '%s.tif' % (fileid))

        raw = data.file.read() # This is dangerous for big files
        filename = data.filename
        filename = os.path.join('data', filename)
        f = file(filename, 'wb')
        f.writelines(raw)
        f.close()
        im = Image.open(filename)
        im.save(filename_tif, 'TIFF')
        os.remove(filename)
        return do_ocr(filename_tif, fileid)

    return "Problem with image upload"


@route('/version')
def index():
    return "<p>Version 0.2</p>"

@route('/')
@route('/index.html')
def index():
    url = '<H1>Tesseract-based O.C.R. web service</H1>'
    url += '<p>Call using a URL to an image e.g. </p>'
    url += '<p><a href="/get_remote_img_and_translate?URL=http://farm2.static.flickr.com/1306/4701412966_7306b84cb5.jpg">http://ocr.aicookbook.com/get_remote_img_and_translate?URL=http://farm2.static.flickr.com/1306/4701412966_7306b84cb5.jpg/</a></p>'
    url += '<p>OR upload a filename here-></p>'
    url += """
    <form action="/upload" method="post" enctype="multipart/form-data">
  <input type="file" name="data" />
  <input type="submit" value="Upload image">
</form>
"""
    url = url + '<p><img src="http://farm2.static.flickr.com/1306/4701412966_7306b84cb5.jpg" alt="Test image" /></p>'
    return url

@route('/static/:filename#.*#')
def static_file(filename):
    # sneaky way to see the processed file
    # e.g. /static/img_71852c140cbee98a561ab5a83e40cd74.tif
    # if you're running locally, you'll have the file name
    send_file(filename, root='/Users/ian/Documents/OpticalCharacterRecognition/ocr_aicookbook/data/')

def do_ocr(filename_tif, fileid):
    cmd = 'tesseract %s %s -l eng' % (filename_tif, fileid)
    #print "---", cmd
    os.system(cmd) # awful approach, ought to use popen style
    tesseract_result = fileid+'.txt'
    input_file = open(tesseract_result)
    lines = input_file.readlines()
    text_english = " ".join([x.strip() for x in lines])
    os.remove(tesseract_result)
    return text_english

@route('/do') # deprecated, kept for Emily's first app for now
@route('/get_remote_img_and_translate')
def get_remote_and_translate():
    URL = request.GET.get('URL', None)
    if URL is None:
        return 'ERROR: must pass ?URL=http://blah.com/img.jpg'
    else:
        if not os.path.exists('data'):
            os.mkdir('data')

	fileid = 'img_%s' % (md5.md5(URL).hexdigest())		
	filename_tif = os.path.join('data', '%s.tif' % (fileid))
	if not os.path.exists(filename_tif):
            filename_tif = get_url(URL, fileid, filename_tif)
        text_english = do_ocr(filename_tif, fileid)

        # escape, google translate, wrap with text to speech
        escaped_english = text_english.replace(' ', '%20')
	translate_fr = 'http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&q=%s&langpair=en|fr' % (escaped_english)
	text_french = ""
	try:
	    translated_json = urllib2.urlopen(translate_fr).readlines()[0]
	    text_french = json.read(translated_json)['responseData']['translatedText']
	except urllib2.HTTPError:
	    pass

        # build dictionary of result, return to user
	d = {}
	d['text_english'] = text_english
	d['text_french'] = text_french
	tts_english = "http://translate.google.com/translate_tts?tl=en&q=%s" % (text_english.replace(' ','+'))
	d['tts_english'] = tts_english
	tts_french = "http://translate.google.com/translate_tts?tl=fr&q=%s" % (text_french.replace(' ','+'))
	d['tts_french'] = tts_french
	j = json.write(d)
        return j



# ... add or import your bottle app code here ...
# Do NOT use bottle.run() with mod_wsgi
if __name__ == "__main__":
    bottle.debug(True)
    run(host='localhost', port=8080)
else:
    application = bottle.default_app()

