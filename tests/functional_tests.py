import unittest
import main
from auth import auth


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        self.test_videos = [
            {'id':'XCspzg9-bAg',
            'title': "Batroll'd",
            'channelId': "UCoQlkuHszaZqv4CGwPYGFvg"},
            {'id': 'WqV22NbR5Wc',
             'title': 'DOUBLE KING'},
            {'id': 'w_MSFkZHNi4',
            'title': 'Rainbow Bunchie 10 hours'}]
        self.client = main.YoutubeClient(credentials=auth.credentials)

    def test_search_for_keywords(self):
        """
        We're going to do multiple tests here to avoid calling this endpoint
        too often
        """
        ids = self.client.search_by_keyword("crime owl", 10, per_page=5,
                                            since='01/01/2018')
        expected_id_length = 11

        # Check IDs are of the right length, and the list isn't empty
        self.assertEqual(len(ids[0]), expected_id_length)

        # Check the right number of IDs are returned, and we're paginating
        self.assertEqual(len(ids), 10)

    def test_get_videos_by_id(self):
        test_ids = [v['id'] for v in self.test_videos]
        query = main.assemble_query(test_ids)[0]
        videos = self.client.get_videos(query=query)

        # Check all videos returned
        self.assertEqual(len(videos), len(test_ids))


if __name__ == '__main__':
    unittest.main()