import re

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
    def __init__(self,file_name):
        """INIT function for vcd_reader class. 
        Calls read_file function and parses the entire file.
        mainly, 9signal_symbol dictionary and transition dictionary are created"""
        self.transitions_dict=self.read_file(file_name)
        #pass
        
    def read_file(self,file_name):
        """Parses the file and returns the signal-symbol pair and transition history"""
        self.signal_symbol_dict={}
        transition_dict={}
        current_scope='' #indicates the current level, as to what level in the module we are
        with open(file_name) as f:
            file_content=f.readlines()
            change_dump_started=0 #indicates when to start reading the file
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
                print current_scope
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
        
