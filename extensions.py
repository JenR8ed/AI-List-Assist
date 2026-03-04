import logging
from services.vision_service import VisionService
from services.conversation_orchestrator import ConversationOrchestrator
from services.listing_synthesis import ListingSynthesisEngine
from services.ebay_integration import eBayIntegration
from services.valuation_database import ValuationDatabase
from services.valuation_service import ValuationService
from services.ebay_category_service import EBayCategoryService
from services.draft_image_manager import DraftImageManager
from services.category_detail_generator import CategoryDetailGenerator

logger = logging.getLogger(__name__)

# Initialize database and services
db = ValuationDatabase()
valuation_service = ValuationService(use_sandbox=True)
category_service = EBayCategoryService()
category_generator = CategoryDetailGenerator()
draft_image_manager = DraftImageManager()

try:
    vision_service = VisionService()
except Exception as e:
    logger.error(f"Vision service failed: {e}")
    vision_service = None

try:
    conversation_orchestrator = ConversationOrchestrator()
    listing_engine = ListingSynthesisEngine()
    ebay_integration = eBayIntegration(use_sandbox=True)
except Exception as e:
    logger.error(f"Other services warning: {e}")
    conversation_orchestrator = None
    listing_engine = None
    ebay_integration = None
