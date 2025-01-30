import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import aiosqlite
from dotenv import load_dotenv
from groq import Groq
from hume import HumeVoiceClient, MicrophoneInterface

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

class DatabaseManager:
    SCHEMA = '''
    CREATE TABLE IF NOT EXISTS conversations (
        uid TEXT PRIMARY KEY,
        conversation TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        summary TEXT,
        criticality TEXT CHECK(criticality IN ('high', 'medium', 'low')),
        is_spam BOOLEAN DEFAULT FALSE,
        user_name TEXT DEFAULT 'Unknown',
        location TEXT DEFAULT 'Unknown',
        department TEXT CHECK(department IN ('Fire', 'Police', 'Medical', 'Unknown'))
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
                (uid, conversation, timestamp, summary, criticality, is_spam, user_name, location, department)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    data['conversation'],
                    datetime.now().isoformat(),
                    data['summary'],
                    data['criticality'].lower(),
                    data['isSpam'].lower() == 'yes',
                    data['user'],
                    data['location'],
                    data['department']
                )
            )
            await db.commit()

class ConversationAnalyzer:
    def __init__(self, api_key: str, model: str = 'llama3-8b-8192'):
        self.client = Groq(api_key=api_key)
        self.model = model
        
    async def analyze_conversation(self, conversation: str) -> Dict[str, Any]:
        try:
            chat_summary = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=[
                    {
                        "role": "system",
                        "content": """
                        Analyze the emergency call and provide:
                        {
                            "summary": "Brief call summary",
                            "criticality": "high/medium/low",
                            "isSpam": "Yes/No",
                            "department": "Fire/Police/Medical",
                            "user": "Caller name or Unknown",
                            "location": "Call location or Unknown"
                        }
                        """
                    },
                    {"role": "user", "content": conversation}
                ],
                model=self.model,
                stream=False
            )
            return json.loads(chat_summary.choices[0].message.content.strip())
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return {
                "summary": "Analysis failed",
                "criticality": "high",  # Default to high for safety
                "isSpam": "No",
                "department": "Unknown",
                "user": "Unknown",
                "location": "Unknown"
            }

class EmergencyCallHandler:
    def __init__(self, hume_key: str, groq_key: str, config_id: str):
        self.hume_key = hume_key
        self.config_id = config_id
        self.db = DatabaseManager()
        self.analyzer = ConversationAnalyzer(groq_key)
        self.conversation_file = Path("conversations.txt")
        
    async def initialize(self):
        await self.db.initialize()
        self.conversation_file.write_text("")  # Clear existing conversation
        
    async def record_conversation(self) -> Optional[str]:
        client = HumeVoiceClient(self.hume_key)
        try:
            async with client.connect(config_id=self.config_id) as socket:
                conversation = await MicrophoneInterface.start(
                    socket,
                    allow_user_interrupt=True
                )
                return conversation
        except Exception as e:
            logger.error(f"Error recording conversation: {e}")
            return None
            
    async def process_conversation(self, conversation: str):
        try:
            analysis = await self.analyzer.analyze_conversation(conversation)
            await self.db.store_conversation({
                "conversation": conversation,
                **analysis
            })
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")

async def main():
    # Load environment variables
    load_dotenv()
    required_env = ["HUME_API_KEY", "GROQ_API_KEY", "CONFIG_ID"]
    missing_env = [var for var in required_env if not os.getenv(var)]
    if missing_env:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_env)}")
        
    handler = EmergencyCallHandler(
        hume_key=os.getenv("HUME_API_KEY"),
        groq_key=os.getenv("GROQ_API_KEY"),
        config_id=os.getenv("CONFIG_ID")
    )
    
    try:
        await handler.initialize()
        conversation = await handler.record_conversation()
        if conversation:
            await handler.process_conversation(conversation)
            logger.info("Successfully processed emergency call")
        else:
            logger.warning("No conversation recorded")
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