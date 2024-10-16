from transformers import AutoProcessor, BarkModel, VitsModel, AutoTokenizer
import torch
import scipy
import os
import csv 
import random
import time
from API import api_key 
from openai import OpenAI

# go get IO class from parent folder
# caution: path[0] is reserved for script path (or '' in REPL)
import sys
#######MICHAEL##############
# sys.path.insert(1, '/Users/michaelmandiberg/Documents/GitHub/facemap/')
############################
#######SATYAM##############
sys.path.insert(1, 'C:/Users/jhash/Documents/GitHub/facemap2/')
###########################
from mp_db_io import DataIO

METHOD="meta" ##openai or bark or meta


start = time.time()
######Michael's folders##########
io = DataIO()
INPUT = os.path.join(io.ROOT, "audioproduction", METHOD)
OUTPUT = os.path.join(io.ROOT, "audioproduction", METHOD)
#################################

######Satyam's folders###########
# INPUT = "C:/Users/jhash/Documents/GitHub/facemap2/sound"
# OUTPUT = "C:/Users/jhash/Documents/GitHub/facemap2/sound/sound_files/OpenAI"
#################################

sourcefile = "metas.csv"
output_csv = "output_file.csv"

STOP_AFTER = 2000
counter = 1
start_at = 425

def get_existing_image_ids():
    existing_files = io.get_img_list(OUTPUT)
    existing_image_ids = [int(f.split("_")[0]) for f in existing_files if f.endswith(".wav")]
    return existing_image_ids

def write_TTS_bark(input_text,file_name):
    inputs = processor(input_text, voice_preset=voice_preset)

    audio_array = model.generate(**inputs)
    audio_array = audio_array.cpu().numpy().squeeze()
    scipy.io.wavfile.write(file_name, rate=sample_rate, data=audio_array)

    return
    
def write_TTS_openai(input_text,file_name):
    voice_preset = random.choice(preset_list)
    response = client.audio.speech.create(
      model="tts-1",
      voice=voice_preset,
      input=input_text
    )
    ### SAMPLE RATE 24 kHz
    ## NO OPTION TO CHANGE THIS IN OPENAI
    ## BUT THERE ARE EXTERNAL LIBRARIES
    response.stream_to_file(file_name)
    return

def write_TTS_meta(input_text,file_name):
    inputs = tokenizer(input_text, return_tensors="pt")
    with torch.no_grad():
        audio_array = model(**inputs).waveform
    audio_array = audio_array.cpu().numpy().squeeze()
    scipy.io.wavfile.write(file_name, rate=sample_rate, data=audio_array)
    #  https://huggingface.co/facebook/mms-tts-eng ##
    return

if METHOD=="openai":
    client = OpenAI(api_key=api_key) ##Michael's API key
    model="tts-1", ##(tts-1,tts-1-hd)
    #voice="alloy", ##(alloy, echo, fable, onyx, nova, and shimmer)
    # preset_list=["alloy", "echo", "fable", "onyx", "nova","shimmer","alloy", "fable", "nova","shimmer", "nova","shimmer", "nova","shimmer"] # this is a clunky way of prioritizing higher pitched voices
    preset_list=["alloy", "echo", "fable", "onyx", "nova","shimmer"]
    write_TTS=write_TTS_openai
    
elif METHOD=="bark":
    processor = AutoProcessor.from_pretrained("suno/bark")
    model = BarkModel.from_pretrained("suno/bark")
    sample_rate = model.generation_config.sample_rate
    preset_list = [f"v2/en_speaker_{i}" for i in range(10)]
    write_TTS=write_TTS_bark
    
elif METHOD=="meta":
    model = VitsModel.from_pretrained("facebook/mms-tts-eng")
    tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-eng")


    # processor = AutoProcessor.from_pretrained("suno/bark")
    # model = BarkModel.from_pretrained("suno/bark")
    # sample_rate = model.generation_config.sample_rate
    ## SINCE GARBAGE TO LOWER SAMPLE RATE   
    sample_rate=16000
    # preset_list = [f"v2/en_speaker_{i}" for i in range(10)]
    write_TTS=write_TTS_meta
    


with open(os.path.join(INPUT, sourcefile), mode='r',encoding='utf-8-sig', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    existing_image_ids = get_existing_image_ids()
    # Determine the mode for opening the output CSV file ('w' for new file, 'a' for append)
    mode = 'w' if not os.path.exists(os.path.join(OUTPUT, output_csv)) else 'a'

    # Open the output CSV file for writing (or appending)
    with open(os.path.join(OUTPUT, output_csv), mode, newline='') as output_csvfile:
        # Define the fieldnames for the output CSV file (including new column 'out_name')
        fieldnames = reader.fieldnames + ['out_name']
        writer = csv.DictWriter(output_csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Iterate through each row
        for row in reader:
            image_id = int(row['image_id'])
            if image_id in existing_image_ids:
                print(f"Skipping image_id {image_id} because it already exists {counter}")
                counter += 1
                continue
            # skip row until counter is greater than start_at
            elif counter < start_at:
                counter += 1
                continue
            if counter%10==0: print(counter,"sounds generated")                
            print(row)
            input_text = row['description']
            if METHOD!="meta":
                voice_preset = random.choice(preset_list)
                out_name =f"{str(image_id)}_{METHOD}_v{voice_preset[-1]}_{row['topic_fit']}.wav"
            else:
                ## NO PRESET OPTION FOR META
                out_name =f"{str(image_id)}_{METHOD}_{row['topic_fit']}.wav"            
            file_name=os.path.join(OUTPUT, out_name)
            write_TTS(input_text,file_name)
            # Write the row to the output CSV file with 'out_name' added
            row['out_name'] = out_name
            writer.writerow(row)

            counter += 1
            if counter > STOP_AFTER:
                break

print("Time:", time.time() - start)