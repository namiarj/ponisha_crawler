#!/usr/bin/python3

import logging
import urllib.request
import urllib.parse
from lxml import html

projects_page_url = "https://ponisha.ir/search/projects"

# Set a limit for number of parsed projects
max_projects_allowed = 25

# Telegram bot config
bot_token = ""
chat_id = ""

# Create and configure logger
logging.basicConfig(format = ":: %(levelname)s \t %(message)s")
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

# Function for sending the new projects to Telegram
def sendMessage(text):
    text = urllib.parse.quote(text)
    url = "https://api.telegram.org/bot{}/sendMessage?parse_mode=markdown&disable_web_page_preview=true&chat_id={}&text={}".format(bot_token, chat_id, text)
    logger.debug("requesting: %s", url)
    try:
        urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        logger.error("requested URL returned %d code. exitting...", e.code)
    except urllib.error.URLError as e:
        logger.error("%s. exitting...", e.reason)

# Open last_sent file and import the ids to a list
last_sent = []
try:
    file = open("last_sent", "r")
    for line in file:
        last_sent.append(line)
    file.close()
except IOError:
    logger.warning("there was a problem reading the last_sent file")

# Getting the content of the page
logger.info("requesting: %s", projects_page_url)
try:
    html_response = urllib.request.urlopen(projects_page_url).read()
except urllib.error.HTTPError as e:
    logger.critical("requested URL returned %d code. exitting...", e.code)
    exit(1)
except urllib.error.URLError as e:
    logger.critical("%s. exitting...", e.reason)
    exit(1)

logger.debug("response len: %d bytes", len(html_response))

logger.debug("starting processing...")
html_tree = html.fromstring(html_response)

projects = html_tree.xpath('//*[@class="col-sm-9 col-xs-12 right"]')

number_of_projects = len(projects)
if number_of_projects > max_projects_allowed:
    logger.warning("%d projects. more than maximum allowed. will only process the first %d", number_of_projects, max_projects_allowed)
    number_of_projects = max_projects_allowed
else:
    logger.debug("number of projects: %d", number_of_projects)

project_ids = []
file_change_flag = False
for i in range(number_of_projects):
    project_title = projects[i][0][0][0].text_content().strip()
    project_desc = projects[i][1].text_content().strip()
    
    illegal_chars = "*[]_`~" # Remove special chars to prevent messing up markdown format
	for char in illegal_chars:
		project_title = project_title.replace(char, "")
		project_desc = project_desc.replace(char, "")
    
    project_link = projects[i][0][0].attrib["href"][:33]
    project_id = project_link[-6:]
    project_ids.append(project_id)
    if (project_id + "\n") not in last_sent:
        logger.info("project id %s was not in last_sent. sending the post to Telegram...", project_id)
        sendMessage("*{}*\n\n {}\n\n[لینک به پروژه]({})".format(project_title, project_desc, project_link))
        file_change_flag = True

if file_change_flag:
    logger.info("saving the changes to the last_sent file")
    try:
        file = open("last_sent", "w")
        for project_id in project_ids:
            file.write(project_id + "\n")
        file.close()
    except IOError:
        logger.warning("there was a problem opening the last_sent file")
else:
    logger.debug("no change for the last_sent file")

logger.debug("program done. exitting...")
