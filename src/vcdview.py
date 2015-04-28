import os
import urllib
import cgi
import StringIO
import re
#from parse_vcd import *
import json
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
        #for b in blobstore.BlobInfo.all():
         #   self.response.out.write('<li><a href="/serve/%s' % str(b.key()) + '">' + str(b.filename) + '</a>') -- to display all the files uploaded till now.

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        #self.response.out.write("Hello")
        upload_files = self.get_uploads('file')
        blob_info = upload_files[0]        
        self.redirect('/serve/%s' % blob_info.key())
       
        #self.redirect('/')
        #filesize = blob_info.getSize()
        #file_info = blobstore.parse_file_info(cgi.FieldStorage()['file'])
        #'''file_info = self.get_file_infos()[0]
        #rtn_data = {
        #    "filename": file_info.filename,
         #   "content_type": file_info.content_type,
          #  "creation": file_info.creation,
          #  "size": file_info.size,
          #  "md5_hash": file_info.md5_hash,
          #  "gs_object_name": file_info.gs_object_name
        #}
        #data = fetch_data(file_info,0,2227)
        #self.response.out.write(rtn_data.values())
        #rtnval = rtn_data.values()
        #self.response.out.write(rtnval[1]) #prints the filename of the uploaded file
        #self.response.out.write(rtnval[3])
        
        #output = StringIO.StringIO()
        #upload = self.request.get('file')
        #output.write(upload)
        #self.response.write(output.getvalue())'''
        
       
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, blob_key):
        blob_key=str(urllib.unquote(blob_key)) #extracting the blob_key from blob info
        blob_reader = blobstore.BlobReader(blob_key) #blob_reader is similar to the file pointer
        value = blob_reader.read() #The complete file is read in a string
        valuelines = value.splitlines() #It is obtained as a list of lines
        if not blobstore.get(blob_key):
            self.error(404)
        else:
            vcdread = vcd_reader(valuelines) #The file is parsed
            signal_dict = vcdread.signal_symbol_dict
            transaction_dict = vcdread.transitions_dict
            signals = signal_dict.keys() #The value of all the signals
            signal_values = signal_dict.values()
            transacting_signals = transaction_dict.keys()
            #display_array=['/dut/clk','/dut/data_path', '/inputs_ready', '/dut/quotient[16:0]', '/dut/divider_ready', '/i', '/dut/inputs_ready', '/output_accept']
            trans_details=vcdread.create_json_to_display_waveforms(signals,vcdread.signal_symbol_dict,vcdread.transitions_dict)
            display_signals=trans_details.keys()
            display_values=trans_details.values()
            x=display_values[0]
            template_values = {
            'signal_dict': signal_dict,
			'transaction_dict': transaction_dict,
            'signals':signals,
            'signal_values':signal_values,
            'transacting_signals':transacting_signals,
            'trans_details':trans_details,
            #'display_array':display_array,
            'display_signals':display_signals,
            'display_values':display_values,
            'x':x,
            }
            path = os.path.join(os.path.dirname(__file__),'index.htm')
            self.response.out.write(template.render(path, template_values))
            #self.response.out.write(json.dumps(signal_dict))
            #self.send_blob(blobstore.BlobInfo.get(blob_key), save_as=True)



    
application = webapp.WSGIApplication([('/', MainPage),('/upload', UploadHandler),
           ('/serve/([^/]+)?', ServeHandler)], debug=True)


def main():
    run_wsgi_app(application)


