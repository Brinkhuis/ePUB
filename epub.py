import datetime
import os
import requests
import shutil
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm


def create_folders(info):
    """
    Create an Open Format Container (OCF).
    https://www.w3.org/AudioVideo/ebook
    """
    p = Path(info['title'])
    p.mkdir()
    for folder in ['META-INF', 'OEBPS/Images', 'OEBPS/Styles', 'OEBPS/Text']:
        (p / folder).mkdir(parents=True)


def create_mimetype(info):
    p = Path(info['title'])
    f = open(p / 'mimetype', 'w')
    f.write('application/epub+zip')
    f.close()


def create_container(info):
    p = Path(info['title'])
    f = open(p / 'META-INF/container.xml', 'w')
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">',
             '    <rootfiles>',
             '        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>',
             '    </rootfiles>',
             '</container>']
    for line in lines:
        f.write(line + '\n')
    f.close()


def create_cover(info):
    download_dir = Path('Downloads')
    p = Path(info['title'])
    os.rename(download_dir / 'cover.jpg', p / 'OEBPS/Images' / 'cover.jpg')
    f = open(p / 'OEBPS/Text/CoverPage.html', 'a')
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<html xmlns="http://www.w3.org/1999/xhtml">',
             '<head>',
             '    <link href="../Styles/styles.css" rel="stylesheet" type="text/css" />',
             '    <title>Cover Page</title>',
             '    <style type="text/css">',
             '        @page { margin:0; }',
             '    </style>',
             '</head>',
             '<body style="margin-top:0px; margin-left:0px; margin-right:0px; margin-bottom:0px; text-align:center;">',
             '    <div><a id="Cover"></a> <img alt="image" src="../Images/cover.jpg" style="height:100%; text-align:center;" /></div>',
             '</body>',
             '</html>']
    for line in lines:
        f.write(line + '\n')
    f.close()


def create_html(info, bible):
    p = Path(info['title'])

    books = bible['book'].unique()
    
    for i in tqdm(range(len(books)), desc='Creating chapters files'):
        file_name = 'chapter_{:04}.html'.format(i + 1)
        f = open(p / 'OEBPS/Text' / file_name, 'a')
        
        # write title
        lines = ['<?xml version="1.0" encoding="utf-8"?>',
                 '<html xmlns="http://www.w3.org/1999/xhtml">',
                 '<head>',
                 '    <link href="../Styles/styles.css" rel="stylesheet" type="text/css" />',
                 '    <title>{}</title>'.format(books[i]),
                 '</head>',
                 '<body>',
                 '    <h1>{}</h1>'.format(books[i])]
        for line in lines:
            f.write(line + '\n')
        
        # write chapters
        df_book = bible.loc[bible['book'] == books[i]]
        for chapter in df_book['book_chapter'].unique():
            lines = ['    <h3>{}</h3>'.format(chapter),
                     '    <p>']
            for line in lines:
                f.write(line + '\n')
            
            # write verses
            df_chapter = df_book.loc[df_book['book_chapter'] == chapter]
            for _, row in df_chapter.iterrows():
                lines = ['    <span class="verseNum">{}</span> {}'.format(row['verse'], row['text'])]
                for line in lines:
                    f.write(line + '\n')
            f.write('    </p>' + '\n')
        
        # closing html tags
        lines = ['</body>',
                 '</html>']
        for line in lines:
            f.write(line + '\n')  
        
        # close file
        f.close()


