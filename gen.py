from gtts import gTTS
import os

def text_to_audio_from_file(text_file, output_audio_file):
    try:
        # Ensure the 'assets' directory exists
        os.makedirs('assets', exist_ok=True)
        
        # Read the content from the text file
        with open(text_file, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Initialize gTTS with the text content
        tts = gTTS(text=text, lang='en')
        
        # Save the audio file in 'assets' folder
        tts.save(output_audio_file)
        print(f"Audio saved as {output_audio_file}")
    
    except Exception as e:
        print(f"Error occurred: {e}")

# Example usage
text_file = 'assets/audio.txt'  # Input text file
output_audio_file = 'assets/audio.mp3'  # Output audio file in assets folder
text_to_audio_from_file(text_file, output_audio_file)
