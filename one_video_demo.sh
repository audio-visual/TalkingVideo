
work_folder=/home/gao/TalkingVideo/workfolder
for ytb_id in 0hbC7tap0aw _8nyqeQK-vY
do 
    echo "Processing ${ytb_id}"
    # python download.py --video_id ${ytb_id} --raw_folder ${work_folder}/raw
    cd syncnet_python
    python run_pipeline.py --videofile ${work_folder}/raw/${ytb_id}.mp4 --reference ${ytb_id} --data_dir ${work_folder}/syncnet
    python run_syncnet.py --videofile ${work_folder}/raw/${ytb_id}.mp4 --reference ${ytb_id} --data_dir ${work_folder}/syncnet 
    python syncnet_postprocess.py --video_id ${ytb_id} --work_folder ${work_folder}/syncnet
    cd ..
done