def create_content(info):
    p = Path(info['title'])
    f = open(p / 'OEBPS/content.opf', 'a')
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">',
             '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:opf="http://www.idpf.org/2007/opf" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
             '    <dc:identifier id="BookId">{}</dc:identifier>'.format(info['ISBN']),
             '    <dc:title>{}</dc:title>'.format(info['title']),
             '    <dc:creator opf:role="aut">{}</dc:creator>'.format(info['creator']),
             '    <dc:language>{}</dc:language>'.format(info['language']),
             '    <dc:subject>{}</dc:subject>'.format(info['subject']),
             '    <dc:identifier opf:scheme="ISBN">{}</dc:identifier>'.format(info['ISBN']),
             '    <dc:date opf:event="modification">{}</dc:date>'.format(datetime.datetime.now().strftime("%Y-%m-%d")),
             '</metadata>',
             '<manifest>',
             '    <item href="toc.ncx" id="toc_ncx" media-type="application/x-dtbncx+xml" />',
             '    <item href="Text/CoverPage.html" id="CoverPage_html" media-type="application/xhtml+xml" />',
             '    <item href="Styles/styles.css" id="styles_css" media-type="text/css" />']
    for line in lines:
        f.write(line + '\n')
    
    ordered_titles = list()
    
    chapter_files = [f.name for f in list((p / 'OEBPS/Text').glob('chapter_*.html'))]
    chapter_files.sort()
    for chapter_file in chapter_files:
        file_path = p / 'OEBPS/Text' / chapter_file
        with open(file_path, 'r') as file:
            data = file.read()
        soup = BeautifulSoup(data, 'html.parser')
        ordered_titles.append(soup.find('title').text)
        
    for index in range(len(ordered_titles)):
        section_number = '{:04}'.format(index + 1)
        file_name = 'chapter_{}.html'.format(section_number)
        lines = ['    <item href="Text/{}" id="section-{}_html" media-type="application/xhtml+xml" />'.format(file_name, section_number)]
        for line in lines:
            f.write(line + '\n')
    
    images = [f.name for f in list((p / 'OEBPS' / 'Images').glob('*.jpg'))]
    
    for image in images:
        lines = ['    <item href="Images/{}" id="{}" media-type="image/jpeg" />'.format(image, image.replace('.', '_'))]
        for line in lines:
            f.write(line + '\n')
    
    lines = ['</manifest>',
             '<spine toc="toc_ncx">',
             '    <itemref idref="CoverPage_html" />']
    for line in lines:
        f.write(line + '\n')
    
    for index in range(len(ordered_titles)):
        section_number = '{:04}'.format(index + 1)
        lines = ['    <itemref idref="section-{}_html" />'.format(section_number)]
        
        for line in lines:
            f.write(line + '\n')
    
    lines = ['</spine>',
             '<guide>',
             '    <reference href="Text/CoverPage.html" title="Cover Page" type="cover" />',
             '</guide>',
             '</package>']
    for line in lines:
        f.write(line + '\n')
    
    f.close()


def create_toc(info):
    p = Path(info['title'])
    f = open(p / 'OEBPS' / 'toc.ncx', 'a')
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
             '<head>',
             '    <meta name="dtb:uid" content="{}" />'.format(info['ISBN']),
             '    <meta name="dtb:depth" content="1" />',
             '    <meta name="dtb:totalPageCount" content="0" />',
             '    <meta name="dtb:maxPageNumber" content="0" />',
             '</head>',
             '<docTitle>',
             '    <text>{}</text>'.format(info['title']),
             '</docTitle>',
             '<navMap>']
    for line in lines:
        f.write(line + '\n')
    
    ordered_titles = list()
    chapter_files = [f.name for f in list((p / 'OEBPS/Text').glob('chapter_*.html'))]
    chapter_files.sort()
    for chapter_file in chapter_files:
        file_path = p / 'OEBPS/Text' / chapter_file
        with open(file_path, 'r') as file:
            data = file.read()
        soup = BeautifulSoup(data, 'html.parser')
        ordered_titles.append(soup.find('title').text)
    
    for index in range(len(ordered_titles)):
        text = ordered_titles[index]
        number = index + 1
        section_number = '{:04}'.format(number)
        file_name = 'chapter_{}.html'.format(section_number)
        lines = ['    <navPoint id="navPoint-{0}" playOrder="{0}">'.format(number),
                 '        <navLabel>',
                 '            <text>{}</text>'.format(text),
                 '        </navLabel>',
                 '        <content src="Text/{}" />'.format(file_name),
                 '    </navPoint>']
        for line in lines:
             f.write(line + '\n')
            
    lines = ['</navMap>',
             '</ncx>']
    for line in lines:
        f.write(line + '\n')
    f.close()


