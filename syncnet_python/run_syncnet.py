#!/usr/bin/python
#-*- coding: utf-8 -*-

import time, pdb, argparse, subprocess, pickle, os, gzip, glob

from SyncNetInstance import *

# ==================== PARSE ARGUMENT ====================

parser = argparse.ArgumentParser(description = "SyncNet");
parser.add_argument('--initial_model', type=str, default="data/syncnet_v2.model", help='');
parser.add_argument('--batch_size', type=int, default='20', help='');
parser.add_argument('--vshift', type=int, default='15', help='');
parser.add_argument('--data_dir', type=str, default='data/work', help='');
parser.add_argument('--videofile', type=str, default='/raw/5HEprZ8PuuA.mp4', help='');
parser.add_argument('--reference', type=str, default='5HEprZ8PuuA', help='');
opt = parser.parse_args();

setattr(opt,'avi_dir',os.path.join(opt.data_dir,'pyavi'))
setattr(opt,'tmp_dir',os.path.join(opt.data_dir,'pytmp'))
setattr(opt,'work_dir',os.path.join(opt.data_dir,'pywork'))
setattr(opt,'crop_dir',os.path.join(opt.data_dir,'pycrop'))


# ==================== LOAD MODEL AND FILE LIST ====================

s = SyncNetInstance();

s.loadParameters(opt.initial_model);
print("Model %s loaded."%opt.initial_model);

flist = glob.glob(os.path.join(opt.crop_dir,opt.reference,'0*.avi'))
flist.sort()

# ==================== GET OFFSETS ====================

dists = []
print('Start evaluating')
print('Number:',len(flist))
start_time = time.time()
for idx, fname in enumerate(flist):
    """
    offset,minval,conf = s.evaluate(opt,videofile=fname)
    # change the file name with conf
    # rename fname to f'fname_conf{conf}.avi'
    dir_name = os.path.dirname(fname)
    base_name = os.path.basename(fname)
    base_name_without_ext = os.path.splitext(base_name)[0]
    new_name = f"{base_name_without_ext}_conf{conf}.avi"
    new_fname = os.path.join(dir_name, new_name)
    os.rename(fname, new_fname)
    """
    offset, conf, dist = s.evaluate(opt,videofile=fname)
    print('fname:{}, conf:{}, dist:{}'.format(fname, conf, dist))
    dists.append(dist)
    
elapsed_time =  time.time() - start_time

print('time cost:',elapsed_time)
# ==================== PRINT RESULTS TO FILE ====================

with open(os.path.join(opt.work_dir,opt.reference,'activesd.pckl'), 'wb') as fil:
    pickle.dump(dists, fil)
