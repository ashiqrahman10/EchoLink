import sounddevice as sd
import numpy as np
import speech_recognition as sr
import subprocess
import wave
import pygame
import io
from groq import Groq
import queue
import threading
import time
from scipy.io import wavfile
import tempfile
import os

class AudioChat:
    def __init__(self, groq_api_key, voice_model="en_US-amy-medium.onnx"):
        # Initialize the speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Set Piper voice model
        self.voice_model = voice_model
        
        # Initialize Groq client for LLM
        self.client = Groq(api_key=groq_api_key)
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=22050)  # Piper's default sample rate
        
        # Audio settings
        self.sample_rate = 44100
        self.channels = 1
        self.dtype = np.int16
        
        # Queues for audio processing
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
        # Conversation history
        self.conversation = []

    def setup_tts(self):
        """Check if piper is installed"""
        try:
            subprocess.run(['piper', '--help'], capture_output=True)
        except FileNotFoundError:
            print("Error: Piper TTS is not installed. Please install it first:")
            print("Instructions:")
            print("1. Download from https://github.com/rhasspy/piper/releases")
            print("2. Extract the archive")
            print("3. Add piper binary to your PATH")
            print("4. Download voice models from https://huggingface.co/rhasspy/piper-voices/tree/main")
            sys.exit(1)

    def record_audio(self):
        """Record audio from microphone"""
        def callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            self.audio_queue.put(indata.copy())

        with sd.InputStream(samplerate=self.sample_rate,
                          channels=self.channels,
                          dtype=self.dtype,
                          callback=callback):
            print("\nListening... Press Ctrl+C to stop.")
            while self.is_recording:
                time.sleep(0.1)

    def save_audio_to_file(self):
        """Save recorded audio to a temporary WAV file"""
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
        
        if audio_data:
            audio_data = np.concatenate(audio_data)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            wavfile.write(temp_file.name, self.sample_rate, audio_data)
            return temp_file.name
        return None

    def transcribe_audio(self, audio_file):
        """Convert speech to text"""
        with sr.AudioFile(audio_file) as source:
            audio = self.recognizer.record(source)
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return None

    def get_llm_response(self, user_input):
        """Get response from LLM and format it for natural conversation"""
        # Add system message to encourage conversational tone
        system_message = {
            "role": "system",
            "content": "You are having a natural, spoken conversation. Keep responses concise and conversational. Use natural speech patterns and avoid technical language unless necessary. Pause naturally between thoughts."
        }
        self.conversation.append({"role": "user", "content": user_input})
        
        messages = [system_message] + [{"role": msg["role"], "content": msg["content"]} for msg in self.conversation]
        
        response = self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": assistant_message})
        return assistant_message

    def clean_response_for_speech(self, text):
        """Clean up the LLM response to make it more natural for speech"""
        # Remove markdown formatting
        text = text.replace('*', '').replace('_', '').replace('#', '')
        
        # Replace common symbols with spoken equivalents
        replacements = {
            '%': ' percent',
            '&': ' and',
            '+': ' plus',
            '=': ' equals',
            '→': ' leads to',
            '...': '.',  # Replace ellipsis with period
            '  ': ' ',   # Remove double spaces
        }
        for symbol, replacement in replacements.items():
            text = text.replace(symbol, replacement)
        
        # Add natural pauses with SSML-like markup
        sentences = text.split('. ')
        text = '. <break time="500ms"> '.join(sentences)
        
        # Clean up any remaining unnecessary whitespace
        text = ' '.join(text.split())
        
        return text

    def speak_response(self, text):
        """Convert text to speech using Piper TTS and play it"""
        # Clean up the text for more natural speech
        clean_text = self.clean_response_for_speech(text)
        
        try:
            # Create a temporary file for the audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Run Piper TTS command
                process = subprocess.Popen(
                    [
                        'piper',
                        '--model', self.voice_model,
                        '--output_raw'  # Output raw audio data
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Send text to Piper and get raw audio data
                stdout, stderr = process.communicate(input=clean_text)
                
                if process.returncode != 0:
                    raise Exception(f"Piper TTS failed: {stderr}")
                
                # Convert raw audio to WAV
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(22050)  # Piper's default sample rate
                    wav_file.writeframes(stdout.encode())
                
                # Play the audio using pygame
                pygame.mixer.music.load(temp_file.name)
                pygame.mixer.music.play()
                
                # Wait for audio to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                # Clean up
                pygame.mixer.music.unload()
                os.unlink(temp_file.name)
                
        except Exception as e:
            print(f"TTS Error: {e}")
            # Implement additional fallback if needed

    def start_chat(self):
        """Main chat loop"""
        print("Starting audio chat... Press Ctrl+C to exit.")
        
        try:
            while True:
                # Start recording
                self.is_recording = True
                record_thread = threading.Thread(target=self.record_audio)
                record_thread.start()
                
                # Wait for user input (Ctrl+C) to stop recording
                try:
                    while True:
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    self.is_recording = False
                    record_thread.join()
                
                # Process recorded audio
                audio_file = self.save_audio_to_file()
                if audio_file:
                    # Transcribe audio to text
                    user_text = self.transcribe_audio(audio_file)
                    os.unlink(audio_file)  # Clean up temporary file
                    
                    if user_text:
                        print(f"\nYou said: {user_text}")
                        
                        # Get LLM response
                        llm_response = self.get_llm_response(user_text)
                        print(f"Assistant: {llm_response}")
                        
                        # Speak the response
                        self.speak_response(llm_response)
                    
                print("\nListening... Press Ctrl+C to stop.")

        except KeyboardInterrupt:
            print("\nEnding chat session.")

if __name__ == "__main__":
    # Replace with your Groq API key
    GROQ_API_KEY = "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"
    
    chat = AudioChat(GROQ_API_KEY)
    chat.start_chat()