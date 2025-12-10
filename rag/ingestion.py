"""Document ingestion pipeline for RAG."""
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from app.config import get_settings
from rag.vectorstore import VectorStoreService, get_vectorstore_service

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a document chunk."""
    text: str
    metadata: Dict[str, Any]
    chunk_id: str


class DocumentIngestion:
    """Pipeline for ingesting and processing policy documents."""
    
    # Department mapping based on filename
    DEPARTMENT_MAPPING = {
        "hr_policies": "HR",
        "it_policies": "IT",
        "security_policies": "Security",
        "finance_policies": "Finance"
    }
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        vectorstore: VectorStoreService = None
    ):
        """Initialize the ingestion pipeline.
        
        Args:
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Overlap between chunks.
            vectorstore: Vector store service to use.
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.vectorstore = vectorstore or get_vectorstore_service()
        self.policies_dir = settings.policies_dir
    
    def load_document(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Load a document from disk.
        
        Args:
            file_path: Path to the document.
            
        Returns:
            Tuple of (document text, metadata).
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract department from filename
        filename = file_path.stem
        department = self.DEPARTMENT_MAPPING.get(filename, "General")
        
        metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "department": department
        }
        
        return content, metadata
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: Raw text.
            
        Returns:
            Cleaned text.
        """
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove markdown artifacts that don't add value
        text = re.sub(r'\|[-:]+\|', '', text)  # Table separators
        
        return text.strip()
    
    def extract_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract sections from markdown content.
        
        Args:
            content: Markdown document content.
            
        Returns:
            List of sections with title and content.
        """
        sections = []
        current_section = {"title": "", "content": "", "level": 0}
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for headers
            header_match = re.match(r'^(#{1,4})\s+(.+)$', line)
            
            if header_match:
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                current_section = {
                    "title": title,
                    "content": f"# {title}\n\n",
                    "level": level
                }
            else:
                current_section["content"] += line + "\n"
        
        # Don't forget the last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Split text into chunks with overlap.
        
        Args:
            text: Text to chunk.
            metadata: Base metadata for chunks.
            
        Returns:
            List of DocumentChunk objects.
        """
        chunks = []
        
        # First try to split by sections
        sections = self.extract_sections(text)
        
        chunk_idx = 0
        for section in sections:
            section_text = self.clean_text(section["content"])
            
            if not section_text:
                continue
            
            # If section is small enough, keep it as one chunk
            if len(section_text) <= self.chunk_size:
                chunk_metadata = {
                    **metadata,
                    "section": section["title"],
                    "chunk_index": chunk_idx
                }
                chunks.append(DocumentChunk(
                    text=section_text,
                    metadata=chunk_metadata,
                    chunk_id=f"{metadata['filename']}_{chunk_idx}"
                ))
                chunk_idx += 1
            else:
                # Split large sections by paragraphs
                paragraphs = section_text.split('\n\n')
                current_chunk = ""
                
                for para in paragraphs:
                    if len(current_chunk) + len(para) <= self.chunk_size:
                        current_chunk += para + "\n\n"
                    else:
                        if current_chunk:
                            chunk_metadata = {
                                **metadata,
                                "section": section["title"],
                                "chunk_index": chunk_idx
                            }
                            chunks.append(DocumentChunk(
                                text=current_chunk.strip(),
                                metadata=chunk_metadata,
                                chunk_id=f"{metadata['filename']}_{chunk_idx}"
                            ))
                            chunk_idx += 1
                        
                        # Start new chunk with overlap
                        overlap_text = current_chunk[-self.chunk_overlap:] if current_chunk else ""
                        current_chunk = overlap_text + para + "\n\n"
                
                # Don't forget remaining content
                if current_chunk.strip():
                    chunk_metadata = {
                        **metadata,
                        "section": section["title"],
                        "chunk_index": chunk_idx
                    }
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        metadata=chunk_metadata,
                        chunk_id=f"{metadata['filename']}_{chunk_idx}"
                    ))
                    chunk_idx += 1
        
        return chunks
    
    def ingest_document(self, file_path: Path) -> int:
        """Ingest a single document.
        
        Args:
            file_path: Path to the document.
            
        Returns:
            Number of chunks created.
        """
        logger.info(f"Ingesting document: {file_path}")
        
        # Load document
        content, metadata = self.load_document(file_path)
        
        # Chunk document
        chunks = self.chunk_text(content, metadata)
        
        if not chunks:
            logger.warning(f"No chunks created from {file_path}")
            return 0
        
        # Add to vector store
        texts = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]
        ids = [c.chunk_id for c in chunks]
        
        self.vectorstore.add_documents(texts, metadatas, ids)
        
        logger.info(f"Created {len(chunks)} chunks from {file_path}")
        return len(chunks)
    
    def ingest_all_policies(self) -> Dict[str, int]:
        """Ingest all policy documents from the policies directory.
        
        Returns:
            Dictionary mapping filename to chunk count.
        """
        results = {}
        
        # Find all markdown files
        policy_files = list(self.policies_dir.glob("*.md"))
        
        if not policy_files:
            logger.warning(f"No policy files found in {self.policies_dir}")
            return results
        
        logger.info(f"Found {len(policy_files)} policy files to ingest")
        
        for file_path in policy_files:
            chunk_count = self.ingest_document(file_path)
            results[file_path.name] = chunk_count
        
        total_chunks = sum(results.values())
        logger.info(f"Ingestion complete. Total chunks: {total_chunks}")
        
        return results
    
    def reset_and_reingest(self) -> Dict[str, int]:
        """Delete existing collection and reingest all documents.
        
        Returns:
            Dictionary mapping filename to chunk count.
        """
        logger.warning("Resetting vector store and reingesting all documents")
        self.vectorstore.delete_collection()
        self.vectorstore = get_vectorstore_service()
        return self.ingest_all_policies()


def run_ingestion():
    """Run the ingestion pipeline."""
    ingestion = DocumentIngestion()
    results = ingestion.ingest_all_policies()
    
    print("\nIngestion Results:")
    print("-" * 40)
    for filename, count in results.items():
        print(f"  {filename}: {count} chunks")
    print("-" * 40)
    print(f"Total: {sum(results.values())} chunks")
    
    # Print collection stats
    stats = ingestion.vectorstore.get_collection_stats()
    print(f"\nCollection '{stats['name']}' has {stats['count']} documents")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion()

