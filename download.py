import os, subprocess, argparse
# export http_proxy="http://127.0.0.1:12333"
# export https_proxy="http://127.0.0.1:12333"
def convert_name_to_txt():
    import os
    folder = '/media/cwy/8T/GoogleDownload/vox1_test_txt/txt'
    for id in os.listdir(folder):
        for ytb_id in os.listdir(os.path.join(folder,id)):
            os.remove(os.path.join(folder,id,ytb_id,'video.txt'))
            # with open(os.path.join(folder,id,ytb_id,'video.txt'),'w') as f:
                # f.write(ytb_id+'\n')

def download(video_path, ytb_id, proxy=None):
    """
    ytb_id: youtube_id
    save_folder: save video folder
    proxy: proxy url, defalut None
    """
    if proxy is not None:
        proxy_cmd = "--proxy {}".format(proxy)
    else:
        proxy_cmd = ""
    if not os.path.exists(video_path):
        down_video = " ".join([
            "yt-dlp",
            proxy_cmd,
            '-f', "'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio'",
            '--skip-unavailable-fragments',
            '--merge-output-format', 'mp4',
            "https://www.youtube.com/watch?v=" + ytb_id, "--output",
            video_path, "--external-downloader", "aria2c",
            "--external-downloader-args", '"-x 16 -k 1M"'
            "--quiet"
        ])
        print(down_video)
        status = os.system(down_video)
        if status != 0:
            print(f"video not found: {ytb_id}")

def format_process(opt):
    
    if not os.path.exists(os.path.join(opt.fps25_folder,opt.video_id)):
        os.makedirs(os.path.join(opt.fps25_folder,opt.video_id))

    if not os.path.exists(os.path.join(opt.fps25_folder,opt.video_id, 'video.avi')):   
        command = "ffmpeg -y -i %s -qscale:v 2 -async 1 -r 25 %s" % (os.path.join(opt.raw_folder,opt.video_id+'.mp4'), os.path.join(opt.fps25_folder,opt.video_id,'video.avi')) # 输出的这个avi是自带声音的
        output = subprocess.call(command, shell=True, stdout=None)

    if not os.path.exists(os.path.join(opt.fps25_folder,opt.video_id, 'audio.wav')):   
        command = ("ffmpeg -y -i %s -ac 1 -vn -acodec pcm_s16le -ar 16000 %s" % (os.path.join(opt.fps25_folder,opt.video_id,'video.avi'),os.path.join(opt.fps25_folder,opt.video_id,'audio.wav')))
        output = subprocess.call(command, shell=True, stdout=None)

if __name__ == '__main__':

    proxy = "http://10.0.1.4:7891"  
    # proxy = None
    parser = argparse.ArgumentParser(description = "youtude video download and process")
    # https://www.youtube.com/watch?v=VQDF8vUQj28&list=RDCMUCp2zBKrqP0ZQF6RN4RJtF2Q&index=31
    parser.add_argument('--video_id',       type=str, default='TI70xn6KL9k', help='youtube id to download') # WCa0xWZXT3k ojA8VJolCVI rYO82-Ndq9U MiITedbdu3w
    parser.add_argument('--video_txt',       type=str, help='youtube id to download')
    parser.add_argument('--raw_folder',      type=str, default='/media/cwy/250G/ppt/princess',   help='raw folder to save downloaded videos') # '/media/cwy/8T/voxceleb1/raw'
    # parser.add_argument('--fps25_folder',      type=str, default='25fps',   help='folder to save process videos')
   
    count = 0
    opt = parser.parse_args()
    if not os.path.exists(opt.raw_folder):
        os.makedirs(opt.raw_folder)

    if opt.video_txt is not None:
        with open(opt.video_txt,'r') as f: # 如果提供了下载列表
            lines = f.readlines()
            for line in lines:
                line = line.strip().split('\t')
                video_id = line[0]
                video_path = os.path.join(opt.raw_folder, video_id+".mp4")
                if not os.path.exists(video_path):
                    try:
                        download(video_path, video_id, proxy)
                        count+=1
                        # if count % 10 == 0:
                        #     print(count)
                    except Exception as e:
                        print("error",video_id)
                        print(e)
    else: # 否则的话，直接下载单个视频
        video_id = opt.video_id
        video_path = os.path.join(opt.raw_folder, video_id+".mp4")
        if not os.path.exists(video_path):
            try:
                download(video_path, video_id, proxy)
            except Exception as e:
                print("error",video_id)
                print(e)
