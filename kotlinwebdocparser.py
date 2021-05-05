import os
import re
from subprocess import call
from bs4 import BeautifulSoup

from sqliteconnection import SQLiteConnection


class KotlinWebDocParser:
    def __init__(self, url: str, local_path: str, database: SQLiteConnection):
        self.url = url
        self.local_path = local_path
        self.database = database

    def mirror_website(self):
        call([
            'wget',
            '--mirror',
            '--convert-links',
            '--adjust-extension',
            '--page-requisites',
            '--no-parent',
            '--no-host-directories',
            '--directory-prefix', self.local_path,
            '--quiet',
            '--show-progress',
            self.url
        ])

    def parse(self):
        for dirpath, _, files in os.walk(self.local_path):
            for page in files:
                if page.endswith('.html'):
                    self.parse_file(os.path.join(dirpath, page))

    def parse_file(self, file_path: str):
        with open(file_path) as page:
            soup = BeautifulSoup(page.read(), features='html.parser')
            for node in soup.find_all('div', attrs={'class': ['node-page-main', 'overload-group']}):
                signature = node.find('div', attrs={'class': 'signature'})
                if signature:
                    code_type = self.parse_code_type(signature.text.strip())
                    name_dom = soup.find('div', attrs={'class': 'api-docs-breadcrumbs'})
                    name = '.'.join(map(lambda string: string.strip(), name_dom.text.split('/')[2::]))
                    path = file_path.replace('kotlin.docset/Contents/Resources/Documents/', '')
                    if code_type is not None and name:
                        self.database.insert_into_index(name, code_type, path)
                        print('%s -> %s -> %s' % (name, code_type, path))

    def parse_code_type(self, code: str) -> str:
        tokens = list(filter(
            lambda token: token not in [
                'public',
                'private',
                'protected',
                'open',
                'const',
                'abstract',
                'suspend',
                'operator'
            ],
            code.split()
        ))
        if 'class' in tokens or 'typealias' in tokens:
            return 'Class'
        elif 'interface' in tokens:
            return 'Interface'
        elif 'fun' in tokens:
            return 'Function'
        elif 'val' in tokens or 'var' in tokens:
            return 'Property'
        elif 'object' in tokens:
            return 'Object'
        elif '<init>' in tokens or '<init>' in tokens[0]:
            return 'Constructor'
        elif re.match(r"[a-zA-Z0-9]*\(.*\)", code) or re.match(r"[a-zA-Z0-9]*\(.*\)", tokens[0]):
            return 'Constructor'
        elif re.match(r"[A-Z0-9\_]+", code):
            return 'Enum'
