import os
import re
import glob
from subprocess import call
from bs4 import BeautifulSoup

from sqliteconnection import SQLiteConnection

mapping_dict = {
    "Annotations": "Annotation",
    # "Companion Object Extension Properties": "Attribute",
    # "TODO": "Binding",
    # "TODO": "Builtin",
    # "TODO": "Callback",
    # "TODO": "Category",
    # "TODO": "Class",
    # "TODO": "Command",
    # "TODO": "Component",
    "Companion Object Properties": "Constant",
    "Constructors": "Constructor",
    # "TODO": "Define",
    # "TODO": "Delegate",
    # "TODO": "Diagram",
    # "TODO": "Directive",
    # "TODO": "Element",
    # "TODO": "Entry",
    "Enum Values": "Enum",
    # "TODO": "Environment",
    # "TODO": "Error",
    # "TODO": "Event",
    "Exceptions": "Exception",
    "Extensions for External Classes": "Extension",
    "Extension Functions": "Extension",
    "Companion Object Extension Properties": "Field",
    "Extension Properties": "Field",
    "Extensions for java.nio.file.Path": "Field",
    "Extensions for java.net.URI": "Field",
    "Extensions for java.math.BigDecimal": "Field",
    "Extensions for java.math.BigInteger": "Field",
    "Extensions for java.util.stream.DoubleStream": "Field",
    "Extensions for kotlin.sequences.Sequence": "Field",
    "Extensions for java.util.stream.IntStream": "Field",
    "Extensions for java.util.stream.LongStream": "Field",
    "Extensions for java.util.stream.Stream": "Field",
    "Extensions for java.util.Optional": "Field",
    "Extensions for java.util.concurrent.ConcurrentMap": "Field",
    "Extensions for java.util.Enumeration": "Field",
    "Extensions for java.util.regex.Pattern": "Field",
    "Extensions for java.io.OutputStream": "Field",
    "Extensions for java.io.InputStream": "Field",
    "Extensions for java.lang.reflect.Method": "Field",
    "Extensions for java.lang.reflect.Constructor": "Field",
    "Extensions for java.lang.reflect.Field": "Field",
    "Extensions for java.lang.concurrent.ConcurrentMap": "Field",
    "Extensions for java.lang.StringBuilder": "Field",
    "Extensions for java.lang.Appendable": "Field",
    "Extensions for java.lang.Class": "Field",
    "Extensions for java.lang.Field": "Field",
    "Extensions for java.lang.Method": "Field",
    "Extensions for java.lang.ThreadLocal": "Field",
    "Extensions for java.lang.Enum.getDeclaringClass": "Field",
    "Extensions for java.lang.reflect.AnnotatedElement.getAnnotationsByType": "Field",
    "Extensions for java.lang.annotation.Repeatable": "Field",
    "Extensions for java.lang.Class.getName": "Field",
    "Extensions for java.reflect.Constructor": "Field",
    "Extensions for java.reflect.Field": "Field",
    "Extensions for java.reflect.Method": "Field",
    "Extensions for java.lang.reflect.AccessibleObject": "Field",
    "Extensions for java.util.Random": "Field",
    "Extensions for java.util.concurrent.locks.Lock": "Field",
    "Extensions for java.util.Timer": "Field",
    "Extensions for java.util.concurrent.locks.ReentrantReadWriteLock": "Field",
    "Extensions for java.time.Duration": "Field",
    # "TODO": "File",
    # "TODO": "Filter",
    # "TODO": "Framework",
    "Functions": "Function",
    "Inherited Functions": "Function",
    # "TODO": "Global",
    # "TODO": "Guide",
    # "TODO": "Hook",
    # "TODO": "Instance",
    # "TODO": "Instruction",
    # "TODO": "Interface",
    # "TODO": "Keyword",
    # "TODO": "Library",
    # "TODO": "Literal",
    # "TODO": "Macro",
    "Companion Object Functions": "Method",
    "Inherited Properties": "Mixin",
    # "TODO": "Modifier",
    "Companion Object Extension Functions": "Module",
    # "TODO": "Namespace",
    # "TODO": "Notation",
    # "TODO": "Object",
    # "TODO": "Operator",
    # "TODO": "Option",
    "Packages": "Package",
    # "TODO": "Parameter",
    # "TODO": "Plugin",
    # "TODO": "Procedure",
    "Properties": "Property",
    # "TODO": "Protocol",
    "Inheritors": "Provider",
    # "TODO": "Provisioner",
    # "TODO": "Query",
    # "TODO": "Record",
    # "TODO": "Resource",
    # "TODO": "Sample",
    # "TODO": "Section",
    # "TODO": "Service",
    # "TODO": "Setting",
    # "TODO": "Shortcut",
    # "TODO": "Statement",
    # "TODO": "Struct",
    # "TODO": "Style",
    # "TODO": "Subroutine",
    # "TODO": "Tag",
    # "TODO": "Test",
    # "TODO": "Trait",
    "Types": "Type",
    # "TODO": "Union",
    # "TODO": "Value",
    # "TODO": "Variable",
    # "TODO": "Word"
}


