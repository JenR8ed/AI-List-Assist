import os

with open('patch_app.py', 'r') as f:
    content = f.read()

old_logic = '''old_logic = """        # Create listing draft
        listing_draft = listing_engine.create_listing_draft(
            item_id=item_id,
            valuation=valuation,
            conversation_state=conv_state,
            images=original_images
        )

        # Save images to draft storage
        if original_images:
            draft_images = draft_image_manager.save_draft_images(
                listing_draft.listing_id,
                original_images
            )
            listing_draft.images = draft_images

        # Save to database
        conn = sqlite3.connect('listings.db')
        c = conn.cursor()
        c.execute(\'\'\'
            INSERT INTO listings (listing_id, item_id, title, price, status, draft_data)
            VALUES (?, ?, ?, ?, ?, ?)
        \'\'\', (
            listing_draft.listing_id,
            listing_draft.item_id,
            listing_draft.title,
            listing_draft.price,
            'DRAFT',
            json.dumps(listing_draft.to_dict())
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "listing": listing_draft.to_dict()
        })"""'''

new_old_logic = '''old_logic = """        # Create listing draft
        listing_draft = listing_engine.create_listing_draft(
            item_id=item_id,
            valuation=valuation,
            conversation_state=conv_state,
            images=original_images
        )

        # Save images to draft storage
        if original_images:
            draft_images = draft_image_manager.save_draft_images(
                listing_draft.listing_id,
                original_images
            )
            listing_draft.images = draft_images

        # Save to database
        conn = sqlite3.connect('listings.db')
        c = conn.cursor()
        c.execute(\'\'\'
            INSERT INTO listings (listing_id, item_id, title, price, status, draft_data)
            VALUES (?, ?, ?, ?, ?, ?)
        \'\'\', (
            listing_draft.listing_id,
            item_id,
            listing_draft.title,
            listing_draft.price,
            "draft",
            json.dumps(listing_draft.to_dict())
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "listing": listing_draft.to_dict()
        })"""'''

content = content.replace(old_logic, new_old_logic)

with open('patch_app.py', 'w') as f:
    f.write(content)
