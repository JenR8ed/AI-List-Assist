import re

with open('app_enhanced.py', 'r') as f:
    content = f.read()

# Replace the create_listing logic
old_logic = """        # Create listing draft
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
        c.execute('''
            INSERT INTO listings (listing_id, item_id, title, price, status, draft_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
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
        })"""

new_logic = """        # Create listing draft using LLM synthesis
        listing_draft = listing_engine.create_listing_draft(
            item_id=item_id,
            valuation=valuation,
            conversation_state=conv_state,
            images=original_images
        )

        if listing_draft.missing_required_specifics:
            # Route to state machine for Progressive Questioning
            state = conversation_orchestrator.start_conversation(item_id, listing_draft.model_dump())
            return jsonify({
                "status": "needs_info",
                "session_id": state.session_id
            })

        # Else it is ready
        listing_draft.ready_for_api = True

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
        c.execute('''
            INSERT INTO listings (listing_id, item_id, title, price, status, draft_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            listing_draft.listing_id,
            listing_draft.item_id,
            listing_draft.title,
            listing_draft.price,
            'DRAFT',
            json.dumps(listing_draft.model_dump())
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "listing": listing_draft.model_dump()
        })"""

content = content.replace(old_logic, new_logic)

with open('app_enhanced.py', 'w') as f:
    f.write(content)
