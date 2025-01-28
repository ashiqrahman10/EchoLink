import asyncio
import json
import logging
import os
import uuid
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import aiosqlite
import numpy as np
import pyaudio
import torch
import librosa
import noisereduce as nr
from scipy import signal
from dotenv import load_dotenv
from groq import Groq
from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
    pipeline,
    AutoModelForSequenceClassification,
    AutoTokenizer
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('emergency_calls.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CallAnalysis(BaseModel):
    """Pydantic model for call analysis output"""
    summary: str = Field(description="Brief summary of the emergency call")
    criticality: str = Field(description="Call criticality: high, medium, or low")
    is_spam: bool = Field(description="Whether the call appears to be spam")
    department: str = Field(description="Relevant department: Fire, Police, or Medical")
    user_name: str = Field(description="Caller's name if provided, otherwise Unknown")
    location: str = Field(description="Call location if provided, otherwise Unknown")

class AudioProcessor:
    def __init__(self):
        self.target_sr = 16000  # Target sample rate for wav2vec2
        
    def reduce_noise(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """Apply noise reduction to audio data."""
        try:
            # Apply noise reduction
            reduced_noise = nr.reduce_noise(
                y=audio_data,
                sr=sr,
                stationary=True,
                prop_decrease=1.0
            )
            return reduced_noise
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio_data
            
    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to a consistent volume level."""
        try:
            # Peak normalization
            peak = np.abs(audio_data).max()
            if peak > 0:
                normalized = audio_data / peak * 0.9  # Leave some headroom
                return normalized
            return audio_data
        except Exception as e:
            logger.warning(f"Audio normalization failed: {e}")
            return audio_data
            
    def apply_bandpass_filter(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """Apply bandpass filter to focus on speech frequencies."""
        try:
            # Define speech frequency range (Hz)
            lowcut = 80
            highcut = 7000
            
            # Design Butterworth bandpass filter
            nyquist = sr / 2
            low = lowcut / nyquist
            high = highcut / nyquist
            order = 4
            b, a = signal.butter(order, [low, high], btype='band')
            
            # Apply filter
            filtered = signal.filtfilt(b, a, audio_data)
            return filtered
        except Exception as e:
            logger.warning(f"Bandpass filtering failed: {e}")
            return audio_data
            
    def remove_silence(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """Remove silent segments from audio."""
        try:
            # Use librosa's effects module to trim silence
            trimmed, _ = librosa.effects.trim(
                audio_data,
                top_db=30,
                frame_length=2048,
                hop_length=512
            )
            return trimmed
        except Exception as e:
            logger.warning(f"Silence removal failed: {e}")
            return audio_data
            
    def enhance_speech(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """Apply multiple processing steps to enhance speech quality."""
        try:
            # 1. Remove silence
            audio = self.remove_silence(audio_data, sr)
            
            # 2. Apply noise reduction
            audio = self.reduce_noise(audio, sr)
            
            # 3. Apply bandpass filter
            audio = self.apply_bandpass_filter(audio, sr)
            
            # 4. Normalize audio
            audio = self.normalize_audio(audio)
            
            return audio
        except Exception as e:
            logger.error(f"Speech enhancement failed: {e}")
            return audio_data
            
    def resample_audio(self, audio_data: np.ndarray, orig_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        try:
            if orig_sr != self.target_sr:
                audio_resampled = librosa.resample(
                    y=audio_data,
                    orig_sr=orig_sr,
                    target_sr=self.target_sr
                )
                return audio_resampled
            return audio_data
        except Exception as e:
            logger.warning(f"Audio resampling failed: {e}")
            return audio_data

class AudioRecorder:
    def __init__(self, 
                 chunk: int = 1024,
                 format_type: int = pyaudio.paFloat32,
                 channels: int = 1,
                 rate: int = 16000,
                 silence_threshold: float = 0.01,
                 silence_duration: float = 2.0,
                 noise_reduction_strength: float = 0.5):
        self.chunk = chunk
        self.format = format_type
        self.channels = channels
        self.rate = rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.noise_reduction_strength = noise_reduction_strength
        self.p = pyaudio.PyAudio()
        self.audio_processor = AudioProcessor()
        
        # Buffer for noise profile estimation
        self.noise_buffer_duration = 1.0  # seconds
        self.noise_buffer_size = int(self.noise_buffer_duration * self.rate)
        
    async def calibrate_noise(self, stream) -> np.ndarray:
        """Record ambient noise for noise profile estimation."""
        logger.info("Calibrating noise levels... Please remain silent")
        noise_frames = []
        
        try:
            for _ in range(0, int(self.noise_buffer_size / self.chunk)):
                data = await asyncio.to_thread(stream.read, self.chunk)
                noise_frames.append(np.frombuffer(data, dtype=np.float32))
            
            noise_profile = np.concatenate(noise_frames)
            logger.info("Noise calibration complete")
            return noise_profile
        except Exception as e:
            logger.error(f"Error during noise calibration: {e}")
            return np.zeros(self.noise_buffer_size)
        
    async def record(self) -> Tuple[str, np.ndarray]:
        """Record audio with noise reduction and enhancement."""
        frames = []
        silent_frames = 0
        required_silent_frames = int(self.silence_duration * self.rate / self.chunk)
        
        stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        # Calibrate noise profile
        noise_profile = await self.calibrate_noise(stream)
        
        logger.info("Recording started... Speak now")
        
        try:
            while True:
                data = await asyncio.to_thread(stream.read, self.chunk)
                frames.append(data)
                
                audio_data = np.frombuffer(data, dtype=np.float32)
                if np.max(np.abs(audio_data)) < self.silence_threshold:
                    silent_frames += 1
                else:
                    silent_frames = 0
                    
                if silent_frames >= required_silent_frames and len(frames) > required_silent_frames:
                    break
                    
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            raise
        finally:
            stream.stop_stream()
            stream.close()
            
        logger.info("Recording finished")
        
        # Convert frames to numpy array
        audio_array = np.concatenate([np.frombuffer(frame, dtype=np.float32) for frame in frames])
        
        # Process audio
        try:
            logger.info("Enhancing audio quality...")
            enhanced_audio = self.audio_processor.enhance_speech(audio_array, self.rate)
            
            # Save both original and enhanced versions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            orig_filename = f"call_original_{timestamp}.wav"
            enhanced_filename = f"call_enhanced_{timestamp}.wav"
            
            # Save original
            with wave.open(orig_filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(audio_array.tobytes())
            
            # Save enhanced
            with wave.open(enhanced_filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(enhanced_audio.tobytes())
            
            logger.info(f"Saved original audio to {orig_filename}")
            logger.info(f"Saved enhanced audio to {enhanced_filename}")
            
            return enhanced_filename, enhanced_audio
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            # Fallback to original audio if enhancement fails
            filename = f"call_fallback_{timestamp}.wav"
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.p.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(audio_array.tobytes())
            return filename, audio_array

class SpeechRecognizer:
    def __init__(self):
        self.processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
        self.model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
        self.model.eval()
        
    async def transcribe(self, audio_array: np.ndarray) -> str:
        try:
            inputs = self.processor(
                audio_array,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True
            )
            
            with torch.no_grad():
                logits = self.model(inputs.input_values).logits
                
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            return transcription.lower()
        except Exception as e:
            logger.error(f"Error in transcription: {e}")
            return ""

class EmotionAnalyzer:
    def __init__(self):
        self.model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
        self.emotion_classifier = pipeline(
            "audio-classification",
            model=self.model_name
        )
        
    async def analyze_emotion(self, audio_array: np.ndarray) -> Dict[str, float]:
        try:
            emotions = await asyncio.to_thread(
                self.emotion_classifier,
                audio_array
            )
            return {emotion['label']: emotion['score'] for emotion in emotions}
        except Exception as e:
            logger.error(f"Error in emotion analysis: {e}")
            return {'neutral': 1.0}

class DatabaseManager:
    SCHEMA = '''
    CREATE TABLE IF NOT EXISTS conversations (
        uid TEXT PRIMARY KEY,
        conversation TEXT NOT NULL,
        audio_file TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        summary TEXT,
        criticality TEXT CHECK(criticality IN ('high', 'medium', 'low')),
        is_spam BOOLEAN DEFAULT FALSE,
        user_name TEXT DEFAULT 'Unknown',
        location TEXT DEFAULT 'Unknown',
        department TEXT CHECK(department IN ('Fire', 'Police', 'Medical', 'Unknown')),
        emotion_data TEXT,
        confidence_score REAL
    )
    '''
    
    def __init__(self, db_path: str = 'conversation.db'):
        self.db_path = db_path
        
    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(self.SCHEMA)
            await db.commit()
            
    async def store_conversation(self, data: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO conversations 
                (uid, conversation, audio_file, timestamp, summary, criticality, 
                is_spam, user_name, location, department, emotion_data, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    data['conversation'],
                    data['audio_file'],
                    datetime.now().isoformat(),
                    data['analysis'].summary,
                    data['analysis'].criticality.lower(),
                    data['analysis'].is_spam,
                    data['analysis'].user_name,
                    data['analysis'].location,
                    data['analysis'].department,
                    json.dumps(data.get('emotion_data', {})),
                    data.get('confidence_score', 0.0)
                )
            )
            await db.commit()

class ConversationAnalyzer:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.output_parser = PydanticOutputParser(pydantic_object=CallAnalysis)
        
    async def analyze_conversation(self, transcript: str) -> CallAnalysis:
        try:
            system_prompt = """You are an emergency call analyzer. Analyze the call transcript and extract key information.
            Provide your analysis in the following JSON format:
            {
                "summary": "Brief summary of the emergency call",
                "criticality": "high/medium/low",
                "is_spam": true/false,
                "department": "Fire/Police/Medical",
                "user_name": "Caller name or Unknown",
                "location": "Call location or Unknown"
            }
            """
            
            chat_completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript}
                ],
                model="llama3-8b-8192",
                temperature=0.1
            )
            
            response_text = chat_completion.choices[0].message.content
            response_dict = json.loads(response_text)
            
            return CallAnalysis(
                summary=response_dict["summary"],
                criticality=response_dict["criticality"],
                is_spam=response_dict["is_spam"],
                department=response_dict["department"],
                user_name=response_dict["user_name"],
                location=response_dict["location"]
            )
            
        except Exception as e:
            logger.error(f"Error in conversation analysis: {e}")
            return CallAnalysis(
                summary="Analysis failed",
                criticality="high",
                is_spam=False,
                department="Unknown",
                user_name="Unknown",
                location="Unknown"
            )

class EmergencyCallHandler:
    def __init__(self, groq_key: str):
        self.db = DatabaseManager()
        self.audio_recorder = AudioRecorder()
        self.speech_recognizer = SpeechRecognizer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.conversation_analyzer = ConversationAnalyzer(groq_key)
        
    async def initialize(self):
        await self.db.initialize()
        
    async def handle_call(self) -> Optional[Dict[str, Any]]:
        try:
            # Record audio
            audio_file, audio_array = await self.audio_recorder.record()
            
            # Transcribe speech
            transcript = await self.speech_recognizer.transcribe(audio_array)
            if not transcript:
                logger.warning("No speech detected in the recording")
                return None
                
            # Analyze emotions
            emotions = await self.emotion_analyzer.analyze_emotion(audio_array)
            
            # Analyze conversation
            analysis = await self.conversation_analyzer.analyze_conversation(transcript)
            
            # Calculate confidence score based on emotion analysis
            confidence_score = max(emotions.values()) if emotions else 0.0
            
            # Combine all data
            data = {
                'conversation': transcript,
                'audio_file': audio_file,
                'emotion_data': emotions,
                'analysis': analysis,
                'confidence_score': confidence_score
            }
            
            # Store in database
            await self.db.store_conversation(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error handling call: {e}")
            return None

async def main():
    load_dotenv()
    
    if not os.getenv("GROQ_API_KEY"):
        raise EnvironmentError("Missing GROQ_API_KEY environment variable")
        
    handler = EmergencyCallHandler(
        groq_key=os.getenv("GROQ_API_KEY")
    )
    
    try:
        await handler.initialize()
        result = await handler.handle_call()
        if result:
            logger.info(f"Successfully processed emergency call: {result['analysis'].summary}")
            logger.info(f"Emotions detected: {result['emotion_data']}")
            logger.info(f"Confidence score: {result['confidence_score']}")
        else:
            logger.warning("Failed to process emergency call")
    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Program terminated due to error: {e}")