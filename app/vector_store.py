# app/vector_store.py
import os
import sys
import glob
import json
import chromadb
from sentence_transformers import SentenceTransformer

# Helper function to load all verses from JSON files dynamically
def load_all_verses_from_json():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    json_files = glob.glob(os.path.join(data_dir, "Bhagavad_Geeta_*.json"))
    
    all_verses = []
    
    for file_path in sorted(json_files):
        filename = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                doc_type = data.get("document_type", "chapter")
                chapter = data.get("chapter", 0)
                chapter_name_hindi = data.get("chapter_name_hindi", "")
                chapter_name_english = data.get("chapter_name_english", "")
                
                # Check for standard verses list
                verses = data.get("verses", [])
                for verse in verses:
                    verse_entry = {
                        "chapter": chapter,
                        "chapter_name_hindi": chapter_name_hindi,
                        "chapter_name_english": chapter_name_english,
                        "verse": verse.get("verse_number", 0),
                        "sanskrit": verse.get("sanskrit", ""),
                        "transliteration": verse.get("transliteration", ""),
                        "translation_hindi": verse.get("translation_hindi", ""),
                        "translation_english": verse.get("translation_english", ""),
                        "keywords_hindi": verse.get("keywords_hindi", []),
                        "keywords_english": verse.get("keywords_english", []),
                        "tags": verse.get("tags", []),
                        "summary_hindi": verse.get("summary_hindi", ""),
                        "summary_english": verse.get("summary_english", ""),
                        "commentary_hindi": verse.get("commentary_hindi", ""),
                        "commentary_english": verse.get("commentary_english", "")
                    }
                    all_verses.append(verse_entry)
                
                # Check for history document context
                if doc_type == "historical_introduction" and "historical_context" in data:
                    context = data["historical_context"]
                    idx = 1
                    for section_name, section_data in context.items():
                        text_hindi = section_data.get("text_hindi", "") or section_data.get("quote_hindi", "")
                        text_english = section_data.get("text_english", "") or section_data.get("quote_english", "")
                        author = section_data.get("author", "")
                        if author:
                            text_english += f" - Quote by {author}"
                        
                        verse_entry = {
                            "chapter": 0,
                            "chapter_name_hindi": "ऐतिहासिक परिचय",
                            "chapter_name_english": "Historical Introduction",
                            "verse": 100 + idx,
                            "sanskrit": "",
                            "transliteration": "",
                            "translation_hindi": text_hindi,
                            "translation_english": text_english,
                            "keywords_hindi": ["इतिहास", "ऐतिहासिक", section_name],
                            "keywords_english": ["history", "historical", section_name],
                            "tags": ["history", section_name],
                            "summary_hindi": text_hindi[:150],
                            "summary_english": text_english[:150],
                            "commentary_hindi": "",
                            "commentary_english": ""
                        }
                        all_verses.append(verse_entry)
                        idx += 1
        except Exception as e:
            print(f"Error parsing file {filename}: {e}")
            
    return all_verses

class GitaVectorStore:
    def __init__(self):
        print("[INFO] Initializing Vector Store...")
        
        # Use local embedding model (free, runs on your computer)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with persistent storage
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="bhagavad_gita"
        )
        
        # Load data if collection is empty or has incomplete data (dummy verses)
        current_count = self.collection.count()
        if current_count < 500:
            print(f"[INFO] Database has only {current_count} items. Reloading all 670+ verses...")
            try:
                self.client.delete_collection("bhagavad_gita")
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection("bhagavad_gita")
            self.load_verses()
        else:
            print(f"[SUCCESS] Database already has {current_count} verses loaded!")
    
    def load_verses(self):
        """Load all verses into vector database"""
        verses = load_all_verses_from_json()
        documents = []
        metadatas = []
        ids = []
        
        for i, verse in enumerate(verses):
            # Create rich searchable text with multiple fields for high-quality semantic search
            search_text = f"""
            Chapter {verse['chapter']} ({verse['chapter_name_english']} / {verse['chapter_name_hindi']}), Verse {verse['verse']}:
            Sanskrit: {verse['sanskrit']}
            Transliteration: {verse['transliteration']}
            Hindi Translation: {verse['translation_hindi']}
            English Translation: {verse['translation_english']}
            Summary: {verse['summary_hindi']}
            Commentary: {verse['commentary_hindi']}
            Keywords: {', '.join(verse['keywords_hindi'])} {', '.join(verse['keywords_english'])}
            Tags: {', '.join(verse['tags'])}
            """
            
            documents.append(search_text)
            metadatas.append({
                "chapter": verse['chapter'],
                "chapter_name_hindi": verse['chapter_name_hindi'],
                "chapter_name_english": verse['chapter_name_english'],
                "verse": verse['verse'],
                "translation_hindi": verse['translation_hindi'],
                "translation_english": verse['translation_english'],
                "sanskrit": verse['sanskrit'],
                "transliteration": verse['transliteration'],
                "summary_hindi": verse['summary_hindi'],
                "commentary_hindi": verse['commentary_hindi'],
                "tags": ", ".join(verse['tags'])
            })
            ids.append(f"ch{verse['chapter']}_v{verse['verse']}_{i}")
        
        # Add all verses to collection in batches
        batch_size = 100
        for idx in range(0, len(documents), batch_size):
            self.collection.add(
                documents=documents[idx:idx+batch_size],
                metadatas=metadatas[idx:idx+batch_size],
                ids=ids[idx:idx+batch_size]
            )
        
        print(f"[SUCCESS] Loaded {len(documents)} verses into database!")
    
    def search(self, query, n_results=3):
        """Search for relevant verses based on user's question"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

# Test the vector store
if __name__ == "__main__":
    print("Testing Vector Store...")
    
    # Force UTF-8 stdout encoding for printing Sanskrit/Hindi content in Windows terminal
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
    store = GitaVectorStore()
    
    # Test searches
    test_queries = [
        "I'm feeling very anxious about my future",
        "My loved one passed away, how do I cope?",
        "How do I control my anger?",
        "What is the historical background of the Gita?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Question: {query}")
        print('='*60)
        
        results = store.search(query)
        
        print("\nRelevant Verses Found:")
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\n{i}. Chapter {meta['chapter']} ({meta['chapter_name_english']}), Verse {meta['verse']}")
            print(f"   Sanskrit: {meta['sanskrit']}")
            print(f"   Hindi: {meta['translation_hindi'][:150]}...")
            print(f"   Tags: {meta['tags']}")