# app/vector_store.py
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import os
import sys

# Add parent directory to path to import verses_data
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.verses import verses_data

class GitaVectorStore:
    def __init__(self):
        print("🔄 Initializing Vector Store...")
        
        # Use local embedding model (free, no API key needed)
        # This model runs on your computer
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with persistent storage
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="bhagavad_gita"
        )
        
        # Load data if collection is empty
        if self.collection.count() == 0:
            print("📚 Loading verses into database...")
            self.load_verses()
        else:
            print(f"✅ Database already has {self.collection.count()} verses loaded!")
    
    def load_verses(self):
        """Load all verses into vector database"""
        documents = []
        metadatas = []
        ids = []
        
        for i, verse in enumerate(verses_data):
            # Create rich searchable text with multiple fields
            search_text = f"""
            Chapter {verse['chapter']}, Verse {verse['verse']}:
            Translation: {verse['translation']}
            Tags: {', '.join(verse['tags'])}
            Keywords: {', '.join(verse['keywords'])}
            """
            
            documents.append(search_text)
            metadatas.append({
                "chapter": verse['chapter'],
                "verse": verse['verse'],
                "translation": verse['translation'],
                "tags": ", ".join(verse['tags']),
                "sanskrit": verse.get('sanskrit', '')
            })
            ids.append(f"ch{verse['chapter']}_v{verse['verse']}_{i}")
        
        # Add all verses to collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Loaded {len(documents)} verses into database!")
    
    def search(self, query, n_results=3):
        """Search for relevant verses based on user's question"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return results
    
    def get_verse_by_id(self, chapter, verse):
        """Get a specific verse by chapter and verse number"""
        verse_id = f"ch{chapter}_v{verse}"
        # This would need implementation - we can add later
        pass

# Test the vector store
if __name__ == "__main__":
    print("Testing Vector Store...")
    store = GitaVectorStore()
    
    # Test searches
    test_queries = [
        "I'm feeling very anxious about my future",
        "My loved one passed away, how do I cope?",
        "I can't control my anger",
        "What is my purpose in life?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🙏 Question: {query}")
        print('='*60)
        
        results = store.search(query)
        
        print("\n📖 Relevant Verses Found:")
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\n{i}. Chapter {meta['chapter']}, Verse {meta['verse']}")
            print(f"   {meta['translation'][:150]}...")
            print(f"   🏷️  Tags: {meta['tags']}")