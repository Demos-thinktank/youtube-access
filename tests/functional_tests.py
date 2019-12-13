import unittest
import main
from auth import auth


class TestStringMethods(unittest.TestCase):

    def test_create_client_using_credentials(self):
        client = main.YoutubeClient(credentials=auth.credentials)


if __name__ == '__main__':
    unittest.main()