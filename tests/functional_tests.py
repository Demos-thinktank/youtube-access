import unittest
import main
import os
import csv

from auth import auth
from tests.data.example_video_details import example_response


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        self.test_videos = [
            {'id':'XCspzg9-bAg',
            'title': "Batroll'd",
            'channelId': "UCoQlkuHszaZqv4CGwPYGFvg"},
            {'id': 'WqV22NbR5Wc',
             'title': 'Rainbow Bunchie 10 hours'},
            {'id': 'w_MSFkZHNi4',
            'title': 'DOUBLE KING'}]
        self.client = main.YoutubeClient(credentials=auth.credentials)
        test_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(test_dir, 'data')
        self.out_csv = os.path.join(self.data_dir, 'test-out.csv')

    def tearDown(self):
        if os.path.exists(self.out_csv):
            os.remove(self.out_csv)

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

        # Check titles
        for v in videos:
            expected = [t['title'] for t in self.test_videos
                        if t['id'] == v.id][0]
            observed = v.title
            self.assertEquals(observed,expected)

    def test_video_written_to_csv(self):
        self.assertFalse(os.path.exists(self.out_csv))
        videos = [main.Video(v) for v in example_response['items']]
        main.write_objects_to_csv(objects=videos,
                                  out_path=self.out_csv)
        self.assertTrue(os.path.exists(self.out_csv))

        # Check all videos written
        with open(self.out_csv, 'r') as object_file:
            reader = csv.DictReader(object_file)
            lines = [l for l in reader]
            self.assertEquals(len(lines), 2)

    def test_can_get_and_write_comments(self):
        comments = self.client.get_comments('XCspzg9-bAg',
                                            limit=10, per_page=5)
        self.assertEquals(len(comments), 10)

        self.assertFalse(os.path.exists(self.out_csv))
        main.write_objects_to_csv(objects=comments,
                                  out_path=self.out_csv)
        self.assertTrue(os.path.exists(self.out_csv))

        # Check all comments written
        with open(self.out_csv, 'r') as object_file:
            reader = csv.DictReader(object_file)
            lines = [l for l in reader]
            self.assertEquals(len(lines), 10)


if __name__ == '__main__':
    unittest.main()