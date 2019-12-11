# -*- coding: utf-8 -*-

import math

from googleapiclient.errors import HttpError


def assemble_query(id_list, length=50):
    """
    In order to save on API limits, YT will allow you to pass 50 ids in the
    'query' parameter. This f assembles those lists into a single
    comma seperated string.

    >>> assemble_query(['a','b','c','d'], length=3)
    ['a,b,c', 'd']

    :param id_list: A list of strings to be queried (e.g. video ids)
    :param length: Max length of lists to be returned
    :return: A list of strings
    """
    final_list = []
    chunks = math.floor(len(id_list) / length) + 1
    for i in range(chunks):
        final_list.append(",".join(id_list[i*length:(i+1)*length]))
    return final_list


def search_by_keyword(client, query, limit,
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
    :param since: Retuen videos published after this date
    :param per_page: Number of results to request per page (50 is YT's limit)
    :param order: Order in which to return IDs. viewCount sorts by views,
    descending
    :return: A list of video ids related to the query
    """
    ids = []

    request = client.search().list(
        part='id',
        publishedAfter=since,
        maxResults=per_page,
        q=query,
        order=order
    )
    response = request.execute()
    ids.extend(response['items'])

    if limit:
        while len(ids) < limit:
            try:
                next_page_token = response['nextPageToken']
                try:
                    request = client.search().list(
                        part='id',
                        pageToken=next_page_token
                    )
                    response = request.execute()
                    ids.extend(response['items'])
                except HttpError as e:
                    print("403 on video - likely due to be rate limits.")
                    raise e
            except KeyError:
                print('Found all videos for search term {}'.format(query))
                break


if __name__ == "__main__":
    import doctest
    doctest.testmod()
