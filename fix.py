with open("routes/ebay.py", "r") as f:
    text = f.read()
text = text.replace("if listing_id:\n                draft_image_manager.cleanup_draft_images(listing_id)", "if listing_id:\n                draft_image_manager.cleanup_draft_images(listing_id)")