def create_css(info):
    p = Path(info['title'])
    f = open(p / 'OEBPS' / 'Styles' / 'styles.css', 'a')
    lines = ['h1 {color: %s; margin-bottom: 0.2em; font-size: 2.0em; font-weight: bold;}'%(info['color']),
             'h3 {color: %s; margin-bottom: 0.2em; font-size: 1.2em; font-weight: bold;}'%(info['color']),
             '.verseNum{color: %s; font-size: smaller; font-weight: bold; }'%(info['color'])]
    for line in lines:
        f.write(line + '\n')
    f.close()


def create_epub(info):
    p = Path(info['title'])
    book_dir = Path('Books')
    book_dir.mkdir(exist_ok=True)
    file_name = info['title'].replace(' ', '_').lower()
    shutil.make_archive(book_dir / file_name, 'zip', p)
    source = book_dir / f'{file_name}.zip'
    target = book_dir / f'{file_name}.epub'
    source.rename(target)


def delete_dir(info):
    p = Path(info['title'])
    shutil.rmtree(p)











    

def create_coverpage_file(folder, image_url):
    """
    For now, the image should be in JPG format
    """
    
    p = Path(folder)
    
    # create cover page
    f = open(p / 'OEBPS/Text/CoverPage.html', 'a')
    
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<html xmlns="http://www.w3.org/1999/xhtml">',
             '<head>',
             '    <link href="../Styles/styles.css" rel="stylesheet" type="text/css" />',
             '    <title>Cover Page</title>',
             '    <style type="text/css">',
             '        @page { margin:0; }',
             '    </style>',
             '</head>',
             '<body style="margin-top:0px; margin-left:0px; margin-right:0px; margin-bottom:0px; text-align:center;">',
             '    <div><a id="Cover"></a> <img alt="image" src="../Images/cover.jpg" style="height:100%; text-align:center;" /></div>',
             '</body>',
             '</html>']
    
    for line in lines:
        f.write(line + '\n')
    
    f.close()
    
    # download cover image
    r = requests.get(image_url, allow_redirects=True)
    open(p / 'OEBPS/Images/cover.jpg', 'wb').write(r.content)


