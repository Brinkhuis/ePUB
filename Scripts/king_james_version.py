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


# set base url
base_url = 'http://www.o-bible.com'


# get book urls
book_urls_unsorted = list()

r = requests.get(base_url + '/kjv.html')
soup = BeautifulSoup(r.content, 'html.parser')
for testament in soup.find_all('table', {'class': 'tm'}):
    for table_data in testament.find_all('td'):
        book_urls_unsorted.append((table_data.text, base_url + table_data.a['href']))


# sort book urls
book_urls_sorted = dict()

for i in range(0, 0 + 3):
    for j in range(i, 39, 3):
        book_urls_sorted[book_urls_unsorted[j][0]] = book_urls_unsorted[j][1]
        
for i in range(39, 39 + 3):
    for j in range(i, 66, 3):
         book_urls_sorted[book_urls_unsorted[j][0]] = book_urls_unsorted[j][1]


# get chapter urls
chapter_urls = pd.DataFrame()

for book, book_url in book_urls_sorted.items():
    
    data = pd.Series([book, '1', book_url])
    chapter_urls = chapter_urls.append(data, ignore_index=True)
    
    r = requests.get(book_url)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    chapters = soup.find_all('table')[-3].find_all('td')[-1].find_all('a')
    
    for chapter in chapters:
        
        data = pd.Series([book, chapter.text, base_url + chapter['href']])
        chapter_urls = chapter_urls.append(data, ignore_index=True)
        
chapter_urls.columns = ['book', 'chapter', 'url']


# get bible verses
bible = pd.DataFrame()

for index, row in tqdm(chapter_urls.iterrows()):
    
    r = requests.get(row['url'])
    soup = BeautifulSoup(r.content, 'html.parser')
    
    verses = soup.find_all('table')[-2].find_all('tr')
    
    for verse in verses:
        
        stripped_strings = verse.stripped_strings
        
        number = next(stripped_strings).split(':')[-1]
        verse = next(stripped_strings)
        
        data = pd.Series([row['book'], row['chapter'], number, verse])
        
        bible = bible.append(data, ignore_index=True)
    
bible.columns = ['book', 'chapter', 'number', 'verse']


# rename chapters titles
chapter_counts = bible[['book', 'chapter']].drop_duplicates().groupby(by='book').size()
bible.loc[bible.book.isin(chapter_counts[chapter_counts == 1].index), ['chapter']] = ''
bible.loc[bible.book.isin(chapter_counts[chapter_counts != 1].index), ['chapter']] = bible.book + ' ' + bible.chapter


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
epub.create_epub_file(metadata, delete_folder=True)
