import pytest
import pytest_asyncio
from datetime import datetime
from dateutil.relativedelta import relativedelta

from SpotifyBot.app.tools.db import Database


@pytest_asyncio.fixture
async def db() -> Database:
    """
    Initalize database instance for all consequent tests
    :yield: Database instance
    """
    database = Database()
    await database.connect()
    yield database
    await database.close()


@pytest.mark.asyncio
@pytest.mark.dependency(name="init")
async def test_init(db):
    """
    Test tables initialization
    :param db: Database instance
    :return: assert whether tables were created successfully (T/F)
    """
    response = await db.initialize()
    assert response == True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input, expected",
    [
        ((111, "user"), True),
        ((111, "user"), False),
        ((111, "another"), False),
        ((112, "user"), False),
        ((123, "another"), True),
        (("133", "other"), True),
        ((1234, "214"), True),
        ((11244, 213), False),
        (("sdgds", 214), False),
    ],
)
@pytest.mark.dependency(name="add_user", depends=["block"])
async def test_add_user(db, test_input, expected):
    """
    Test tables adding user
    :param db: Database instance
    :param test_input: (userID, username) input
    :param expected: expected output (T/F)
    :return: assert whether user was created successfully (T/F)
    """
    response = await db.add_user(*test_input)
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input,expected",
    [
        (111, (111, "user")),
        (211, None),
        (112, None),
        (123, (123, "another")),
        ("133", (133, "other")),
        (1234, (1234, "214")),
        ("sdgds", None),
    ],
)
@pytest.mark.dependency(name="get_user_by_id", depends=["add_user"])
async def test_get_user_by_id(db, test_input, expected):
    """
    Test getting user by id from users table
    :param db: Database instance
    :param test_input: userID example
    :param expected: expected output (userID, username)/None
    :return: assert whether output is correct (T/F)
    """
    response = await db.get_user_by_id(test_input)
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("user", (111, "user")),
        ("another", (123, "another")),
        ("username", None),
        ("anotherx2", None),
        ("other", (133, "other")),
        (214, None),
        ("214", (1234, "214")),
    ],
)
@pytest.mark.dependency(name="get_user_by_name", depends=["add_user"])
async def test_get_user_by_name(db, test_input, expected):
    response = await db.get_user_by_name(test_input)
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input,expected",
    [
        ((111, None), True),
        ((111, "user"), True),
        ((211, None), False),
        ((123, "another2"), True),
        ((123, "another"), True),
        (("133", "other3"), True),
        ((1234, 215), False),
        (("sdgds", 123), False),
    ],
)
@pytest.mark.dependency(name="update_username", depends=["get_user_by_id", "get_user_by_name"])
async def test_update_username(db, test_input, expected):
    response = await db.update_username(*test_input)
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("user", True),
        ("user", False),
        ("another", True),
        ("anotherx2", False),
        ("another", False),
        ("other3", True),
        (214, False),
        ("214", True),
    ],
)
@pytest.mark.dependency(
    name="delete_user", depends=["update_username"]
)
async def test_delete_user(db, test_input, expected):
    response = await db.delete_user(test_input)
    assert response == expected


######################################


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input, expected",
    [
        ((1, "spotify 001", datetime.now()), True),
        ((1, "spotify 002", datetime.now()), False),
        ((3, "spotify 003", datetime.now()), True),
        ((4, "spotify 004", datetime.now()), True),
        ((5, "spotify 004", datetime.now()), False),
        ((6, "spotify 005", '2025-07-07'), False),
        ((7, "spotify 005", 'spotify 005'), False),
        (('8', "spotify 006", datetime.now()), True),
        (('8', 7, datetime.now()), False),
    ],
)
@pytest.mark.dependency(name="add_group", depends=["init"])
async def test_add_group(db, test_input, expected):
    response = await db.add_group(*test_input)
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input, expected",
    [
        (1, (1, "spotify 001",
             (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
            )),
        (3, (3, "spotify 003",
             (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
            )),
        (5, None),
        (6, None),
        ('8', (8, "spotify 006",
               (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
            )),
        (8, (8, "spotify 006",
             (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
            )),
    ],
)
@pytest.mark.dependency(name="get_group_by_id", depends=["add_group"])
async def test_get_group_by_id(db, test_input, expected):
    response = await db.get_group_by_id(test_input)
    if response:
        response = (response[0], response[1], response[2].strftime("%Y-%m-%d"))
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("spotify 001", (1, "spotify 001",
                         (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
                        )),
        ("spotify 003", (3, "spotify 003",
                         (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
                        )),
        ("nonexistent group", None),
        ("", None),
        ("SPOTIFY 001", (1, "spotify 001",
                         (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
                        )),
        ("spotify 006", (8, "spotify 006",
                         (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%d')
                        )),
    ],
)
@pytest.mark.dependency(name="get_group_by_name", depends=["add_group"])
async def test_get_group_by_name(db, test_input, expected):
    """Test getting a group by group name

    Args:
        db: Database instance
        test_input (str): The group name
        expected (tuple or None):
            (group_id, group_name, payment_at, created_at) or None if not found

    Assertions:
        - With valid name function will return group information
        - With invalid/non-existent name function will return None
    """
    response = await db.get_group_by_name(test_input)
    if response:
        response = (
            response[0],
            response[1],
            response[2].strftime("%Y-%m-%d")
        )
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "group_id, new_name, expected",
    [
        (1, "updated spotify 001", True),
        (3, "renamed group 003", True),
        (8, "new name for group 8", True),
        (999, "nonexistent group update", False),  # Non-existent group
        (1, "", False),  # Empty name
        (1, None, False),  # None name
        (-1, "negative id test", False),  # Invalid ID
        (0, "zero id test", False),  # Invalid ID
    ],
)
@pytest.mark.dependency(name="update_group_name", depends=["get_group_by_id", "get_group_by_name"])
async def test_update_group_name(db, group_id, new_name, expected):
    """Test updating group name

    Args:
        db: Database fixture instance for testing
        group_id (int): The ID of the group to update
        new_name (str or None): The new name to assign to the group
        expected (bool):
            True for successful updates, False for failed updates

    Assertions:
        - Returns True for successful updates
        - Returns False for failed updates (invalid ID, invalid name)
    """
    response = await db.update_group_name(group_id, new_name)
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "group_name, expected",
    [
        ("", False), # Empty test
        ("updated spotify 001", True),
        ("renamed GROUP 003", True), # Case sensitivity test
        ("spotify 006", True),
        ("nonexistent group", False),  # Non-existent group
        ("", False),  # Empty name
        ("SPOTIFY 001", False),  # Old name test
        ("spotify 006", False),  # Previously deleted group
    ],
)
@pytest.mark.dependency(name="delete_group", depends=["update_group_name"])
async def test_delete_group(db, group_name, expected):
    """Test deleting a group by group name

    Args:
        db: Database instance
        group_name (str): The name of the group
        expected (bool):
            True for successful deletions, False for failed deletions

    Assertions:
        - Returns True for successful deletions
        - Returns False for failed deletions (non-existent group)
    """
    response = await db.delete_group(group_name)
    assert response == expected


@pytest.mark.asyncio
@pytest.mark.dependency(name="drop")
async def test_drop(db):
    """
    Test tables dropping
    :param db: Database instance
    :return: assert whether tables were dropped successfully (T/F)
    """
    response = await db.drop_tables()
    assert response == True


# TESTS TO BE CREATED:
# payment get
# payment check
# payment edit
# payment delete
# payment statistic
