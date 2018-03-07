import urllib2
from bs4 import BeautifulSoup
import re
import json

data = []
counter = 0
debugMode = False

with open('happenings_eventLinks.txt', 'r') as f:
  for url in f:
    if debugMode: print "URL: " + url.strip() + '\n'
    data.append({'url': url.strip()})

    # Query website to get html of the page
    page = urllib2.urlopen(url.strip())

    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(page, 'html.parser')
    for e in soup.findAll('br'):
      e.extract()

    # Get the event information
    event_title = soup.find('h2')
    if debugMode: print "TITLE: " + event_title.text.strip() + '\n'
    data[counter]['event_name'] = event_title.text.strip()
    
    event_date_location = soup.find('p', attrs={'id': 'more-info'})
    if debugMode: print "DATE/LOCATION: " 
    if debugMode: print event_date_location.contents[0].strip()
    if debugMode: print event_date_location.contents[1].strip() + '\n'
    data[counter]['date'] = event_date_location.contents[0].strip()
    split = event_date_location.contents[1].split(",")
    data[counter]['time'] = split[0].strip()
    data[counter]['location'] = split[1].strip()

    event_admission = soup.find('h3', text='Admission')
    if debugMode: print "ADMISSION: " + event_admission.next_sibling.text + '\n'
    data[counter]['admission'] = event_admission.next_sibling.text.strip()

    # http://happenings.ucla.edu/all/event/242683
    event_contact = soup.find('h3', text='Contact')
    if debugMode: print "CONTACT: "
    data[counter]['contact'] = []
    for content in event_contact.next_sibling.contents:
      if content.name == 'a' and content.get('href', ''):
        content_re = re.sub('mailto:','', content['href'])
        if debugMode: print content_re
        data[counter]['contact'].append(content_re)
      else:
        if debugMode: print content
        data[counter]['contact'].append(content)
    if debugMode: print '\n'

    event_info = soup.find('h3', text='Additional Information')
    if debugMode: print "INFORMATION: "
    data[counter]['info'] = ""

    shouldPrint = False
    event_details = soup.find_all('div', attrs={'id': 'event-details'})
    for tag in event_details:
      tags = tag.find_all(['p', 'li'])
      for t in tags:
        if t.text == event_info.next_sibling.text:
          shouldPrint = True
        if shouldPrint and t.name == "li":
          if debugMode: print " - " + t.text.strip()
          data[counter]['info'] = data[counter]['info'] + "\n - " + t.text.strip()
        elif shouldPrint:
          if debugMode: print t.text.strip()
          data[counter]['info'] = data[counter]['info'] + "\n" + t.text.strip()

    if debugMode: print "~~~~~~~~~~"
    print counter
    counter += 1

with open('data.txt', 'w') as outfile:
  json.dump(data, outfile, indent=4) #, sort_keys=True)
