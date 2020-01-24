# -*- coding: utf-8 -*-

import os
import time
import csv
import json
import math

import googleapiclient.discovery
from googleapiclient.errors import HttpError


class YoutubeClient:
    """
    This object allows you to interface with the Youtube API.
    Instatiates a 'client' attribute, and contains functions which can be used
    to request data from it.
    """

    def __init__(self, credentials, rate_limit_retry=15):
        """
        :param credentials: A dictionary of credentials - must include:
            api_key
            client_id
            client_secret
        :param rate_limit_retry: minutes to wait before retrying request when
            rate limit has been exceeded.
        All of these can be found on your YouTube developer page
        """

        # disable oauthlib's https verification when running locally.
        # *do not* leave this option enabled in production.
        os.environ["oauthlib_insecure_transport"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        developer_key = credentials['api_key']

        self.client = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=developer_key)
        self.rate_limit_retry = rate_limit_retry

    def _search(self, request, limit=math.inf, query_name=None):
        ids = []

        response = _execute_and_retry(request, self.rate_limit_retry)

        for r in response['items']:
            try:
                ids.append(r['id']['videoId'])
            except:
                pass

        if limit > 0:
            while len(ids) < limit:
                try:
                    next_page_token = response['nextPageToken']
                    request = self.client.search().list(
                        part='id',
                        pageToken=next_page_token
                    )
                    response = _execute_and_retry(request, self.rate_limit_retry)
                    found = [i['id']['videoId'] for i in response['items']]
                    ids.extend(found)
                except KeyError:
                    print('Found all videos for search {}'.format(query_name if query_name else request.uri))
                    break
        return ids

    def search_by_channel(self,
                          channel_id,
                          limit=math.inf,
                          since='01/01/2019',
                          per_page='50',
                          order='viewCount'):
        """
        Note: It looks like this search is limited to 500 videos max (even with following next page token).
         See https://developers.google.com/youtube/v3/docs/search/list#channelId

        :param channel_id:
        :param limit:
        :param since:
        :param per_page:
        :param order:
        :return:
        """

        request = self.client.search().list(
            part='id',
            publishedAfter=self.format_date(since),
            maxResults=per_page,
            channelId=channel_id,
            order=order,
            type='video'
        )

        return self._search(request, limit=limit, query_name=channel_id)

    def search_by_keyword(self, query, limit=math.inf,
                          since='01/01/2019',
                          per_page='50',
                          order='viewCount'):
        """
        Return video ids related to a search term. Will scroll through pages
        until it has reached limit ids.

        Relevant API docs
        https://developers.google.com/youtube/v3/docs/search/list

        :param client: Youtube client
        :param query: Keywords to search on
        :param limit: Max number of ids to look for
        :param since: Return videos published after this date
        :param per_page: Number of results to request per page (50 YT's limit)
        :param order: Order in which to return IDs. viewCount sorts by views,
        descending
        :return: A list of video ids related to the query
        """

        request = self.client.search().list(
            part='id',
            publishedAfter=self.format_date(since),
            maxResults=per_page,
            q=query,
            order=order,
            type='video'
        )

        return self._search(request, limit=limit, query_name=query)

    def get_videos(self, query, get_stats=True):
        """
        Query the API for details on videos, by id
        :param query: a comma separated list of video ids
        :param get_stats: boolean: Whether to query view count (at extra cost)
        :return: A list of Video objects
        """
        request_part = 'snippet'
        if get_stats:
            request_part += ',statistics'
        request = self.client.videos().list(
            part=request_part,
            id=query
        )
        response = _execute_and_retry(request, self.rate_limit_retry)
        return [Video(item) for item in response['items']]

    def format_date(self, date, from_format='%d/%m/%Y'):
        """
        Convert human readable date into RFC3339 for the publishedAt attribute
        """
        to_format = "%Y-%m-%dT00:00:00z"
        published_date = time.strptime(date, from_format)
        return time.strftime(to_format, published_date)

    def get_comments(self, from_video_id, limit=math.inf, per_page=50):
        """
        Get top level comments left on a single video
        :return: A list of Comment objects
        """
        comments = []
        request = self.client.commentThreads().list(
            part="snippet",
            maxResults=per_page,
            order="time",
            videoId=from_video_id
        )
        response = _execute_and_retry(request, self.rate_limit_retry)

        comments.extend([Comment(i['snippet']['topLevelComment'])
                         for i in response['items']])

        if limit > 0:
            while len(comments) < limit:
                try:
                    next_page_token = response['nextPageToken']
                    request = self.client.commentThreads().list(
                        pageToken=next_page_token,
                        part='snippet',
                        maxResults=per_page,
                        order="time",
                        videoId=from_video_id
                    )
                    response = _execute_and_retry(request, self.rate_limit_retry)
                    cs = [Comment(i['snippet']['topLevelComment']) for i in response['items']]
                    comments.extend(cs)
                except KeyError:
                    print(f'Found all comments for video {from_video_id}')
                    break
        return comments

    def get_user_channels(self, username, limit=math.inf, per_page=50):

        request = self.client.channels().list(
            part="id,statistics",
            forUsername=username,
            maxResults=per_page
        )
        response = _execute_and_retry(request, self.rate_limit_retry)

        channels = []
        channels += [Channel(item) for item in response['items']]

        if limit > 0:
            while len(channels) < limit:
                try:
                    next_page_token = response['nextPageToken']
                    request = self.client.channels().list(
                        part="id,statistics",
                        forUsername=username,
                        maxResults=per_page,
                        pageToken=next_page_token
                    )
                    response = _execute_and_retry(request, self.rate_limit_retry)
                    channels += [Channel(item) for item in response['items']]
                except KeyError:
                    print('Found all channels for user {}'.format(username))
                    break

        return channels


