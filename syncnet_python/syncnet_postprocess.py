import torch
import numpy as np
import time, pdb, argparse, subprocess, pickle, os, glob
import cv2

from scipy import signal
skip = 5
frame_rate = 25
def compute_count_list(track_list, min_conf=2.1):
    count = 0
    count_list = []
    segments = []
    start_index = None
    for i, value in enumerate(track_list):
        if value > min_conf:
            count += 1
            if start_index is None:
                start_index = i
        else:
            if start_index is not None:
                segments.append((start_index, i - 1))
                start_index = None
            count = 0
        count_list.append(count)
    if start_index is not None:
        segments.append((start_index, len(track_list) - 1))
    return count_list, segments

def modify_segments(segments, threshold=15, min_length=75):
    modified_segments = []
    if len(segments)<1:
        return modified_segments
    current_start, current_end = segments[0]

    for start, end in segments[1:]:
        if start - current_end <= threshold:
            current_end = end  # Extend the current segment
        else:
            # Add the current segment to the list and start a new one
            if current_end - current_start >= min_length:
                modified_segments.append((current_start, current_end))
            current_start, current_end = start, end

    # Add the last segment
    if current_end - current_start >= min_length:
        modified_segments.append((current_start, current_end))

    return modified_segments 

def get_track_data(tracks,dists, flist):
    track_data = [[] for _ in range(len(tracks))]
    # print('len of tracks:',len(tracks))
    # print('len of dists:',len(dists))
    for tidx, track in enumerate(tracks):
        faces = [[] for i in range(len(flist))]
        
       
        mean_dists 	=  np.mean(np.stack(dists[tidx],1),1)
        # print(mean_dists[:3])
        
        minidx 		= np.argmin(mean_dists,0)

        minval 		= mean_dists[minidx] 
        # print(minval)
      
        fdist   	= np.stack([dist[minidx] for dist in dists[tidx]])
        
        fdist   	= np.pad(fdist, (3,3), 'constant', constant_values=10) # 399 + 6 = 405

        fconf   = np.median(mean_dists) - fdist
       

        fconfm  = signal.medfilt(fconf,kernel_size=9)
        
        for fidx, frame in enumerate(track['track']['frame'].tolist()):
            faces[frame].append({'track': tidx, 'conf':fconfm[fidx], 's':track['proc_track']['s'][fidx], 'x':track['proc_track']['x'][fidx], 'y':track['proc_track']['y'][fidx]})
       

        track_data[tidx] = faces
    return track_data

def generate_meta(tracks,conf_ys):
    for track_idnex in range(len(tracks)):
        print(track_idnex)
        # if track_index!=1:
            # continue
        _, segments = compute_count_list(conf_ys[track_idnex])
        segments2 = modify_segments(segments)
       
        track_cur = track_data[track_idnex]

        for seg_index,seg in enumerate(segments2):
            
            image = cv2.imread(flist[seg[0]+skip])
            origin_h = image.shape[0]
            
            origin_w = image.shape[1]
            with open(f'2DLq_Kkc1r8_{track_idnex}_{seg_index}.txt','a') as f:
                f.write("Identity :\n")
                f.write("Reference: \n")
                f.write("Offset: \n")
                f.write("FV Conf:\n")
                f.write("ASD Conf: \n\n")
                f.write("FRAME \tX\tY\tW\tH\n")
                for index in range(seg[0]+skip,seg[1]-skip+1):
                
                    bs = track_cur[index][0]['s']
                    cs = 0.4
 
                    my  = track_cur[index][0]['y']  # BBox center Y
                    mx  = track_cur[index][0]['x']  # BBox center X
                    # y1:y2, x1:x2
                    y1 = int(my-bs)
                    y2 = int(my+bs*(1+2*cs))
                    x1 = int(mx-bs*(1+cs))
                    x2 = int(mx+bs*(1+cs))
                    crop_size_w = x2-x1 
                    crop_size_h = y2-y1
                    
                    ratio_x1 = x1/origin_w
                    ratio_y1 = y1/origin_h
                   
                    ratio_crop_w = crop_size_w / origin_w
                    ratio_crop_h = crop_size_h / origin_h
                    str_index = "{:06d}".format(index)
                    # convert float to 3 decimal places
                    ratio_x1 = "{:.3f}".format(ratio_x1)
                    ratio_y1 = "{:.3f}".format(ratio_y1)
                    ratio_crop_w = "{:.3f}".format(ratio_crop_w)
                    ratio_crop_h = "{:.3f}".format(ratio_crop_h)
                    f.write(f'{str_index}\t{ratio_x1}\t{ratio_y1}\t{ratio_crop_w}\t{ratio_crop_h}\n')

