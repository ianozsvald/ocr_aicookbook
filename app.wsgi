#!/usr/local/bin/python2.5
# File: /var/www/yourapp/app.wsgi
import os
import urllib
import urllib2
import random
import md5
from PIL import Image
import json
# Change working directory so relative paths (and template lookup) work again
os.chdir(os.path.dirname(__file__))

import bottle
from bottle import route, run, request


def get_url(URL, fileid, filename_tif):
    """Retrieve URL, save as .tif file"""
    filename = fileid + '.jpg'
    urllib.urlretrieve(URL, filename)
    im = Image.open(filename)
    #filename_tif = fileid+'.tif'
    im.save(filename_tif, 'TIFF')
    return filename_tif

@route('/version')
def index():
    return "<p>Version 0.1</p>"

@route('/')
@route('/index.html')
def index():
    url = '<H1>Tesseract-based O.C.R. web service</H1>'
    url += '<p>Call using a URL to an image e.g. </p>'
    url += '<p><a href="/do?URL=http://farm2.static.flickr.com/1306/4701412966_7306b84cb5.jpg">http://ocr.aicookbook.com/do?URL=http://farm2.static.flickr.com/1306/4701412966_7306b84cb5.jpg/</a></p>'
    url = url + '<p><img src="http://farm2.static.flickr.com/1306/4701412966_7306b84cb5.jpg" alt="Test image" /></p>'
    return url

@route('/do')
def do():
    # assume that URL is a fileid for now...
    #fileid = 'img_%d' % (random.randint(0,100)) #'1'
    #fileid = 'img_%s' % (md5.md5(URL).hexdigest())
    URL = request.GET.get('URL', None)
    if URL is None:
        return 'ERROR: must pass ?URL=http://blah.com/img.jpg'
    else:
	fileid = 'img_%s' % (md5.md5(URL).hexdigest())		
	filename_tif = '%s.tif' % (fileid)
	if not os.path.exists(filename_tif):
            filename_tif = get_url(URL, fileid, filename_tif)
        cmd = 'tesseract %s %s -l eng' % (filename_tif, fileid)
        #return "yes2", 
        #print "Executing:", cmd
        os.system(cmd)
        #return 'yes %s' % (cmd+','+URL)
        input_file = open(fileid+'.txt')
        lines = input_file.readlines()
        text_english = " ".join([x.strip() for x in lines])

	escaped_english = text_english.replace(' ', '%20')
	translate_fr = 'http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&q=%s&langpair=en|fr' % (escaped_english)
	text_french = ""
	try:
	    translated_json = urllib2.urlopen(translate_fr).readlines()[0]
	    text_french = json.read(translated_json)['responseData']['translatedText']
	except urllib2.HTTPError:
	    pass

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
application = bottle.default_app()