def get_custom_css() -> str:
    return """
    .docs-nav-controls > a {
      display: none;
    }
    .global-layout>div>header{
      display: none;
    }
    .scroll-button-back{
      display: none;
    }
    footer {
      display: none;
    }
    """


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
                # print("page => " + page)
                if page.endswith('.html'):
                    self.parse_file(os.path.join(dirpath, page))

    def parse_file(self, file_path: str):
        # print("parsing file " + file_path)
        with open(file_path) as page:
            soup = BeautifulSoup(page.read(), features='html.parser')

            self.add_toc(soup)

            self.remove_header(soup)

            for node in soup.find_all('div', attrs={'class': ['node-page-main', 'overload-group']}):
                signature = node.find('div', attrs={'class': 'signature'})
                if signature:
                    code_type = self.parse_code_type(signature.text.strip())
                    name_dom = soup.find('div', attrs={'class': 'api-docs-breadcrumbs'})
                    name = '.'.join(map(lambda string: string.strip(), name_dom.text.split('/')[2::]))
                    path = file_path.replace('kotlin.docset/Contents/Resources/Documents/', '')
                    if code_type is not None and name:
                        self.database.insert_into_index(name, code_type, path)
                        # print('%s -> %s -> %s' % (name, code_type, path))

        # Now, overwrite the original file with the modified soup
        with open(file_path, 'w') as file:
            file.write(str(soup.prettify()))

    def add_toc(self, soup):
        sections = soup.find_all('h3')
        for section in sections:
            docset_links = section.find_all("a")
            for docset_link in docset_links:
                docset_link.decompose()
            section_name = section.text.strip()
            # print("Found section with text {}".format(section_name))
            new_tag = soup.new_tag("a",
                                   attrs={'class': 'dashAnchor', 'name': f"//apple_ref/cpp/Section/{section_name}"})
            section.append(new_tag)

            container_with_things = section.find_next_sibling()
            container_with_things_headers = container_with_things.find_all('h4')
            for element_header in container_with_things_headers:
                header_text = element_header.find('a').text.strip()
                print(header_text)
                if section_name.startswith("Extensions for java"):
                    mapped_section = "Field"
                else:
                    mapped_section = mapping_dict[section_name]
                # print("mapping {} to {}".format(header_text, mapped_section))
                old_elements = element_header.find_all("a", attrs={'class': 'dashAnchor'})
                for old_element in old_elements:
                    old_element.decompose()
                new_tag = soup.new_tag("a", attrs={'class': 'dashAnchor',
                                                   'name': f"//apple_ref/cpp/{mapped_section}/{header_text}"})

                element_header.append(new_tag)

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

    def add_custom_css(self):
        """
        Add custom css to the custom.css file. The only issue is that the common.css file is that the name can be
        randomized at the end. So it can be named something like 'common.css?&v=be6472fafff6ae90f359922e40596cbb.css'

        This function searches for that file, then adds the custom css declared at the top of this file.
        :return:
        """
        css = get_custom_css()

        # add to the common.css file, but it can have a random string in the middle like common.css?v=xxxxxx.css
        files = glob.glob(os.path.join(self.local_path, '_assets/common.css*'))

        for file_path in files:
            print("Adding custom css file: {}".format(file_path))
            with open(file_path, 'r') as file:
                # print("doesn't have content")
                content = file.read()
            if css not in content:
                # print("Adding custom css")
                with open(file_path, 'a') as file:
                    file.write(css)

    def remove_header(self, soup):
        header = soup.find('header')
        header.decompose()
