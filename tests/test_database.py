import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from core.database import init_db

@pytest.mark.asyncio
@patch('core.database.engine')
@patch('core.database.logger')
async def test_init_db_success(mock_logger, mock_engine):
    # Setup mock for engine.begin()
    mock_conn = AsyncMock()
    # The async context manager
    mock_begin = AsyncMock()
    mock_begin.__aenter__.return_value = mock_conn
    mock_engine.begin.return_value = mock_begin

    # Call the function
    await init_db()

    # Verify run_sync was called
    mock_conn.run_sync.assert_called_once()

    # Verify logger.info was called with the success message
    mock_logger.info.assert_called_once_with("✅ Database schema synchronized with Neon Postgres.")

@pytest.mark.asyncio
@patch('core.database.engine')
@patch('core.database.logger')
async def test_init_db_failure(mock_logger, mock_engine):
    # Setup mock for engine.begin()
    mock_conn = AsyncMock()
    # The async context manager
    mock_begin = AsyncMock()
    mock_begin.__aenter__.return_value = mock_conn
    mock_engine.begin.return_value = mock_begin

    # Simulate an exception in run_sync
    test_exception = Exception("Test Database Error")
    mock_conn.run_sync.side_effect = test_exception

    # Call the function and expect an exception
    with pytest.raises(Exception) as exc_info:
        await init_db()

    assert str(exc_info.value) == "Test Database Error"

    # Verify logger.error was called
    mock_logger.error.assert_called_once_with(f"❌ Database initialization failed: {test_exception}")
