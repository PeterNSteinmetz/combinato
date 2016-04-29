# -*- encoding: utf-8 -*-

"""
transfers the types and groups of the PreIctal data to the total data
"""

from __future__ import print_function, division, absolute_import
import os
import numpy as np
import tables
import glob
import shutil

    
def main(preIctal_session, total_session, preIctal_label, totalMatch_label, joblist):

    for job in joblist:
        channel=job#[0][:job[0].rfind('/')]
        print(channel)
        sort_cat_PreIctal_file=os.path.join(preIctal_session, channel, preIctal_label, 'sort_cat.h5') 
               
        # if there are no sorted spikes in the PreIctal data continue
        if not sort_cat_PreIctal_file:
            print(channel+' has no PreIctal matched data')
            continue

        sort_cat_TotalMatch_file=os.path.join(total_session, channel, totalMatch_label, 'sort_cat.h5')
        transform_types(sort_cat_PreIctal_file, sort_cat_TotalMatch_file)
       
     
    
    
def transform_types(sort_cat_PreIctal_file, sort_cat_TotalMatch_file): 

    # copy original sort_cat.h5 from TotalMatch data
    shutil.copyfile(sort_cat_TotalMatch_file, sort_cat_TotalMatch_file[:sort_cat_TotalMatch_file.rfind('.')]+'_2.h5')
    
    sort_cat_TotalMatch=tables.open_file(sort_cat_TotalMatch_file,'r+')
    sort_cat_PreIctal=tables.open_file(sort_cat_PreIctal_file,'r')
    
    # because original classes (before the template matching) are the same (due to prepare_template_matching), transforming groups and types is easy:
    sort_cat_TotalMatch.root.groups[:]=sort_cat_PreIctal.root.groups[:]
    
    # because number of types doesn't have to be the same you first have to remove the node 'types' and create a new one
    try:
        sort_cat_TotalMatch.remove_node('/', 'types')
        print('Updating types')
        
    except tables.NoSuchNodeError:
        print('There seems to be a problem in {}').format(sort_cat_TotalMatch_file)   
        return
        
    sort_cat_TotalMatch.create_array('/','types',sort_cat_PreIctal.root.types[:])

    # also leave the artifacts as they are in the PreIctal data
    
    sort_cat_TotalMatch.root.artifacts[:]=sort_cat_TotalMatch.root.artifacts_prematch[:]

    sort_cat_TotalMatch.flush()
    sort_cat_TotalMatch.close()
    sort_cat_PreIctal.close()

def parse_args():
    """
    usual parser
    """
    from argparse import ArgumentParser, FileType, ArgumentError

    parser = ArgumentParser('transfer_class_assignment',
                            description='Transfers groups and types of PreIctal data',)
                            
    parser.add_argument('--preIctal_session', nargs=1, required=True)
    parser.add_argument('--jobs', type=FileType('r'),required=True)
    parser.add_argument('--total_session', nargs=1, required=True)
    parser.add_argument('--preIctal_label', nargs=1, required=True)
    parser.add_argument('--totalMatch_label', nargs=1,required=True)
    
    

    args = parser.parse_args()
    
    preIctal_session=args.preIctal_session
    total_session=args.total_session
    preIctal_label=args.preIctal_label
    totalMatch_label=args.totalMatch_label
    #channels=args.channels
    
    #if args.templateTimes_label:
    #    templateTimes_label=args.templateTimes_label
    #else:
    #    templateTimes_label='sort_pos_TemplateTimes'
    
    joblist = args.jobs.read().splitlines()
    #joblist = tuple((tuple(line.split()) for line in jobdata))
    #print(joblist)
    main(preIctal_session[0], total_session[0], preIctal_label[0],totalMatch_label[0], joblist)
    
if __name__ == "__main__":
    parse_args()    
    
    
    
    
    
    
    

