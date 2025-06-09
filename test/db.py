import pytest
import pytest_asyncio

from SpotifyBot.app.db import Database


@pytest_asyncio.fixture
async def db():
    database = Database()
    await database.connect()
    yield database
    await database.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input,expected",
    [((111, 'user'), True),
     ((111, 'user'), False),
     ((111, 'another'), False),
     ((112, 'user'), False),
     ((123, 'another'), True),
     (('133', 'other'), True),
     ((1234, 214), True),
     (('sdgds', 214), False)]
)
@pytest.mark.dependency(name="add")
async def test_add_user(db, test_input, expected):
    add = await db.add_user(*test_input)
    assert add is expected

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input,expected",
    [((111, 'user'), True),
     ((111, 'user'), False),
     ((111, 'another'), False),
     ((112, 'user'), False),
     ((123, 'another'), True),
     (('133', 'other'), True),
     ((1234, 214), True),
     (('sdgds', 214), False)]
)
@pytest.mark.dependency(name="add")
async def test_add_user(db, test_input, expected):
    add = await db.add_user(*test_input)
    assert add is expected
