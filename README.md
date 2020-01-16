# youtube-access
- A tool to access video descriptions, comments etc from Youtube's Data API (see https://developers.google.com/youtube/v3)

This is still in development; at present it will allow you to search YouTube for videos matching a string, collect details pertaining to those videos and comments left under them, and write the results to .csv. The file 'example.py' shows how to do this with the search term "teach yourself to"

SETUP: 
To use this script you will need to create a project with access to the YouTube Data API v3. To do so:

 - Go to https://console.developers.google.com/apis/dashboard and create a new project
 - Click 'Enable APIs and services' and select YouTube Data API v3
 - On the 'Credentials' page for your new project, create an API key. You don't need to mke an OAuth Client ID.
 - Open ./auth/auth-template.py in a text editor, fill in your key values, and save the file as 'auth.py'
 - Install Google API python client: 
 	`pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`

That's it - it should run. 

Unit tests (all passing, I hope) are in tests/

There are many TODOs; the most urgent is to handle 403 reponses due to rate limiting better. 
