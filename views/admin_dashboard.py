# views/admin_dashboard.py

from views.base_dashboard import BaseDashboard
from views.pages.home          import HomePage
from views.pages.categories    import CategoryPage
from views.pages.all_books     import AllBooksPage
from views.pages.borrow_book   import BorrowBookPage
from views.pages.return_book   import ReturnBookPage
from views.pages.users         import ManageUsersPage
from views.pages.download_book import DownloadBookPage

class AdminDashboard(BaseDashboard):
    def __init__(self, user):
        # 1) Define all seven menu items
        menu_items = [
            ("Home",          "resources/icons/home.png",       "resources/icons/home_white.png"),
            ("Category",      "resources/icons/categories.png", "resources/icons/categories_white.png"),
            ("All Books",     "resources/icons/book.png",      "resources/icons/book_white.png"),
            ("Borrow Book",   "resources/icons/borrow.png",     "resources/icons/borrow_white.png"),
            ("Return Book",   "resources/icons/return.png",     "resources/icons/return_white.png"),
            ("User",          "resources/icons/user.png",       "resources/icons/user_white.png"),
            ("Download Book", "resources/icons/download.png",   "resources/icons/download_white.png"),
        ]

        # 2) Instantiate each page, passing `user` where required
        pages = [
            HomePage(),
            CategoryPage(),
            AllBooksPage(),
            BorrowBookPage(current_user=user),   # now passes the user
            ReturnBookPage(current_user=user),   # also passes the user
            ManageUsersPage(),
            DownloadBookPage()
        ]

        # 3) Call the BaseDashboard constructor
        super().__init__(
            user_name  = user.username,
            menu_items = menu_items,
            pages      = pages
        )
