# -*- encoding: utf-8 -*-

"""
prepares already clustered part of session for final template matching
"""

from __future__ import print_function, division, absolute_import
import os
import numpy as np
#   pylint: disable=E1101
import tables
#from combinato import SortingManager
import glob
import shutil

def write_joblist(new_joblist):
    outfname = "joblist_transfer.txt"
    
    with open(outfname, 'a') as outf:
         for job in new_joblist:
             outf.write("{}\n".format(job))
    outf.close()   
     
def unique_rows(a):
    a = np.ascontiguousarray(a)
    unique_a = np.unique(a.view([('', a.dtype)]*a.shape[1]))
    return unique_a.view(a.dtype).reshape((unique_a.shape[0], a.shape[1]))    
    
def main(preIctal_session, total_session, preIctal_label, joblist):#, channels):
    #print(preIctal_label)
    #print(preIctal_session)
    
    #ncsfiles=glob.glob(total_session+'CSC*.ncs')
    #ncsfiles=np.unique(ncsfiles)
    #for ncsfile in ncsfiles:
    new_joblist=[]
    
    for job in joblist:
        channel=job[0][:job[0].rfind('/')]
        #channel=ncsfile[ncsfile.rfind('/')+1:ncsfile.rfind('.')]
    #for channel in channels:
        print(channel)
        #print(os.path.join(preIctal_session, channel, preIctal_label+'_*','sorting.h5'))
        sorting_PreIctal_files=glob.glob(os.path.join(preIctal_session, channel, preIctal_label+'_*','sorting.h5'))
        
        # if there are no sorted spikes in the PreIctal data continue
        if not sorting_PreIctal_files[0]:
            print(channel+' has no PreIctal clustered spikes!')
            print(channel+' is not appended to joblist!')
            continue
        
        new_joblist.append(channel)
        sorting_TemplateTimes_file=glob.glob(os.path.join(total_session, job[2],'sorting.h5'))
        #sorting_TemplateTimes_file=glob.glob(os.path.join(total_session, channel,templateTimes_label+'_*','sorting.h5'))
        preIctal_file=os.path.join(preIctal_session, channel,'data_' + channel + '.h5')
        totalSession_file=os.path.join(total_session, job[0])
        #totalSession_file=os.path.join(total_session, channel,'data_' + channel + '.h5')
        #for sorting_PreIctal_file in sorting_PreIctal_files:
        transform_sorting(sorting_PreIctal_files, sorting_TemplateTimes_file[0], preIctal_file, totalSession_file)
        
    
    # write new joblist for template matching    
    write_joblist(new_joblist)   
     
    
    
def transform_sorting(sorting_PreIctal_files, sorting_TemplateTimes_file, preIctal_file, totalSession_file): # input is clustered sorting.h5 of PreIctal and unclustered sorting.h5 of new Data
    shutil.copyfile(sorting_TemplateTimes_file, sorting_TemplateTimes_file[:sorting_TemplateTimes_file.rfind('.')]+'_2.h5')
    
    sorting_TemplateTimes=tables.open_file(sorting_TemplateTimes_file,'r+')
    

    data_total=tables.open_file(totalSession_file,'r')
    data_preIctal=tables.open_file(preIctal_file,'r')
    times_preIctal=data_preIctal.root.pos.times[:]
    times_total=data_total.root.pos.times[:]
    

    #print(times_total)
# find the timestamps which can be found in the preIctal and the totalSession Data
    timestamps_both=np.in1d(times_preIctal,times_total) # is a vector containing True or False depending on finding a timestamp of a extracted preIctal spike in the extracted spiketimes of the total data
    inside_both=np.where(timestamps_both)[0] # is a vector containing the index (between 0 and len(times_preIctal)-1) of the spikes present in both datasets
    
    classes_total=np.zeros(len(sorting_TemplateTimes.root.index[:]),np.uint16)    
    matches_total=np.zeros(len(sorting_TemplateTimes.root.index[:]),np.uint16)   
    
    
    for sorting_PreIctal_file in sorting_PreIctal_files:
        sorting_PreIctal=tables.open_file(sorting_PreIctal_file,'r')    
        index_already_assigned=np.in1d(sorting_PreIctal.root.index[:],inside_both) # is a vector of Boolean values depending if the index of the spikes which are already assigned to a class are present in both datasets
        classes_both=sorting_PreIctal.root.classes[np.where(index_already_assigned)[0]] # classes of the spikes which are present in both datasets
        index_both=sorting_PreIctal.root.index[np.where(index_already_assigned)[0]] # index of the spikes which are present in both datasets and which are already assigned to a class
        matches_both=sorting_PreIctal.root.matches[np.where(index_already_assigned)[0]]
        artifacts_both=sorting_PreIctal.root.artifact_scores[:]
# convert the index, class and match from the preIctal data (ranging usually from 0 to ...) to the total data (usually no starting at 0 but somewhere between 1000 and 3000)
        timestamps_both_total=np.in1d(times_total,times_preIctal[index_both])
        inside_both_total=np.where(timestamps_both_total)[0]
        index_already_assigned_total=np.in1d(sorting_TemplateTimes.root.index[:],inside_both_total)   
        classes_total[np.where(index_already_assigned_total)[0]]=classes_both
        matches_total[np.where(index_already_assigned_total)[0]]=matches_both
        artifacts_total=np.zeros((len(np.unique(classes_total)),2),np.uint8)
        artifacts_total[:,0]=np.unique(classes_total)
        sorting_PreIctal.close()

# save transformed data to sorting.h5
    try:
       sorting_TemplateTimes.create_array('/','classes',classes_total)
       sorting_TemplateTimes.create_array('/','matches',matches_total)
       sorting_TemplateTimes.create_array('/','artifact_scores',artifacts_total)
    except tables.exceptions.NodeError:
       print(sorting_TemplateTimes_file+' already prepared')     

    sorting_TemplateTimes.close()

    data_total.close()
    data_preIctal.close()
    
def parse_args():
    """
    usual parser
    """
    from argparse import ArgumentParser, FileType, ArgumentError

    parser = ArgumentParser('prepare template matching',
                            description='Prepares Matching of PreIctal and unsorted sessions',)
                            
    parser.add_argument('--preIctal_session', nargs=1, required=True)
    parser.add_argument('--jobs', type=FileType('r'))
    parser.add_argument('--total_session', nargs=1, required=True)
    parser.add_argument('--preIctal_label', nargs=1, required=True)
    
    

    args = parser.parse_args()
    
    preIctal_session=args.preIctal_session
    total_session=args.total_session
    preIctal_label=args.preIctal_label
    jobdata = args.jobs.read().splitlines()
    joblist = tuple((tuple(line.split()) for line in jobdata))
    #print(joblist)
    main(preIctal_session[0], total_session[0], preIctal_label[0], joblist)#, channels)
    
if __name__ == "__main__":
    parse_args()    
    
    
    
    
    
    
    

