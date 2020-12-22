import epub
import os
import pandas as pd
import re
import requests
import shutil
from bs4 import BeautifulSoup
from pathlib import Path


# book info
info = {}
info['title'] = 'SV'
info['ISBN'] = ''
info['creator'] = ''
info['language'] = 'nl'
info['subject'] = ''


# set title color
info['color'] = '#800000'


# scrape data and write to file
data_dir = Path('Data')
data_dir.mkdir(exist_ok=True)

f = open(data_dir / '{}.csv'.format(info['title'].lower().replace(' ', '_')), 'a')
f.write('|'.join(['book', 'chapter', 'verse', 'text']) +'\n')

base_url = 'https://www.statenvertaling.net/'
testament_urls = [base_url + 'oude-testament.html', base_url + 'nieuwe-testament.html']

for testament_url in testament_urls:
    r = requests.get(testament_url)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    for book_url in soup.find('table', {'id': 'inhoud'}).find_all('a', href=True):
        r = requests.get(base_url + book_url['href'])
        soup = BeautifulSoup(r.content, 'html.parser')
        
        for chapter_url in soup.find('div', {'id': 'boeklijst'}).find_all('a', href=True):
            r = requests.get(base_url + 'bijbel/' + chapter_url['href'])
            soup = BeautifulSoup(r.content, 'html.parser')
            
            book_title = soup.html.body.div.p.find_all('a')[2].text
            
            chapter_title = soup.html.head.title.text.split(' - ')[0] # i.e. "Genesis 1", "3 Johannes 1" or "Filemon"
            match = re.search(r'\d', chapter_title[1:]) # find first digit but skip first character (i.e. find "1" in "3 Johannes 1")
            if match != None:
                chapter_title = chapter_title[1:][match.start():]
            else:
                chapter_title = '1' # set chapter to 1 if no digit is found (for books like "Filemon", "3 Johannes" or  "Judas")            

            verses = soup.find('div', {'id': 'tekst'}).find_all('p', id=True)
            verse_numbers = [list(verse.stripped_strings)[0] for verse in verses]
            verse_texts = [list(verse.stripped_strings)[1] for verse in verses]
            
            rows = zip([book_title for _ in range(len(verse_numbers))],
                       [chapter_title for _ in range(len(verse_numbers))],
                       verse_numbers,
                       verse_texts)
            
            for row in rows:
                f.write('|'.join([col.strip() for col in row]) + '\n')
            
f.close()


# create download directory
download_dir = Path('Downloads')
download_dir.mkdir(exist_ok=True)


# download cover image
url = 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Statenvertaling_title_page.jpg'
r = requests.get(url, allow_redirects=True)
open(download_dir / 'cover.jpg', 'wb').write(r.content)


# read data
bible = pd.read_csv(data_dir / '{}.csv'.format(info['title'].lower().replace(' ', '_')), sep='|')


# add column
bible['book_chapter'] = None
chapter_counts = bible[['book', 'chapter']].drop_duplicates().groupby(by='book').size()
bible.loc[bible.book.isin(chapter_counts[chapter_counts == 1].index), ['book_chapter']] = ''
bible.loc[bible.book.isin(chapter_counts[chapter_counts != 1].index), ['book_chapter']] = bible['book'] + ' ' + bible['chapter'].astype('str')


# create ebook
epub.create_folders(info)
epub.create_mimetype(info)
epub.create_container(info)
epub.create_cover(info)
epub.create_html(info, bible)
epub.create_content(info)
epub.create_toc(info)
epub.create_css(info)
epub.create_epub(info)
epub.delete_dir(info)


# delete downloads
shutil.rmtree(download_dir)