def generate_video(opt, tracks, conf_ys):
    process_folder = os.path.join(opt.work_folder, 'process', opt.video_id)
    if not os.path.exists(process_folder):
        os.makedirs(process_folder)
    for track_idnex in range(len(tracks)):
        process_sub_folder = os.path.join(process_folder, f'track_{track_idnex}')
        _, segments = compute_count_list(conf_ys[track_idnex])
        segments2 = modify_segments(segments)
        print('segments2')
        print(segments2)
        track_cur = track_data[track_idnex]
        if len(segments2)<1:
            print('none,continue')
            continue
        print(process_sub_folder)
        if not os.path.exists(process_sub_folder):
            os.makedirs(process_sub_folder)

        for seg_index,seg in enumerate(segments2):
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_tmp = os.path.join(process_sub_folder, f't{track_idnex}_s{seg_index}.avi')
            vOut = cv2.VideoWriter(video_tmp, fourcc, 25, (224,224))
            for index in range(seg[0]+skip,seg[1]-skip): #range(seg[0]+skip,seg[1]-skip):
                cs = 0.4
                # print(index)
                try:
                    bs = track_cur[index][0]['s']  
                except:
                    print(index)
                    print(len(track_cur))
                    print(track_cur[index])
                    
                bsi = int(bs*(1+2*cs)) 
                image = cv2.imread(flist[index])
                frame = np.pad(image,((bsi,bsi),(bsi,bsi),(0,0)), 'constant', constant_values=(110,110))
                # print(track_zero[index][0])
                my  = track_cur[index][0]['y']+bsi  # BBox center Y
                mx  = track_cur[index][0]['x']+bsi  # BBox center X
                # y1:y2, x1:x2
                # the original method cuts the lower head，which would result in many face attribute analyse mehtods fail
                face = frame[int(my-bs*(1+cs)):int(my+bs*(1+cs)),int(mx-bs*(1+cs)):int(mx+bs*(1+cs))]
                vOut.write(cv2.resize(face,(224,224)))
            vOut.release()
            audiotmp    = os.path.join(process_sub_folder, f't{track_index}_s{seg_index}.wav')
            audiostart  = (seg[0]+skip)/frame_rate
            audioend    = (seg[1]-skip)/frame_rate 
            command = ("ffmpeg -y -i %s -ss %.3f -to %.3f %s" % (os.path.join(opt.work_folder, 'pyavi', opt.video_id,'audio.wav'),audiostart,audioend,audiotmp)) 
            # output = subprocess.call(command, shell=True, stdout=None) 
            output = subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            command = ("ffmpeg -y -i %s -i %s -c:v copy -c:a aac -strict experimental %s" %(video_tmp, audiotmp, video_tmp.replace('.avi','.mp4')))
            # output = subprocess.call(command, shell=True, stdout=None)
            output = subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            os.remove(video_tmp)
            os.remove(audiotmp) 

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "youtude video download and process")
    parser.add_argument('--video_id',       type=str, default='0G-oLWBu3uA', help='youtube id to download')
    parser.add_argument('--work_folder',    type=str, default='/18T/VoiceFace/dataset/voxceleb2/syncnet', help='youtube id to download')
    # ytb_id = '2DLq_Kkc1r8'
    
    opt = parser.parse_args()
    video_id = opt.video_id
    work_folder = opt.work_folder
    
    ref_folder = f'{work_folder}/pywork/{video_id}'

    with open(os.path.join(ref_folder,'tracks.pckl'), 'rb') as fil:
        tracks = pickle.load(fil, encoding='latin1') # list of dict

    with open(os.path.join(ref_folder,'activesd.pckl'), 'rb') as fil:
        dists = pickle.load(fil, encoding='latin1')

    flist = glob.glob(os.path.join(f'{work_folder}/pyframes/{video_id}','*.jpg'))
    flist.sort() 

    track_data = get_track_data(tracks,dists, flist)



    conf_ys = [[] for _ in range(len(tracks))]
    
    for track_index in range(len(tracks)):
        faces = track_data[track_index]
        for face in faces:
            if len(face)==0:

                conf_ys[track_index].append(-1)
            else:
                assert(len(face)==1)
                conf_ys[track_index].append(face[0]['conf'])

    
    
    # generate_meta(tracks,conf_ys)
    generate_video(opt, tracks, conf_ys)





            

            
	


