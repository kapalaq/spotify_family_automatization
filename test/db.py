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
@pytest.mark.dependency(name="init")
async def test_init(db):
    response = await db.initialize()
    assert response == True

@pytest.mark.asyncio
@pytest.mark.dependency(name="drop", depends=["init"])
async def test_drop(db):
    response = await db.drop_tables()
    assert response == True

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
    pass

# TESTS TO BE CREATED:
# user add
# user edit
# user get
# user delete
# group add
# group get
# group edit
# group delete
# payment add
# payment get
# payment check
# payment edit
# payment delete
# payment statistic
