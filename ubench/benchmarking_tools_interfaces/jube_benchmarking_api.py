#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2015 EDF SA                                                 #
#                                                                            #
#  This file is part of UncleBench                                           #
#                                                                            #
#  This software is governed by the CeCILL license under French law and      #
#  abiding by the rules of distribution of free software. You can use,       #
#  modify and/ or redistribute the software under the terms of the CeCILL    #
#  license as circulated by CEA, CNRS and INRIA at the following URL         #
#  "http://www.cecill.info".                                                 #
#                                                                            #
#  As a counterpart to the access to the source code and rights to copy,     #
#  modify and redistribute granted by the license, users are provided only   #
#  with a limited warranty and the software's author, the holder of the      #
#  economic rights, and the successive licensors have only limited           #
#  liability.                                                                #
#                                                                            #
#  In this respect, the user's attention is drawn to the risks associated    #
#  with loading, using, modifying and/or developing or reproducing the       #
#  software by the user in light of its specific status of free software,    #
#  that may mean that it is complicated to manipulate, and that also         #
#  therefore means that it is reserved for developers and experienced        #
#  professionals having in-depth computer knowledge. Users are therefore     #
#  encouraged to load and test the software's suitability as regards their   #
#  requirements in conditions enabling the security of their systems and/or  #
#  data to be ensured and, more generally, to use and operate it in the      #
#  same conditions as regards security.                                      #
#                                                                            #
#  The fact that you are presently reading this means that you have had      #
#  knowledge of the CeCILL license and that you accept its terms.            #
#                                                                            #
##############################################################################
import os
import re
import sys
from subprocess import call, Popen, PIPE
import benchmarking_api as bapi
import time
import ubench.core.ubench_config as uconfig
import jube_xml_parser

