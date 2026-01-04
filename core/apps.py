from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    
    def ready(self):
        """Import signals when app is ready"""
        import core.signals  # noqa
        # Import project admin to ensure UnfoldAdmin is used for User/Group
        try:
            import xtractme.admin  # noqa
        except ImportError:
            pass