from api import *
from auth import auth
import os
from googleapiclient.errors import HttpError

this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, 'data')

videos_out = os.path.join(data_dir, 'example_videos.csv')
comments_out = os.path.join(data_dir, 'example_comments.csv')

client = YoutubeClient(auth.credentials)
video_ids = client.search_by_keyword("teach yourself to",
                                      limit=3,
                                      since='01/01/2019',
                                      order='viewCount')

# Get video details, check for 403s.
video_queries = assemble_query(video_ids, existing=videos_out)
videos = []
for q in video_queries:
    try:
        videos.extend(client.get_videos(q))
        write_objects_to_csv(videos, videos_out)
    except HttpError as e:
        raise

# Get comments
comments = []
for v in video_ids:
    try:
        video_comments = client.get_comments(v,limit=100)
        comments.extend(video_comments)
    except HttpError as e:
        print(e)

write_objects_to_csv(comments, comments_out)
