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
image_url = 'https://res.cloudinary.com/brinkhuis/image/upload/v1559758092/Statenvertaling_bbqdua.jpg'
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
f = open('Data/statenvertaling.csv', 'a')
f.write('|'.join(['book', 'chapter', 'number', 'verse']) +'\n')


# scrape and write data
base_url = 'https://www.statenvertaling.net/'
testament_urls = [base_url + page for page in ['oude-testament.html', 'nieuwe-testament.html']]

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
            chapter_title = soup.html.head.title.text.split(' - ')[0]
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


# read data
bible = pd.read_csv('Data/statenvertaling.csv', sep='|')


# rename chapters titles (to blanc when there is only one chapter)
chapter_counts = bible[['book', 'chapter']].drop_duplicates().groupby(by='book').size()
bible.loc[bible.book.isin(chapter_counts[chapter_counts == 1].index), ['chapter']] = ''


# create html files
p = Path(metadata['title'])
chapter_titles = bible['book'].unique()

for i in tqdm(range(len(chapter_titles)), desc='writing chapters'):

    file_name = 'chapter_{:04}.html'.format(i + 1)
    f = open(p / 'OEBPS/Text' / file_name, 'a')
    
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