class JubeBenchmarkingAPI(bapi.BenchmarkingAPI):

  def __init__(self,benchmark_name,platform_name):
    """ Constructor
    :param benchmark_name: name of the benchmark
    :type benchmark_name: str
    :type benchmark_path: str
    """
    bapi.BenchmarkingAPI.__init__(self,benchmark_name,platform_name)
    self.uconf=uconfig.UbenchConfig()
    self.benchmark_path_in = os.path.join(self.uconf.benchmark_dir,benchmark_name,benchmark_name+".xml")
    benchmark_dir = os.path.join(self.uconf.benchmark_dir,benchmark_name)
    benchmark_files = [file_b for  file_b in os.listdir(benchmark_dir) if file_b.endswith(".xml")]

    self.benchmark_path = os.path.join(self.uconf.run_dir,platform_name,benchmark_name)
    self.jube_xml_files = jube_xml_parser.JubeXMLParser(benchmark_dir,benchmark_files,self.benchmark_path,os.path.join(self.uconf.platform_dir,"platforms.xml"))
    self.jube_xml_files.load_platform_xml(platform_name)

  def analyse_benchmark(self,benchmark_id):
    """ Analyze benchmark results
    :param benchmark_id: id of the benchmark to be analyzed
    :type benchmark_id: int
    :returns: result directory absolute path
    :rtype: str
    :raises: IOError
    """
    old_path=os.getcwd()
    if(not os.path.isdir(self.benchmark_path)):
      raise IOError

    os.chdir(self.benchmark_path)
    output_dir = self.jube_xml_files.get_bench_outputdir()
    input_str='jube analyse ./'+output_dir+' --id '+benchmark_id
    analyse_from_jube=Popen(input_str,cwd=os.getcwd(),shell=True,stdout=PIPE)
    benchmark_results_path=''


    for line in analyse_from_jube.stdout:
      if ('Analyse data storage: ' in line):
        benchmark_results_path=os.path.join(self.benchmark_path,line[(line.find(':')+2):(line.find('analyse.xml'))])
        if benchmark_results_path=='':
          raise IOError

        # Restore working directory
      os.chdir(old_path)
    return benchmark_results_path


  def analyse_last_benchmark(self):
        """ Get last result from a jube benchmark.
        :returns: result directory absolute path, None if analysis failed.
        :rtype: str
        """
        try:
            return self.analyse_benchmark('last')
        except Exception:
            raise

  def get_results_root_directory(self):
        """ Returns benchmark results root directory
        :returns: result directory asbolut path
        :rtype: str
        """
        return os.path.join(self.benchmark_path,self.jube_xml_files.get_bench_outputdir())


  def get_log(self,idb=-1):
        """ Get a log from a benchmark run
        :param idb: id of the benchmark
        :type idb:int
        :returns: log
        :rtype:str
        """
        out_path=self.get_results_root_directory()
        # If idb equals -1 get highest id directory found in out_dir
        if (idb == -1):
            dir_list=[]
            newest_result_dir=None

            for fd in os.listdir(out_path):
                result_dir=os.path.join(out_path,fd)
                if os.path.isdir(result_dir):
                    dir_list.append(result_dir)

            newest_result_dir = max(dir_list, key=os.path.getmtime)
            idb_s=newest_result_dir
        else:
            idb_s=str(idb).zfill(6)

        # Padding ID with zeros to reach a 6 length id to get Jube run directory path.
        run_path=os.path.join(out_path,idb_s)
        configuration_file_path=os.path.join(run_path,'configuration.xml')

        # Standard log files to look for
        log_files=['stdout','stderr','run.log']

        try :
            self.jube_xml_files.load_config_xml(configuration_file_path)
        except :
            raise IOError('Cannot find: '+configuration_file_path+' file.')

        # Get job errlog and outlog filenames from configuration.xml file
        log_files += self.jube_xml_files.get_job_logfiles()

        # Get filenames that are used for analyse from configuration.xml file
        log_files += self.jube_xml_files.get_analyse_files()

        # Concatenante evry files that are considered as log file and order them
        # with the last modified file at the last position.
        result=''
        log_files_found=[]
        for root, dirs, files in os.walk(run_path):
            for f in files :
                if f in log_files :
                    log_files_found.append(os.path.join(root,f))


        for fpath in sorted(log_files_found,key=os.path.getmtime):
            result+='========= '+fpath+' =========\n'
            with open(fpath, 'r') as log_file:
                result+=log_file.read()+'\n'

        return '\n-------------------------------------------------------\n'\
            +'==== Log for {0} benchmark. (run ID = {1})  ==== \n'.format(self.benchmark_name,os.path.basename(idb_s))\
            +'-------------------------------------------------------\n\n'\
            +result

  def get_status_info(self,benchmark_id):

        if(not os.path.isdir(self.benchmark_path)):
            raise IOError

        os.chdir(self.benchmark_path)
        output_dir = self.jube_xml_files.get_bench_outputdir()

        bench_steps = self.jube_xml_files.get_bench_steps()

        global_status = {}
        for step in bench_steps:
            # Updating state with continue command
            Popen('jube continue --hide-animation ./'+output_dir+' --id '+benchmark_id,cwd=os.getcwd(),stdout=open(os.devnull, "w"),shell=True)
            time.sleep(0.5)
            input_str='jube info ./'+output_dir+' --id '+benchmark_id+' --step '+step
            status_from_jube=Popen(input_str,cwd=os.getcwd(),shell=True,stdout=PIPE)
            global_status[step]=[]
            for line in status_from_jube.stdout:
                if re.search("^\s+\d+\s+\|\s+\w+\s+\|.*",line):
                    raw_values = [c.strip() for c in line.split("|")]
                    task = {}
                    task['id'] = raw_values[0]
                    task['started'] = raw_values[1]
                    task['done'] = raw_values[2]
                    task['workdir'] = raw_values[3]
                    global_status[step].append(task)

        return global_status

  def extract_result_from_benchmark(self,benchmark_id):
        """ Get result from a jube benchmark with its id and build a python result array
        :param benchmark_id: id of the benchmark
        :type benchmark_id:int
        :returns: a result array
        :rtype:str
        """

        # Checking if all tasks have finished.
        status = self.get_status_info(benchmark_id)
        for step in status:
            for task in status[step]:
                if task['done'] == "false":
                    print "Unfinished tasks in step: "+step+", please try later on"


        old_path=os.getcwd()
        os.chdir(self.benchmark_path)
        output_dir = self.jube_xml_files.get_bench_outputdir()
        input_str='jube result ./'+output_dir+' --id '+benchmark_id
        result_from_jube = Popen(input_str,cwd=os.getcwd(),shell=True, stdout=PIPE)

        result_array=[]

        # Get data from result array
        empty=True
        for line in result_from_jube.stdout:
            empty=False

            splitted_line=[]
            if len(line.strip()) > 0:
                splitted_line=line.replace("\n", "").split(',')

            # Merge '[' and ']' sections to authorize [,]
            idx=0
            while idx < len(splitted_line)-1:
                if ('[' in splitted_line[idx]) and \
                   (not ']' in splitted_line[idx]):
                    splitted_line[idx:(idx+2)]=[','.join(splitted_line[idx:(idx+2)])]
                else:
                    idx+=1

            if len(line.strip()) > 0:
                result_array.append(splitted_line)

        if (empty):
            raise IOError

        # Restore working directory
        os.chdir(old_path)
        return result_array


  def extract_result_from_last_benchmark(self):
        """ Get result from the last execution of a benchmark
        :param benchmark_id: id of the benchmark
        :type benchmark_id:int
        :returns: result array
        :rtype:str
        """
        try:
            return self.extract_result_from_benchmark('last')
        except IOError:
            raise


  def run_benchmark(self,platform):
        """ Run benchmark on a given platform and return the benchmark run directory path
        and a benchmark ID.
        :param platform: name of the platform used to configure the benchmark options relative
        to the platform architecture and software.
        :type platform: str
        :returns: return absolute path of the benchmark result directory
        :rtype: str
        """
        old_path=os.getcwd()
        os.chdir(self.benchmark_path)

        # modify bench xml
        self.jube_xml_files.add_bench_input()
        self.jube_xml_files.remove_multisource()
        self.jube_xml_files.write_bench_xml()

        old_run_dir=self.analyse_last_benchmark()

        input_str='jube run --hide-animation '+self.benchmark_name+'.xml --tag '+platform+' > /dev/null &'
        p=Popen(input_str,cwd=os.getcwd(),shell=True)

        # Get the run directory without waiting for jube run command to finish
        run_dir = self.analyse_last_benchmark()
        timeout_counter=0
        time.sleep(2) # waiting for the directory to be created
        while (run_dir == old_run_dir) :
            time.sleep(1) # wait to avoid spamming
            timeout_counter+=1
            run_dir=self.analyse_last_benchmark()
            if (timeout_counter>10):
              raise RuntimeError('Jube parsing might have gone wrong, please check '+
                                 self.benchmark_path+'/jube-parse.log file')

        # Get benchmark run directory
        ID=run_dir[-7:-1]

        absolute_run_dir=os.path.abspath(run_dir)
        # Restore working directory
        os.chdir(old_path)
        return (absolute_run_dir,ID)


  def status(self,benchmark_id):

        status = self.get_status_info(benchmark_id)
        for step in status:
            print "\nStatus for step: "+step
            print "--------------------------------"
            print "id\tstarted\tdone\tworkdir"
            print "--------------------------------"
            for task in status[step]:
                print task['id'] + "\t"+ task['started']+"\t"+task['done']+"\t"+task['workdir']


  def set_custom_nodes(self,nnodes_list,nodes_id_list):
    """
    Modify benchmark xml file to set custom nodes configurations.
    :param nnodes_list: list of number of nodes ex: [1,6]
    :type nnodes_list: list of int
    :param nodes_id_list: list of corresonding nodes ids  ex: ['cn050','cn[103-107,145]']
    :type nodes_id_list:  list of strings
    """
    self.jube_xml_files.substitute_element_text('parameter','nodes','.*','$custom_nodes')
    self.jube_xml_files.substitute_element_text('do',None,re.escape('$submit '),'$custom_submit ')

    # Add an xml section describing custom nodes configurations
    self.jube_xml_files.add_custom_nodes_stub(nnodes_list,nodes_id_list)

  def list_parameters(self,config_dir_path=None):
    """
    List benchmark customisable parameters
    :param config_dir_path: Optional parameter reprenting the path of the config files (usefull when a benchmark has never been run).
    :type config_dir_path: str
    :returns: Return a list of tuples [(param1,value),(param2,value),....]
    :rtype: list of tuples
    """
    parameters_list={'benchmark' : self.jube_xml_files.get_params_bench(),
                     'platform' : self.jube_xml_files.get_params_platform()}
    return  parameters_list

  def set_parameter(self,dict_options):
    """
    Set custom parameter from its name and a new value.
    :type parameter_name:
    :param value: value to substitute to old value
    :type value: str
    :returns: Return a list of tuples [(filename,param1,old_value,new_value),(filename,param2,old_value,new_value),....]
    :rtype: List of 3-tuples ex:[(parameter_name,old_value,value),....]
        """
    return self.jube_xml_files.set_params_bench(dict_options)
