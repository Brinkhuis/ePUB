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
                                 title='Statenvertaling GBS',
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
f = open('Data/{}.csv'.format(metadata['title'].lower().replace(' ', '_')), 'a')
f.write('|'.join(['book', 'chapter', 'number', 'verse']) +'\n')

# scrape and write data
base_url = 'https://statenvertaling.nl/'
bijbel = list()

for n in range(1, 67):
    start = 'tekst.php?bb={}&hf=1&ind=4#starth'.format(n)
    
    r = requests.get(base_url + start)
    soup = BeautifulSoup(r.content, 'html.parser')
    
    hoofdstukken = soup.find('td', {'class': 'hoofdstukken-lijst'}).find_all('a', href=True)
    for hoofdstuk in hoofdstukken[:-1]:
        
        hfst_r = requests.get(base_url + hoofdstuk['href'])
        hfst_soup = BeautifulSoup(hfst_r.content, 'html.parser')
        
        title_split = hfst_soup.title.text.split(' – ')[0].split()
        if len(title_split) == 1:
            book = title_split[0]
            chapter = book
        elif len(title_split) == 2 and title_split[0].isdigit():
            book = ' '.join(title_split)
            chapter = book
        elif len(title_split) == 2 and title_split[1].isdigit():
            book = title_split[0]
            chapter = title_split[1]
        else:
            book = ' '.join(title_split[:-1])
            chapter = title_split[-1]
        
        if book == 'Psalm':
            book = 'Psalmen'
        
        verses = hfst_soup.find('table', {'class': 'tekst'}).find_all('td', {'class': 'tekstbreed'})
        for verse in verses:
            verse_num = verse.text.split()[0]
            verse_txt = ' '.join(verse.text.split()[1:])
        
            bijbel.append([book, chapter, verse_num, verse_txt])
            
df = pd.DataFrame(bijbel, columns = ['book', 'chapter', 'number', 'verse'])
df.to_csv('Data/{}.csv'.format(metadata['title'].lower().replace(' ', '_')), sep='|', index=False)

# read data
bible = pd.read_csv('Data/{}.csv'.format(metadata['title'].lower().replace(' ', '_')), sep='|')

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
