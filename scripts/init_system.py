"""Initialize the system: ingest documents and train routing model."""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_settings
from app.database import engine, Base
from rag.ingestion import DocumentIngestion
from ml.training import train_router_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


def main():
    """Initialize the complete system."""
    logger.info("="*60)
    logger.info("Initializing Enterprise Onboarding Copilot")
    logger.info("="*60)
    
    # Step 1: Create database tables
    logger.info("\n[1/3] Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return 1
    
    # Step 2: Ingest policy documents
    logger.info("\n[2/3] Ingesting policy documents...")
    try:
        ingestion = DocumentIngestion()
        results = ingestion.ingest_all_policies()
        
        print("\nIngestion Results:")
        print("-" * 40)
        for filename, count in results.items():
            print(f"  {filename}: {count} chunks")
        print("-" * 40)
        print(f"Total: {sum(results.values())} chunks")
        
        if sum(results.values()) == 0:
            logger.warning("No documents were ingested!")
    except Exception as e:
        logger.error(f"Failed to ingest documents: {e}")
        return 1
    
    # Step 3: Train routing model
    logger.info("\n[3/3] Training routing model...")
    try:
        results = train_router_model(register_model=False)
        
        print("\nTraining Results:")
        print("-" * 40)
        print(f"Accuracy: {results['metrics']['accuracy']:.4f}")
        print(f"F1 Macro: {results['metrics']['f1_macro']:.4f}")
        print(f"Model saved to: {results['model_path']}")
    except Exception as e:
        logger.error(f"Failed to train routing model: {e}")
        return 1
    
    logger.info("\n" + "="*60)
    logger.info("System initialization complete!")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("1. Create a .env file with your OPENAI_API_KEY")
    logger.info("2. Start the backend: python -m app.main")
    logger.info("3. Start the frontend: cd ui && npm run dev")
    
    return 0


if __name__ == "__main__":
    exit(main())