class vcd_reader:
    """vcd_reader is the class which parses the vcd file
    
    Syntax:
        vcd_file=vcd_reader(FILEPATH)
        
        The following objects are available
        
        vcd_file.transitions_dict 
            A dictionary which has symbol as key and in the vlaue, it has [[timestamps],[signal_values]] pairs
        vcd_file.signal_symbol_dict
            A dictionary which has all signals as keys and symbols as values. [Hierarchy info preserved]
        vcd_file.timescale_string
            A string which stores the timescale string as in vcd
        vcd_file.end_time
            A scalar which has the integer value of when the vcd file is getting ended. (Last timestamp)
        vcd_file.date
            Date on which vcd was created
        vcd_file.version
            A scalar which has the version information of the vcd file. 
            Usually has the tool information which had dumped the vcd file.
        
        The following functions are available on the parsing.
        vcd_file.read_file --> VCD parsing is done by this completely. Most of above objects are created here
        vcd_file.symbols(array) --> Give a array of names to get the symbols. A dict is returned
        vcd_file.time_query_transitions(array,start_time,stop_time) --> Transitions between start and stop for given signals
        vcd_file.value_at(array_of_names,timestamp=1) --> returns value at timestamp for all the queried signals
    """
    def __init__(self,file_content):
        """INIT function for vcd_reader class. 
        Calls read_file function and parses the entire file.
        mainly, 9signal_symbol dictionary and transition dictionary are created"""
        self.transitions_dict=self.read_file(file_content)
        #pass
        
    def read_file(self,file_content):
        """Parses the file and returns the signal-symbol pair and transition history"""
        self.signal_symbol_dict={}
        transition_dict={}
        current_scope='' #indicates the current level, as to what level in the module we are
        change_dump_started=0 #indicates when to start reading the file
        #with open(file_name) as f:
            #file_content=f.readlines()
            #change_dump_started=0 #indicates when to start reading the file
        for line_no in range(len(file_content)):
            if re.match('^\$date',file_content[line_no]):
                self.date=file_content[line_no+1]
            if re.match('^\$version',file_content[line_no]):
                self.version=file_content[line_no+1]
            if re.match('^\$timescale',file_content[line_no]):
                self.timescale_string=file_content[line_no+1]
                matchObj=re.match('^[\s\t]*(\d+)\s*(\w+)',self.timescale_string)
                #[\s\t - indicates spaces or tabs, and * indicates may/may not exist, 
                #followed by a digit which may or may not be followed by spaces and w indicates word/character, can be alphanumeric or underscore
                timescale_dict={'fs':1e-15,'ps':1e-12,'ns':1e-9,'us':1e-6,'ms':1e-3}
                if matchObj:
                    timescale=float(matchObj.group(1))*timescale_dict[matchObj.group(2)]
                    #print timescale
            matchObj=re.match(r'^\$scope\s+module\s+(\w+)\s+\$end',file_content[line_no])
            if matchObj:
                current_scope=current_scope+'/'+matchObj.group(1)
                #print current_scope
            matchObj=re.match(r'^\$upscope',file_content[line_no])
            if matchObj:
                try:
                    print self.timescale_string
                except NameError:
                    print "Timescale not defined"

                scopes=current_scope.split('/')
                current_scope=''
                for scope in range(len(scopes)-1):
                    if scopes[scope]!='':
                        current_scope=current_scope+'/'+scopes[scope]
                #print current_scope
            matchObj=re.match(r'^\$var\s+(\w+)\s+(\d+)\s+(\S+?)\s+(\S+)\s+\$end$', file_content[line_no])
            #reading the lines starting with var and assigning to signal_symbol_dict
            if matchObj:
                #print matchObj.group(3)
                #print matchObj.group(2)
                current_signal=current_scope+'/'+matchObj.group(4)
                self.signal_symbol_dict[current_signal]=matchObj.group(3)
                transition_dict[matchObj.group(3)]=[[],[]]
    
            matchObj=re.match(r'^\$dumpvars', file_content[line_no])
            matchObj2=re.match(r'^\$enddefinitions', file_content[line_no])
            if matchObj or matchObj2:
                change_dump_started=1
                timestamp=0
                #print "Change dump started"

            matchObj=re.match(r'^\#(\d+)', file_content[line_no])
            if matchObj:
                timestamp=int(matchObj.group(1))
                self.end_time=timestamp
                
            matchObj=re.match(r'^(\S)(\S+)$',file_content[line_no])#capital S is non-space
            if matchObj and change_dump_started==1 and matchObj.group(2) in transition_dict.keys() and matchObj.group(1)!='#':
                transition_dict[matchObj.group(2)][0].append(timestamp)
                transition_dict[matchObj.group(2)][1].append(matchObj.group(1))               
            
            matchObjBus=re.match(r'^b(\w+) (\S+)$',file_content[line_no])#make it S+ everywhere
            if matchObjBus and change_dump_started==1 and matchObjBus.group(2) in transition_dict.keys() and matchObjBus.group(1)!='#':
                transition_dict[matchObjBus.group(2)][0].append(timestamp)
                transition_dict[matchObjBus.group(2)][1].append(matchObjBus.group(1)) 
        return transition_dict 

    def symbols(self,array_of_names):
        """
        Usage: 
            symbols=vcd_reader.symbols(array)
            where array=['/clk','/dut/reset']
            
        Returns a dictionary with signal-symbol pairs
        When a list of names is sent, make sure you have '/' at the beginning of the hierarchy.
        For eg. query for ['/clk'] and not ['clk']"""
        dict_to_return={}
        for item in array_of_names:
            dict_to_return[item]=self.signal_symbol_dict[item]
        return dict_to_return

    def time_query_transitions(self,array_of_names,start_time,stop_time):
        """
        Usage:
            transitions_within_a_time_range=vcd_reader.time_query_transitions(array_of_names,start_time,stop_time)
            
            Here only the transitions of the signals in array_of_names between 
            start_time and stop_time will be returned
        """
        symbols_queried=self.symbols(array_of_names)
        dict_to_return={}
        for sig in symbols_queried.values():
            dict_to_return[sig]=[[],[]]
            #sym=self.signal_symbol_dict[sig]
            timestamps=self.transitions_dict[sig][0]
            for index in range(len(timestamps)-1):
                if timestamps[index]>start_time and timestamps[index]<stop_time:
                    dict_to_return[sig][0].append(timestamps[index])
                    dict_to_return[sig][1].append(self.transitions_dict[sig][1][index])
        return dict_to_return

    def value_at(self, array_of_names,timestamp=1):
        """This function gives the value of any signal at a particular time instance
        
        Say vcd file is already read as vcd_file=vcd_reader(FILEPATH)
        Then vcd_file.value_at(array,timestamp) returns a dictionary.
        Array can be list of names. timestamp is optional(default is '1').
        
        Dictionary returned will have symbol as the key and value at that particular time as value
        """
        
        symbols_queried=self.symbols(array_of_names)
        dict_to_return={}
        for sig in symbols_queried.values():
            #print sig
            for i in range(len(self.transitions_dict[sig][0])):
                time=self.transitions_dict[sig][0][i]
                if time<timestamp:
                    value=self.transitions_dict[sig][1][i]
                else:
                    #print sig,value
                    break
            dict_to_return[sig]=value
        return dict_to_return
        
    def create_json_to_display_waveforms(self,array_of_names,signal_symbol_dict,transitions_dict):
        dict_to_return={}
        voltage_val=0;
        #json_string=json_string+'{"type":"line","dataPoints":[';       
        for name in array_of_names:
			json_string='{"name":"'+name+'","showInLegend": "true",'
			json_string=json_string+'"type":"line","dataPoints":['
			symbol=self.signal_symbol_dict[name]
			x_y_pairs=[]
			for i in range(len(self.transitions_dict[symbol][0])-1):
				#print self.transitions_dict[symbol][1][i]
				x_y_pairs.append((self.transitions_dict[symbol][0][i],str(int(self.transitions_dict[symbol][1][i])+voltage_val)))
				x_y_pairs.append((self.transitions_dict[symbol][0][i+1],str(int(self.transitions_dict[symbol][1][i])+voltage_val)))
			x_y_pairs.append((self.transitions_dict[symbol][0][len(self.transitions_dict[symbol][0])-1],str(int(self.transitions_dict[symbol][1][len(self.transitions_dict[symbol][0])-1])+voltage_val)))
			x_y_pairs.append((self.end_time,str(int(self.transitions_dict[symbol][1][len(self.transitions_dict[symbol][0])-1])+voltage_val)))
			# creating string in json object
			for time,val in x_y_pairs:
				if time == 0:
					json_string=json_string+'{"x":'+str(time/1000000)+',"y":'+val+',"indexLabel": "'+name+'","indexLabelLineThickness":1}'
				else:
					json_string=json_string+'{"x":'+str(time/1000000)+',"y":'+val+'}'
				if x_y_pairs[-1]==(time,val):
					break
				else:
					json_string=json_string+','
			json_string=json_string+']}'
			print json_string
			voltage_val=voltage_val+1.25
			dict_to_return[name]=json_string
	return(dict_to_return)


if __name__ == "__main__":
    main()
