import os
import urllib
import cgi
import StringIO
#import webapp2

#from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.api import files
#from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
#from google.appengine.ext import db

#class Shout(db.Model):
 #   message = db.StringProperty(required=True)
  #  when = db.DateTimeProperty(auto_now_add=True)


class MainPage(webapp.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')
        # The method must be "POST" and enctype must be set to "multipart/form-data".
        self.response.out.write('<html><body>')
        self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
        self.response.out.write('''Upload File: <input type="file" name="file"><br> <input type="submit"
            name="submit" value="Submit"> </form></body></html>''')
        for b in blobstore.BlobInfo.all():
            self.response.out.write('<li><a href="/serve/%s' % str(b.key()) + '">' + str(b.filename) + '</a>')

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        self.response.out.write("Hello")
        upload_files = self.get_uploads('file')
        blob_info = upload_files[0]
        blob_reader = blobstore.BlobReader(blob_info)
        value = blob_reader.read()
        self.response.out.write("<br />" + value)        
        #self.redirect('/serve/%s' % blob_info.key())
        #self.redirect('/')
        #filesize = blob_info.getSize()
        #file_info = blobstore.parse_file_info(cgi.FieldStorage()['file'])
        '''file_info = self.get_file_infos()[0]
        rtn_data = {
            "filename": file_info.filename,
            "content_type": file_info.content_type,
            "creation": file_info.creation,
            "size": file_info.size,
            "md5_hash": file_info.md5_hash,
            "gs_object_name": file_info.gs_object_name
        }
        #data = fetch_data(file_info,0,2227)
        self.response.out.write(rtn_data.values())
        rtnval = rtn_data.values()
        #self.response.out.write(rtnval[1]) #prints the filename of the uploaded file
        #self.response.out.write(rtnval[3])
        
        output = StringIO.StringIO()
        upload = self.request.get('file')
        output.write(upload)
        self.response.write(output.getvalue())'''
        
       
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        blob_key=str(urllib.unquote(blob_key))
        if not blobstore.get(blob_key):
            self.error(404)
        else:
            self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)
    
    

        
        
application = webapp.WSGIApplication([('/', MainPage),('/upload', UploadHandler),
           ('/serve/([^/]+)?', ServeHandler)], debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