def create_epub_file(metadata, delete_folder=False):
    
    p = Path(metadata['title'])
    
    # create mimetype
    f = open(p / 'mimetype', 'w')
    f.write('application/epub+zip')
    f.close()
    
    
    # create container.xml
    f = open(p / 'META-INF/container.xml', 'w')
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">',
             '    <rootfiles>',
             '        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>',
             '    </rootfiles>',
             '</container>']
    for line in lines:
        f.write(line + '\n')
    f.close()
    
    
    # create content.opf 
    f = open(p / 'OEBPS/content.opf', 'a')
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">',
             '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:opf="http://www.idpf.org/2007/opf" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
             '    <dc:identifier id="BookId">{}</dc:identifier>'.format(metadata['identifier_id']),
             '    <dc:title>{}</dc:title>'.format(metadata['title']),
             '    <dc:creator opf:role="aut">{}</dc:creator>'.format(metadata['creator']),
             '    <dc:language>{}</dc:language>'.format(metadata['language']),
             '    <dc:subject>{}</dc:subject>'.format(metadata['subject']),
             '    <dc:identifier opf:scheme="ISBN">{}</dc:identifier>'.format(metadata['identifier_opf']),
             '    <dc:date opf:event="modification">{}</dc:date>'.format(datetime.datetime.now().strftime("%Y-%m-%d")),
             '</metadata>',
             '<manifest>',
             '    <item href="toc.ncx" id="toc_ncx" media-type="application/x-dtbncx+xml" />',
             '    <item href="Text/CoverPage.html" id="CoverPage_html" media-type="application/xhtml+xml" />',
             '    <item href="Styles/styles.css" id="styles_css" media-type="text/css" />']
    for line in lines:
        f.write(line + '\n')
    
    ordered_titles = list()
    
    chapter_files = [f.name for f in list((p / 'OEBPS/Text').glob('chapter_*.html'))]
    chapter_files.sort()

    for chapter_file in chapter_files:
        file_path = p / 'OEBPS/Text' / chapter_file
        with open(file_path, 'r') as file:
            data = file.read()
        soup = BeautifulSoup(data, 'html.parser')
        ordered_titles.append(soup.find('title').text)
        
    for index in range(len(ordered_titles)):
        section_number = '{:04}'.format(index + 1)
        file_name = 'chapter_{}.html'.format(section_number)
        lines = ['    <item href="Text/{}" id="section-{}_html" media-type="application/xhtml+xml" />'.format(file_name, section_number)]
        for line in lines:
            f.write(line + '\n')
    
    images = [f.name for f in list((p / 'OEBPS' / 'Images').glob('*.jpg'))]
    
    for image in images:
        lines = ['    <item href="Images/{}" id="{}" media-type="image/jpeg" />'.format(image, image.replace('.', '_'))]

        for line in lines:
            f.write(line + '\n')
    
    lines = ['</manifest>',
             '<spine toc="toc_ncx">',
             '    <itemref idref="CoverPage_html" />']
    for line in lines:
        f.write(line + '\n')
    
    for index in range(len(ordered_titles)):
        section_number = '{:04}'.format(index + 1)
        lines = ['    <itemref idref="section-{}_html" />'.format(section_number)]
        
        for line in lines:
            f.write(line + '\n')
    
    lines = ['</spine>',
             '<guide>',
             '    <reference href="Text/CoverPage.html" title="Cover Page" type="cover" />',
             '</guide>',
             '</package>']
    for line in lines:
        f.write(line + '\n')
    
    f.close()
    
    
    # create toc.ncx
    f = open(p / 'OEBPS' / 'toc.ncx', 'a')
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
             '<head>',
             '    <meta name="dtb:uid" content="{}" />'.format(metadata['identifier_id']),
             '    <meta name="dtb:depth" content="1" />',
             '    <meta name="dtb:totalPageCount" content="0" />',
             '    <meta name="dtb:maxPageNumber" content="0" />',
             '</head>',
             '<docTitle>',
             '    <text>{}</text>'.format(metadata['title']),
             '</docTitle>',
             '<navMap>']
    for line in lines:
        f.write(line + '\n')
    
    ordered_titles = list()
    
    chapter_files = [f.name for f in list((p / 'OEBPS/Text').glob('chapter_*.html'))]
    chapter_files.sort()
    
    for chapter_file in chapter_files:
        file_path = p / 'OEBPS/Text' / chapter_file
        with open(file_path, 'r') as file:
            data = file.read()
        soup = BeautifulSoup(data, 'html.parser')
        ordered_titles.append(soup.find('title').text)
    
    for index in range(len(ordered_titles)):
        text = ordered_titles[index]
        number = index + 1
        section_number = '{:04}'.format(number)
        file_name = 'chapter_{}.html'.format(section_number)
        lines = ['    <navPoint id="navPoint-{0}" playOrder="{0}">'.format(number),
                 '        <navLabel>',
                 '            <text>{}</text>'.format(text),
                 '        </navLabel>',
                 '        <content src="Text/{}" />'.format(file_name),
                 '    </navPoint>']

        for line in lines:
            f.write(line + '\n')
            
    lines = ['</navMap>',
             '</ncx>']

    for line in lines:
        f.write(line + '\n')
        
    f.close()
    
    
    # create epub file
    b = Path('Books')
    b.mkdir(exist_ok=True)
    file_name = metadata['title'].replace(' ', '_').lower()
    shutil.make_archive(b / file_name, 'zip', p)
    source = b / f'{file_name}.zip'
    target = b / f'{file_name}.epub'
    source.rename(target)
    if delete_folder:
        shutil.rmtree(p)
