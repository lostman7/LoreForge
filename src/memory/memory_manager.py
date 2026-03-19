"""
Memory manager for handling floating memory and RAG retrieval.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class MemoryManager:
    """Manages character memory and context retrieval."""

    def __init__(self, config: dict):
        self.config = config
        self.max_memory_mb = config.get('memory', {}).get('max_floating_mb', 50)
        self.vector_db_path = config.get('memory', {}).get('vector_db_path', str(Path(__file__).parent.parent.parent / 'knowledge' / 'chroma_storage'))

        self.floating_memory: List[Dict[str, Any]] = []
        self.current_preset = None
        self.collection = None

        if CHROMA_AVAILABLE:
            try:
                # Use simpler ephemeral client for now to avoid file path issues
                self.client = chromadb.EphemeralClient()
                self.collection = self.client.get_or_create_collection(name="memory")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("[MemoryManager] ✅ ChromaDB initialized successfully.")
            except Exception as e:
                self.client = None
                self.embedding_model = None
                self.collection = None
                print(f"[MemoryManager] ❌ Initialization failed: {e}")
        else:
            self.client = None
            self.embedding_model = None
            print("[MemoryManager] ⚠️ ChromaDB not available - using fallback memory only")

    def is_ready(self) -> bool:
        """Check if memory system is ready for use."""
        return self.collection is not None

    def load_preset_memory(self, preset_name: str, player_name: Optional[str] = None):
        """Load memory for a specific preset and optional player."""
        self.current_preset = preset_name
        self.current_player = player_name
        self.floating_memory = []

        if not self.client:
            return

        # Create collection name based on preset and player
        if player_name:
            collection_name = f"memory_{preset_name.replace(' ', '_')}_{player_name.replace(' ', '_')}"
        else:
            collection_name = f"memory_{preset_name.replace(' ', '_')}"

        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            self.collection = self.client.create_collection(collection_name)

        # Load recent interactions into floating memory
        results = self.collection.get(limit=20, include=['documents', 'metadatas'])
        for doc, meta in zip(results['documents'], results['metadatas']):
            self.floating_memory.append({
                'content': doc,
                'metadata': meta
            })

    def add_interaction(self, user_message: str, ai_response: str):
        """Add a new interaction to memory."""
        if not self.collection or not self.embedding_model:
            return

        # Create memory entry
        memory_text = f"User: {user_message}\nAI: {ai_response}"
        embedding = self.embedding_model.encode(memory_text).tolist()

        # Add to vector DB
        import uuid
        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[memory_text],
            embeddings=[embedding],
            metadatas=[{
                'type': 'interaction',
                'timestamp': str(Path(__file__).stat().st_mtime),  # Placeholder
                'preset': self.current_preset
            }]
        )

        # Add to floating memory
        self.floating_memory.append({
            'content': memory_text,
            'metadata': {'type': 'interaction'}
        })

        # Trim floating memory if too large (rough estimate)
        while len(str(self.floating_memory)) > self.max_memory_mb * 1024 * 1024:
            self.floating_memory.pop(0)

    def get_context(self, query: str, max_results: int = 5) -> str:
        """Retrieve relevant context for a query."""
        if not self.collection or not self.embedding_model:
            # Fallback to floating memory
            return "\n".join([item['content'] for item in self.floating_memory[-max_results:]])

        # Search vector DB
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max_results,
            include=['documents']
        )

        context = []
        if results['documents']:
            context.extend(results['documents'][0])

        # Add recent floating memory
        context.extend([item['content'] for item in self.floating_memory[-3:]])

        return "\n".join(context)

    def index_character_documents(self, preset_name: str, documents_dir: Path):
        """Index all text files in a directory for a character."""
        if not self.collection or not self.embedding_model:
            return 0

        indexed_count = 0
        for ext in ['*.txt', '*.md']:
            for file_path in documents_dir.glob(ext):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if not content.strip():
                        continue
                    
                    # Split into chunks (simple for now)
                    chunks = [content[i:i+1000] for i in range(0, len(content), 800)]
                    
                    for i, chunk in enumerate(chunks):
                        embedding = self.embedding_model.encode(chunk).tolist()
                        import uuid
                        self.collection.add(
                            ids=[f"{file_path.name}_{i}_{uuid.uuid4()}"],
                            documents=[chunk],
                            embeddings=[embedding],
                            metadatas=[{
                                'source': file_path.name,
                                'preset': preset_name,
                                'type': 'document'
                            }]
                        )
                    indexed_count += 1
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")
        
        return indexed_count

    def consolidate_memory(self, preset_name: str):
        """Consolidate and clean up memory for a preset."""
        try:
            # Load existing memory
            memory_file = Path("./Memory") / f"{preset_name}.json"
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)

                conversations = memory_data.get('conversations', [])

                # Keep only recent conversations (last 50)
                if len(conversations) > 50:
                    conversations = conversations[-50:]
                    memory_data['conversations'] = conversations

                    # Save cleaned memory
                    with open(memory_file, 'w') as f:
                        json.dump(memory_data, f, indent=2)

                    print(f"Memory consolidated for {preset_name}: kept {len(conversations)} conversations")

        except Exception as e:
            print(f"Memory consolidation failed for {preset_name}: {e}")