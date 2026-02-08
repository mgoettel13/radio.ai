from speechify import Speechify
import os

client = Speechify(
    token="xfwVyPc52SkSfD9CTMt195O6Y2RKJomFpocA0jVWUu8=",
)
audio_response = client.tts.audio.speech(
    input="The death toll from the January 1, 2026, fire at Le Constellation bar in Crans-Montana, Switzerland, has risen to 41 after an 18-year-old Swiss national died from injuries in a Zurich hospital on January 31.[1][4] The blaze, which started in the crowded basement during New Year's celebrations when sparklers on champagne bottles ignited flammable ceiling insulation, injured over 100 people, many with severe burns, amid reports of a blocked emergency exit and inadequate fire safety measures.[2][3] Swiss prosecutors have launched a criminal investigation into the bar owners for negligent homicide, bodily harm, and arson, with one co-owner under bail and his wife under house arrest.[3][4]",
    voice_id="oliver",
    audio_format="mp3")




with open("output.mp3", "wb") as f:
    # Debug: Log the type of audio_data
    import sys
    print(f"audio_data type: {type(audio_response.audio_data)}", file=sys.stderr)
    print(f"audio_data length: {len(audio_response.audio_data) if hasattr(audio_response.audio_data, '__len__') else 'N/A'}", file=sys.stderr)
    
    # Check if it's a string that needs decoding
    if isinstance(audio_response.audio_data, str):
        print("audio_data is a string, attempting to decode from base64", file=sys.stderr)
        import base64
        f.write(base64.b64decode(audio_response.audio_data))
    else:
        f.write(audio_response.audio_data)

# Play with Windows default player
os.system("start output.mp3")