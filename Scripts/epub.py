import requests
import os
import shutil
import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path

def set_book_metadata(identifier_id, title, creator='', language='', subject='', identifier_opf=''):
    """
    identifier_id: Book ISBN (formatted with dashes, like xxx-xx-xxx-xxxx-x)
    title: Book Title
    creator: Book Author
    language: Book Language
    subject: Book Subject
    identifier opf: Book ISBN (no dashes, like xxxxxxxxxxxxx)
    """
    
    metadata = dict()
    
    metadata['identifier_id'] = identifier_id
    metadata['title'] = title
    metadata['creator'] = creator
    metadata['language'] = language
    metadata['subject'] = subject
    metadata['identifier_opf'] = identifier_opf
    
    return metadata


def create_ebook_folder(folder):
    """
    Create an Open Format Container (OCF).
    https://www.w3.org/AudioVideo/ebook
    """
    
    root = Path(folder)
    
    # create folders
    Path.mkdir(root)

    for folder in ['META-INF', 'OEBPS']:
        Path.mkdir(root / folder)
    
    for subfolder in ['Images', 'Styles', 'Text']:
        Path.mkdir(root / 'OEBPS' / subfolder)


def create_coverpage_file(folder, image_url):
    """
    For now, the image should be in JPG
    """
    
    # create cover page
    root = Path(folder)
    f = open(root / 'OEBPS/Text' / 'CoverPage.html', 'a')
    
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
    open(root / 'OEBPS/Images' / 'cover.jpg', 'wb').write(r.content)




def create_epub_file(metadata, delete_folder=False):
    
    root = Path(metadata['title'])
    
    # create mimetype
    
    f = open(root / 'mimetype', 'w')
    f.write('application/epub+zip')
    f.close()
    
    
    # create container.xml
    
    f = open(root / 'META-INF' / 'container.xml', 'w')
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
    
    f = open(root / 'OEBPS' / 'content.opf', 'a')
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
    
    chapter_files = [file for file in os.listdir(root / 'OEBPS/Text') if file.startswith('chapter_')]
    chapter_files.sort()

    for chapter_file in chapter_files:
        file_path = root / 'OEBPS/Text' / chapter_file
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
    
    images = [file.name for file in list((root / 'OEBPS' / 'Images').glob('**/*.jpg')) if file.is_file()]
    
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
    
    f = open(root / 'OEBPS' / 'toc.ncx', 'a')
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
    
    chapter_files = [file for file in os.listdir(root / 'OEBPS/Text') if file.startswith('chapter_')]
    chapter_files.sort()
    
    for chapter_file in chapter_files:
        file_path = root / 'OEBPS/Text' / chapter_file
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
    file_name = metadata['title'].replace(' ', '_').lower()
    shutil.make_archive(file_name, 'zip', './{}'.format(root))
    os.rename(file_name + '.zip', file_name + '.epub')
    if not os.path.isdir('Books'):
        os.mkdir('Books')
    shutil.move(file_name + '.epub', 'Books')
    
    if delete_folder:
        shutil.rmtree(root)
