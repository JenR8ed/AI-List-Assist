1. Create `extensions.py` file to hold global dependencies.
   - Initialize `db` (ValuationDatabase)
   - Initialize `valuation_service` (ValuationService)
   - Initialize `category_service` (EBayCategoryService)
   - Initialize `category_generator` (CategoryDetailGenerator)
   - Initialize `draft_image_manager` (DraftImageManager)
   - Initialize `vision_service` (VisionService)
   - Initialize `conversation_orchestrator` (ConversationOrchestrator)
   - Initialize `listing_engine` (ListingSynthesisEngine)
   - Initialize `ebay_integration` (eBayIntegration)
   - This prevents circular dependencies when separating routes into Blueprints.

2. Verify `extensions.py` was created correctly using `cat extensions.py`.

3. Create the `routes/ui.py` Blueprint file.
   - It will handle: `/`, `/simple`, and `/uploads/<filename>`.
   - The original code will be moved from `app_enhanced.py`.

4. Verify `routes/ui.py` was created correctly using `cat routes/ui.py`.

5. Create the `routes/analysis.py` Blueprint file.
   - It will handle: `/api/analyze`, `/api/valuations/recent`, `/api/valuations/approved`, `/api/valuations/<valuation_id>`, `/api/valuations/<valuation_id>/approve`, `/api/stats`.
   - The original code will be moved from `app_enhanced.py`.

6. Verify `routes/analysis.py` was created correctly using `cat routes/analysis.py`.

7. Create the `routes/listings.py` Blueprint file.
   - It will handle: `/api/listing/create`, `/api/listing/publish`, `/api/listing/update-draft`, `/api/listing/create-draft`, `/api/listings/drafts`.
   - The original code will be moved from `app_enhanced.py`.

8. Verify `routes/listings.py` was created correctly using `cat routes/listings.py`.

9. Create the `routes/ebay.py` Blueprint file.
   - It will handle: `/api/ebay/oauth/url`, `/api/ebay/submit-listing`, `/api/ebay/live-listings`, `/api/ebay/refresh-listings`, `/api/ebay/listing/<ebay_listing_id>`, `/api/ebay/update-listing`, `/api/ebay/end-listing`, `/api/ebay/token/status`, `/api/ebay/token/refresh`.
   - The original code will be moved from `app_enhanced.py`.

10. Verify `routes/ebay.py` was created correctly using `cat routes/ebay.py`.

11. Create the `routes/conversation.py` Blueprint file.
    - It will handle: `/api/conversation/start`, `/api/conversation/answer`.
    - The original code will be moved from `app_enhanced.py`.

12. Verify `routes/conversation.py` was created correctly using `cat routes/conversation.py`.

13. Create the `routes/categories.py` Blueprint file.
    - It will handle: `/api/category/<category_id>/aspects`, `/api/category/questions`, `/api/category/suggest`, `/api/category/<category_id>/fields`.
    - The original code will be moved from `app_enhanced.py`.

14. Verify `routes/categories.py` was created correctly using `cat routes/categories.py`.

15. Create `routes/__init__.py` file to export all the Blueprints.

16. Refactor `app_enhanced.py`:
    - Remove the old route definitions and service initialization.
    - Import services from `extensions.py`.
    - Add `app.register_blueprint(ui_bp)`, `app.register_blueprint(analysis_bp)`, etc., for all blueprints.

17. Verify `app_enhanced.py` structure by running `python -m py_compile app_enhanced.py`.

18. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
    - Use pytest tests/ with `PYTHONPATH=$PYTHONPATH:/home/jules/.local/share/pipx/venvs/poetry/lib/python3.12/site-packages:/home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages` and environment variables.

19. Submit the fix with a commit message "🧹 [Refactor app_enhanced.py to use Blueprints]".
