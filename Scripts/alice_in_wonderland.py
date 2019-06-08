# imports
import epub
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path

# set book metadata
metadata = epub.set_book_metadata(identifier_id='000-00-000-0000-0', identifier_opf='000-00-000-0000-0',
                                 title='Alice in Wonderland', creator='Lewis Carroll', language='en')

# create book folder
epub.create_ebook_folder(folder = metadata['title'])

# create css file
f = open(Path(metadata['title']) / 'OEBPS' / 'Styles' / 'styles.css', 'a')
lines = ['h2 {color: #007500; margin-bottom: 0.2em; font-size: 1.2em; font-weight: bold;}']
for line in lines:
    f.write(line + '\n')
f.close()

# get book text and images
base_url = 'https://www.cs.cmu.edu/~rgs/'
ordered_file_list = list()
r = requests.get(base_url + 'alice-table.html')
for chapter in tqdm(BeautifulSoup(r.content, 'html.parser').find('pre').find_all('a', href=True), desc='Chapter'):
    ordered_file_list.append(chapter['href'])
    r = requests.get(base_url + chapter['href'])
    f = open(Path(metadata['title']) / 'OEBPS' / 'Text' / chapter['href'], 'wb')
    f.write(r.content)
    f.close()
    for image in BeautifulSoup(r.content, 'html.parser').find_all('a', href=True):
        if image['href'].split('.')[-1] != 'html':
            r = requests.get(base_url + image['href'])
            f = open(Path(metadata['title']) / 'OEBPS' / 'Images' / image['href'], 'wb')
            f.write(r.content)
            f.close()

# create chapter files
for i in range(len(ordered_file_list)):
    f_org = open(Path(metadata['title']) / 'OEBPS' / 'Text' / ordered_file_list[i], 'r')
    f_new = open(Path(metadata['title']) / 'OEBPS' / 'Text' / 'chapter_{:04}.html'.format(i + 1), 'a')
    for line in f_org.readlines():
        if not (line.startswith('<A NAME="PREV"') or line.startswith('<P><A NAME="NEXT"')):
            if line.startswith('<A HREF='):
                f_new.write('<div><a id="{0}"></a> <img alt="image" src="../Images/{0}" /></div>'.format(line.split('"')[1]))
            elif line.startswith('<HEAD>'):
                f_new.write(line)
                f_new.write('    <link href="../Styles/styles.css" rel="stylesheet" type="text/css" />' + '\n')
            else:
                f_new.write(line)
    f_new.close()
    f_org.close
    (Path(metadata['title']) / 'OEBPS' / 'Text' / ordered_file_list[i]).unlink()

# create cover file
epub.create_coverpage_file(folder = metadata['title'], image_url = 'https://www.cs.cmu.edu/~rgs/alice01a.gif')

# create epub
epub.create_epub_file(metadata, delete_folder=True)
