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
                                 title='Statenvertaling',
                                 creator='God',
                                 language='nl')


# create book folder
epub.create_ebook_folder(folder = metadata['title'])


# create cover file
image_url = 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Statenvertaling_title_page.jpg'
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
base_url = 'https://www.statenvertaling.net/'


# get book urls
book_urls = dict()

r = requests.get(base_url + 'oude-testament.html')
soup = BeautifulSoup(r.content, 'html.parser')
for book in soup.table.find_all('li'):
    book_urls[book.text] = base_url + book.a['href']

r = requests.get(base_url + 'nieuwe-testament.html')
soup = BeautifulSoup(r.content, 'html.parser')

for book in soup.table.find_all('a'):
    book_urls[book.text] = base_url + book['href']


# get chapter urls
chapter_urls = dict()

for key, value in book_urls.items():

    r = requests.get(value)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    boeklijst = soup.find('div', {'id': 'boeklijst'})
    urls = boeklijst.find_all('a', href=True)
    
    chapter = dict()
    
    for url in urls:
                
        chapter[url.text] = base_url + 'bijbel/' + url['href']
        chapter_urls[key] = chapter

chapters = pd.DataFrame()

for book_key, book_value in chapter_urls.items():
    for chapter_key, chapter_value in book_value.items():
        chapters = chapters.append(pd.Series([book_key, chapter_key, chapter_value]),
                                   ignore_index=True)

chapters.columns = ['book', 'chapter', 'url']


# get bible verses
bible = pd.DataFrame()

for index, row in tqdm(chapters.iterrows()):

    r = requests.get(row['url'])
    soup = BeautifulSoup(r.content, 'html.parser')
    
    tekst = soup.find('div', {'id': 'tekst'})
    verses = tekst.find_all('p', id=True)
    
    for verse in verses:
        number_verse = verse.stripped_strings
        data = pd.Series([row['book'], row['chapter'], next(number_verse), next(number_verse)])
        bible = bible.append(data, ignore_index=True)
        
bible.columns = ['book', 'chapter', 'number', 'verse']


# rename chapters titles
chapter_counts = bible[['book', 'chapter']].drop_duplicates().groupby(by='book').size()
bible.loc[bible.book.isin(chapter_counts[chapter_counts == 1].index), ['chapter']] = ''


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
