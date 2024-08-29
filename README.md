

This project is designed to automatically download and crop speaking segments from full videos. It can be viewed as a reproduction of Voxceleb2/MAV-Celeb/CelebV-HQ, etc.

# Quick Start
Ensure you have installed `ffmpeg`, `yt-dlp`, and other necessary Python packages.
```
# Change the proxy, video_id, or other parameters
bash ./one_video_demo.sh
```

# Full Pipeline
## Step 1
Automatically download videos from YouTube.
```
# Change the proxy, video_id, or other parameters
python download.py 
```
## Step 2
Detect and track faces automatically.
```
# cd syncnet_python
python run_pipeline.py
``` 
In detail, this step includes:

1) Preprocessing: Convert video to 25 FPS; extract images from video; convert audio to 16 KHz.
2) Face detection.
3) Scene detection.
4) Face tracking for every scene (through confirming the intersection of face detection bounding boxes between neighboring images).
5) Video trimming and cropping.

## Step 3
Calculate the lip-sync confidence for every video clip obtained in step 2.
```
# cd syncnet_python
python run_syncnet.py
``` 

## Step 4
Postprocess the video clip into smaller segments with more lip-sync precision.
```
# cd syncnet_python
python run_syncnet.py
``` 

# Optimization
The original pipeline is time-consuming, so we made some changes for a faster process (according to our rudimentary tests, the following changes speed up the full process by more than 2.5x).

## Disable Warnings
In `detectors/s3fd/box_util.py`, add `resize_(0)` at each loop to suppress user warnings.
```python
# Load bounding boxes of next highest values.
xx1.resize_(0)
torch.index_select(x1, 0, idx, out=xx1)
yy1.resize_(0)
torch.index_select(y1, 0, idx, out=yy1)
xx2.resize_(0)
torch.index_select(x2, 0, idx, out=xx2)
yy2.resize_(0)
torch.index_select(y2, 0, idx, out=yy2)
```
## Batch Face Detection
In the original face detection method, faces were fed to the network one by one, which can be time-consuming. We've implemented an `ImageDataset(Dataset)` class and employed `DataLoader` to batch our data. We use a skip strategy `inference_video_batch_skip()` (only face detection is performed for each skip step).

## Disable FFmpeg Output
```python
# output = subprocess.call(command, shell=True, stdout=None)
output = subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
```

## Multi-processing
We've transformed the original, sequential video cropping process into a multi-processing approach.
```python
with Pool() as p:
    vidtracks = p.map(process_track, [(opt, track, ii) for ii, track in enumerate(alltracks)])
```
# Differences from Voxceleb2
Voxceleb2 provides a text metafile that we can use to crop and trim the original videos. While our initial intention was to reproduce the Voxceleb2 data collection pipeline described in their paper, we found some minor differences in the final results:

1) Our default pipeline has a stricter minimum face area requirement than Voxceleb2. To obtain the same video segments as in the Vox2 text metafile, you need to change the `min_face_size` (according to our tests, it may be set to 50) in `run_pipeline.py`; in our project, we've set the default minimum face size as 100.
2) Vox2 doesn't force face alignment at the center, as demonstrated by the bounding box crop logic `crop_box()` in `vox2_process_by_txt.py`. However, we enforce it in our project. Our logic initially pads the image fully and then crops it, ensuring that the face always appears near the center (as seen in `crop_video()` in `run_pipeline.py`).

# TODO 
- [ ] Optimize the pipeline further to avoid repeating steps.
- [ ] Implement face verification.
- [ ] Implement speaker change detection/separation.

# Acknowledgments
Thanks to the following projects:

https://github.com/StelaBou/voxceleb_preprocessing/tree/master

https://github.com/joonson/syncnet_python
