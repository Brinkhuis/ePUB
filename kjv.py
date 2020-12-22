import epub
import gzip
import os
import pandas as pd
import re
import requests
from pathlib import Path
from PIL import Image


# book info
info = {}
info['title'] = 'KJV'
info['ISBN'] = ''
info['creator'] = ''
info['language'] = 'en'
info['subject'] = ''


# set title color
info['color'] = '#660066'


# create download directory
download_dir = Path('Downloads')
download_dir.mkdir(exist_ok=True)


# download gzip file
url = 'http://www.o-bible.com/download/kjv.gz'
r = requests.get(url, allow_redirects=True)
open(download_dir / 'kjv.gz', 'wb').write(r.content)


# extract gzip file
with open(download_dir / 'kjv.txt', 'w') as file, gzip.open(download_dir / 'kjv.gz', 'rt', encoding='utf-8') as ip:
    file.write(ip.read())


# download cover image
url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/King-James-Version-Bible-first-edition-title-page-1611.png/800px-King-James-Version-Bible-first-edition-title-page-1611.png'
r = requests.get(url, allow_redirects=True)
open(download_dir / 'cover.png', 'wb').write(r.content)


# convert png to jpg
img = Image.open(download_dir / 'cover.png')
img.save(download_dir / 'cover.jpg')


# kjv.txt to dataframe
books = []
chapters = []
verses = []
texts = []

file = open(download_dir / 'kjv.txt', 'r')
lines = file.readlines()

for line in lines[1:]:
    space = line.find(' ')
    index = line[:space] # index bible verse like 'Ge1:1'
    match = re.search(r'\d', index[1:]).start() # find position chapter number
    books.append(index[:match+1]) # book (everything before the chapter number)
    split = index[match+1:].split(':') # split chapter and verse numbers
    chapters.append(split[0])
    verses.append(split[1])
    texts.append(line[space+1:].strip())

books_unique = []
for book in books:
    if book not in books_unique:
        books_unique.append(book)

book_names = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
              'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings',
              '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah',
              'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes',
              'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel',
              'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah',
              'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
              'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
              '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
              'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
              '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
              '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude',
               'Revelation']
    
book_dict = {key:value for (key,value) in zip(books_unique, book_names)}
  
bible = pd.DataFrame({'book': [book_dict[book] for book in books],
                      'chapter': chapters,
                      'verse': verses,
                      'text': texts})


# save dataframe
data_dir = Path('Data')
data_dir.mkdir(exist_ok=True)
bible.to_csv(data_dir / '{}.csv'.format(info['title'].lower().replace(' ', '_')), sep='|', index=False)


# read data
#bible = pd.read_csv('Data/{}.csv'.format(metadata['title'].lower().replace(' ', '_')), sep='|')


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
