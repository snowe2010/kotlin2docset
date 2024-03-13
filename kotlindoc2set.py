import dirutil
from const import *
from kotlinwebdocparser import KotlinWebDocParser
from sqliteconnection import SQLiteConnection

if __name__ == '__main__':

    # dirutil.setup_docset_directories(DOCSET_DOCUMENT_PATH)
    dirutil.copy_icon(STATIC_ASSET_ICON_PATH, DOCSET_ICON_PATH)
    dirutil.copy_plist(STATIC_ASSET_PLIST_PATH, DOCSET_PLIST_PATH)

    sqlite_connection: SQLiteConnection = SQLiteConnection(DATABASE_PATH)
    sqlite_connection.drop_sqlite_search_index()
    sqlite_connection.create_sqlite_search_index()

    web_parser: KotlinWebDocParser = KotlinWebDocParser(WEB_DOCS_URL, DOCSET_DOCUMENT_PATH, sqlite_connection)
    # web_parser.mirror_website()
    # web_parser.parse()
    # web_parser.add_custom_css()

    web_parser2: KotlinWebDocParser = KotlinWebDocParser(TEST_URL, DOCSET_TEST_DOCUMENT_PATH, sqlite_connection)
    web_parser2.mirror_website()
    web_parser2.parse()
    web_parser2.add_custom_css()

    sqlite_connection.commit_and_close()
