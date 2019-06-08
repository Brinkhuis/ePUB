# imports
import epub
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path

# set book metadata
metadata = epub.set_book_metadata(identifier_id='000-00-000-0000-0',
                                 identifier_opf='000-00-000-0000-0',
                                 title='The Holy Bible',
                                 creator='God',
                                 language='en')

# create book folder
epub.create_ebook_folder(folder = metadata['title'])

# create cover file
image_url = 'https://res.cloudinary.com/brinkhuis/image/upload/v1559758477/King-James-Version-Bible-first-edition-title-page-1611_grmdgy.png'
epub.create_coverpage_file(metadata['title'], image_url)

# create css file
f = open(Path(metadata['title']) / 'OEBPS' / 'Styles' / 'styles.css', 'a')
lines = ['h1 {margin-bottom: 0.2em; font-size: 1.8em; font-weight: bold;}',
         'h3 {color: #8B0000; margin-bottom: 0.2em; font-size: 1.2em; font-weight: bold;}',
         '.verseNum{font-size: smaller; font-weight: bold; color: #8B0000;}']
for line in lines:
    f.write(line + '\n')
f.close()


# open file with header
Path('Data').mkdir(exist_ok=True)
f = open('Data/{}.csv'.format(metadata['title'].lower().replace(' ', '_')), 'a')
f.write('|'.join(['book', 'chapter', 'number', 'verse']) +'\n')

# set base url
base_url = 'http://www.o-bible.com'

# scrape book urls
book_urls_unsorted = list()
r = requests.get(base_url + '/kjv.html')
soup = BeautifulSoup(r.content, 'html.parser')
for testament in soup.find_all('table', {'class': 'tm'}):
    for table_data in testament.find_all('td'):
        book_urls_unsorted.append((table_data.text, base_url + table_data.a['href']))

# sort book urls
book_urls_sorted = dict()
for i in range(0, 0 + 3): # sort old testament books
    for j in range(i, 39, 3):
        book_urls_sorted[book_urls_unsorted[j][0]] = book_urls_unsorted[j][1]
for i in range(39, 39 + 3): # sort new testament books
    for j in range(i, 66, 3):
         book_urls_sorted[book_urls_unsorted[j][0]] = book_urls_unsorted[j][1]

# get chapter urls
chapter_urls = list()
for book_url in book_urls_sorted.values():
    r = requests.get(book_url)
    soup = BeautifulSoup(r.content, 'html.parser')
    chapter_urls.append(book_url) # chapter 1
    chapters = soup.find_all('table')[-3].find_all('td')[-1].find_all('a') # next chapters
    for chapter in chapters:
        chapter_urls.append(base_url + chapter['href'])

# get bible verses
bible_verses = list()
for chapter_url in tqdm(chapter_urls, desc='getting chapters'):
    r = requests.get(chapter_url)
    soup = BeautifulSoup(r.content, 'html.parser')
    book = soup.html.head.title.text
    verses = soup.find_all('table')[-2].find_all('tr')
    for verse in verses:
        stripped_strings = verse.stripped_strings
        verse_and_num = next(stripped_strings).split(':')
        chapter_num = verse_and_num[0]
        verse_num = verse_and_num[1]
        verse_txt = next(stripped_strings)
        f.write('|'.join([book, chapter_num, verse_num, verse_txt]) + '\n')
f.close()

# read data
bible = pd.read_csv('Data/{}.csv'.format(metadata['title'].lower().replace(' ', '_')), sep='|')

# rename chapters titles
chapter_counts = bible[['book', 'chapter']].drop_duplicates().groupby(by='book').size()
bible.loc[bible.book.isin(chapter_counts[chapter_counts == 1].index), ['chapter']] = ''
bible.loc[bible.book.isin(chapter_counts[chapter_counts != 1].index), ['chapter']] = bible['book'] + ' ' + bible['chapter'].astype('str')

# create html files
root = Path(metadata['title'])
chapter_titles = bible['book'].unique()
for i in tqdm(range(len(chapter_titles)), desc='writing chapters'):
    file_name = 'chapter_{:04}.html'.format(i + 1)
    f = open(root / 'OEBPS/Text' / file_name, 'a')
    
    # write book title
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<html xmlns="http://www.w3.org/1999/xhtml">',
             '<head>',
             '    <link href="../Styles/styles.css" rel="stylesheet" type="text/css" />',
             '    <title>{}</title>'.format(chapter_titles[i]),
             '</head>',
             '<body>',
             '    <h1>{}</h1>'.format(chapter_titles[i])]
    for line in lines:
        f.write(line + '\n')
    
    # write chapters
    df_book = bible.loc[bible['book'] == chapter_titles[i]]
    for chapter in df_book['chapter'].unique():
        lines = ['    <h3>{}</h3>'.format(chapter),
                 '    <p>']
        for line in lines:
            f.write(line + '\n')
        
        # write verses
        df_chapter = df_book.loc[df_book['chapter'] == chapter]
        for index, row in df_chapter.iterrows():
            lines = ['    <span class="verseNum">{}</span> {}'.format(row['number'], row['verse'])]
            for line in lines:
                f.write(line + '\n')
        f.write('    </p>' + '\n')
    
    lines = ['</body>',
             '</html>']
    for line in lines:
        f.write(line + '\n')  
    f.close()

# create epub file
epub.create_epub_file(metadata, delete_folder=False)