class Video:

    def __init__(self, detail):
        """
        :param detail: Video item returned from API
        """
        self.id = detail['id']
        snippet = detail['snippet']
        self.channel_id = snippet['channelId']
        self.channel_title = snippet['channelTitle']
        self.title = snippet['title']
        self.published_at = snippet['publishedAt']
        self.thumbnail = snippet['thumbnails']['high']['url']
        self.description = snippet['description']

        # Init stats attributes in case these are included in detail
        self.tags = None
        self.dislikes = None
        self.views = None
        self.likes = None
        self.comment_count = None
        self.favourites = None

        # find statistics
        try:
            r_stats = detail['statistics']
            self.tags = snippet['tags']
            self.dislikes = r_stats['dislikeCount']
            self.views = r_stats['viewCount']
            self.likes = r_stats['likeCount']
            self.comment_count = r_stats['commentCount']
            self.favourites = r_stats['favoriteCount']
        except KeyError:
            # No statistics in record
            pass

        # Define dictionary for printing to CSV
        self.print_header = [
            'id', 'title', 'description', 'published_at', 'channel_id',
            'dislikes', 'views', 'likes', 'comment_count', 'favourites',
            'thumbnail'
        ]
        self.print_dict = {}
        for h in self.print_header:
            self.print_dict[h] = self.__getattribute__(h)


class Channel:

    def __init__(self, detail):
        self.id = detail['id']

        # find statistics
        try:
            r_stats = detail['statistics']
            self.views = r_stats['viewCount']
            self.comment_count = r_stats['commentCount']
            self.video_count = r_stats['videoCount']
            self.subscriber_count = r_stats['subscriberCount']
            self.hidden_subscriber_count = r_stats['hiddenSubscriberCount']
        except KeyError:
            # No statistics in record
            pass

    def __str__(self):
        return "Channel(id=" + self.id + ")"


class Comment:

    def __init__(self, details):
        snippet = details['snippet']
        self.author_channel_url = snippet['authorChannelUrl']
        self.published_at = snippet['publishedAt']
        self.text = snippet['textOriginal']
        self.author_name = snippet['authorDisplayName']
        self.like_count = snippet['likeCount']
        self.id = details['id']
        self.video_id = snippet['videoId']
        self.print_header = [
            'id', 'author_name', 'text', 'like_count', 'published_at',
            'video_id', 'author_channel_url'
        ]
        self.print_dict = {}
        for h in self.print_header:
            self.print_dict[h] = self.__getattribute__(h)


def write_objects_to_csv(objects, out_path, extra_dict=None):
    """
    Write objects (channels, videos, comments etc) to a csv file
    """
    # Append to exiting file if it's there - else write headers
    header = objects[0].print_header
    rows = [o.print_dict for o in objects]
    if extra_dict:
        header.extend(extra_dict.keys())
        for r in rows:
            r.update(extra_dict)

    if not os.path.exists(out_path):
        with open(out_path, 'w') as out_file:
            writer = csv.DictWriter(out_file, header)
            writer.writeheader()
    with open(out_path, 'a', encoding='utf-8-sig') as out_file:
        writer = csv.DictWriter(out_file, header)
        writer.writerows(rows)


def assemble_query(id_list, length=50, existing=None):
    """
    In order to save on API limits, YT will allow you to pass 50 ids in the
    'query' parameter. This fn assembles those lists into a single
    comma seperated string.

    Use the optional 'existing' variable to specify a csv file of previously
    collected records, and remove ids belonging to these from the query to
    prevent unnecessary recollection.

    >>> assemble_query(['a','b','c','d'], length=3)
    ['a,b,c', 'd']

    :param id_list: A list of strings to be queried (e.g. video ids)
    :param length: Max length of lists to be returned
    :param exising: Path to a file which contains already collected records
    :return: A list of strings
    """
    if existing:
        # Read CSVs if file exists, else do nothing
        try:
            with open(existing, 'r') as e_csv:
                reader = csv.DictReader(e_csv)
                existing_ids = set(l['id'] for l in reader)
                id_list = list(set(id_list) - existing_ids)
        except FileNotFoundError:
            pass

    final_list = []
    chunks = math.floor(len(id_list) / length) + 1
    for i in range(chunks):
        final_list.append(",".join(id_list[i * length:(i + 1) * length]))
    return final_list


def _execute_and_retry(request, wait_min=30):
    """
    Execute built HTTP request, if daily rate-limit exceeded, wait and retry same request.

    :param request: HTTP request to `execute`.
    :param wait_min: number of minutes to wait for executing request
    :return:
    """
    while True:
        try:
            return request.execute()
        except HttpError as e:
            reason = _get_http_error_reason(e)

            if reason in ['dailyLimitExceeded', 'quotaExceeded']:
                print(f'Daily limit exceeded, sleeping for {wait_min} mins...')
                time.sleep(wait_min * 60)
            elif reason == 'commentsDisabled':
                print('Comments disabled for video.')
                raise e
            else:
                print('Unknown failure!')
                raise e


def _get_http_error_reason(e: googleapiclient.errors.HttpError):
    try:
        return json.loads(e.content.decode('utf-8'))['error']['errors'][0]['reason']
    except KeyError:
        return "Can't parse error reason from HTTP response!"


if __name__ == "__main__":
    import doctest
    doctest.testmod()
