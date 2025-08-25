# views/student_dashboard.py

from views.base_dashboard import BaseDashboard
from views.pages.home_student import StudentHomePage
from views.pages.library_student import LibraryPage  # <-- New library page

class StudentDashboard(BaseDashboard):
    def __init__(self, user):
        self.current_user = user

        # Sidebar with only Home and Library
        menu_items = [
            ("Home", "resources/icons/home.png", "resources/icons/home_white.png"),
            ("Library", "resources/icons/books.png", "resources/icons/books_white.png"),
        ]

        # Pages
        pages = [
            StudentHomePage(current_user=user),
            LibraryPage(current_user=user),  # New page with filter, cards
        ]

        super().__init__(
            user_name=user.username,
            menu_items=menu_items,
            pages=pages
        )
