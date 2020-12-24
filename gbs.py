import epub
import os
import pandas as pd
import re
import requests
import shutil
from bs4 import BeautifulSoup
from pathlib import Path
from PIL import Image


# book info
info = {}
info['title'] = 'GBS'
info['ISBN'] = ''
info['creator'] = ''
info['language'] = 'nl'
info['subject'] = ''


# set title color
info['color'] = '#0d47a1'


# create download directory
download_dir = Path('Downloads')
download_dir.mkdir(exist_ok=True)


# download cover image
url = 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Statenvertaling_title_page.jpg'
r = requests.get(url, allow_redirects=True)
open(download_dir / 'cover.jpg', 'wb').write(r.content)


# scrape data
base_url = 'https://statenvertaling.nl/'
data = list()

for n in range(1, 67):
    start = 'tekst.php?bb={}&hf=1&ind=4#starth'.format(n)
    
    r = requests.get(base_url + start)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    hoofdstukken = soup.find('td', {'class': 'hoofdstukken-lijst'}).find_all('a', href=True)
    for hoofdstuk in hoofdstukken:
        
        
        hfst_request = requests.get(base_url + hoofdstuk['href'])
        hfst_soup = BeautifulSoup(hfst_request.content, 'html.parser')
        
        title_split = hfst_soup.title.text.split(' – ')[0].split()
        if title_split[0] == 'Inleiding':
            # Skip chapters like 'Inleiding Bijbelboek' and 'Inleiding Nieuwe Testament'
            continue
        elif len(title_split) == 3:
            # '2 Koningen 3'
            # book = '2 Koningen'
            # chapter = 3
            book = ' '.join(title_split[:-1])
            chapter = title_split[-1]
        elif len(title_split) == 2 and title_split[0].isdigit():
            # '3 Johannes'
            # book = '3 Johannes'
            # chapter = '1'
            book = ' '.join(title_split)
            chapter = '1'
        elif len(title_split) == 2 and title_split[1].isdigit():
            # 'Psalm 100'
            # book = 'Psalm'
            # chapter = '100'
            book = title_split[0]
            chapter = title_split[1]
        elif len(title_split) == 1:
            # 'Filemon'
            # book = 'Filemon'
            # chapter = '1'
            book = title_split[0]
            chapter = '1'
        else:
            print("Error: Check book and chapter for: '{}'".format(' '.join(title_split)))
            book = ' '.join(title_split)
            chapter = ' '.join(title_split)
        
        if book == 'Psalm':
            book = 'Psalmen'
        
        verses = hfst_soup.find('table', {'class': 'tekst'}).find_all('td', {'class': 'tekstbreed'})
        for verse in verses:
            verse_num = verse.text.split()[0]
            verse_txt = ' '.join(verse.text.split()[1:])
        
            data.append([book, chapter, verse_num, verse_txt])
            
bible = pd.DataFrame(data, columns = ['book', 'chapter', 'verse', 'text'])


# save dataframe
data_dir = Path('Data')
data_dir.mkdir(exist_ok=True)
bible.to_csv(data_dir / '{}.csv'.format(info['title'].lower().replace(' ', '_')), sep='|', index=False)


# read data
#bible = pd.read_csv('Data/{}.csv'.format(metadata['title'].lower().replace(' ', '_')), sep='|')


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
