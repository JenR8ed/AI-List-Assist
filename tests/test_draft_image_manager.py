import os
import pytest
from pathlib import Path
from services.draft_image_manager import DraftImageManager

@pytest.fixture
def temp_drafts_dir(tmp_path):
    """Fixture providing a temporary directory for drafts."""
    drafts_dir = tmp_path / "drafts"
    drafts_dir.mkdir()
    return str(drafts_dir)

@pytest.fixture
def image_manager(temp_drafts_dir):
    """Fixture providing a DraftImageManager instance."""
    return DraftImageManager(drafts_folder=temp_drafts_dir)

@pytest.fixture
def dummy_images(tmp_path):
    """Fixture providing a list of dummy image file paths."""
    source_dir = tmp_path / "source_images"
    source_dir.mkdir()

    img1 = source_dir / "test1.jpg"
    img1.write_text("dummy image content 1")

    img2 = source_dir / "test2.png"
    img2.write_text("dummy image content 2")

    return [str(img1), str(img2)]

def test_init_creates_folder(tmp_path):
    """Test that initializing DraftImageManager creates the drafts folder if it doesn't exist."""
    new_drafts_dir = tmp_path / "new_drafts"

    assert not new_drafts_dir.exists()

    manager = DraftImageManager(drafts_folder=str(new_drafts_dir))

    assert new_drafts_dir.exists()
    assert new_drafts_dir.is_dir()

def test_save_draft_images_success(image_manager, dummy_images, temp_drafts_dir):
    """Test successful saving of draft images."""
    listing_id = "test_listing_123"

    saved_paths = image_manager.save_draft_images(listing_id, dummy_images)

    assert len(saved_paths) == 2

    expected_dir = Path(temp_drafts_dir) / listing_id
    assert expected_dir.exists()

    for path_str in saved_paths:
        assert Path(path_str).exists()

    assert saved_paths[0].endswith(".jpg")
    assert saved_paths[1].endswith(".png")

    assert Path(saved_paths[0]).name == "image_0.jpg"
    assert Path(saved_paths[1]).name == "image_1.png"

    assert Path(saved_paths[0]).read_text() == "dummy image content 1"
    assert Path(saved_paths[1]).read_text() == "dummy image content 2"

def test_save_draft_images_missing_files(image_manager, dummy_images, tmp_path):
    """Test saving draft images when some source files don't exist."""
    listing_id = "test_listing_456"
    non_existent_image = str(tmp_path / "source_images" / "does_not_exist.jpg")

    images_to_save = [dummy_images[0], non_existent_image, dummy_images[1]]

    saved_paths = image_manager.save_draft_images(listing_id, images_to_save)

    assert len(saved_paths) == 2

    assert saved_paths[0].endswith("image_0.jpg")
    assert saved_paths[1].endswith("image_2.png")

def test_cleanup_draft_images_success(image_manager, dummy_images, temp_drafts_dir):
    """Test successful cleanup of a listing's draft images."""
    listing_id = "test_listing_cleanup"

    image_manager.save_draft_images(listing_id, dummy_images)
    draft_dir = Path(temp_drafts_dir) / listing_id

    assert draft_dir.exists()

    result = image_manager.cleanup_draft_images(listing_id)

    assert result is True
    assert not draft_dir.exists()

def test_cleanup_draft_images_not_found(image_manager, temp_drafts_dir):
    """Test cleanup when the listing's draft directory doesn't exist."""
    listing_id = "non_existent_listing"

    draft_dir = Path(temp_drafts_dir) / listing_id
    assert not draft_dir.exists()

    result = image_manager.cleanup_draft_images(listing_id)

    assert result is False
