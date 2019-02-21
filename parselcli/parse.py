from click.parser import OptionParser
import shlex


class ToggleInputOptionParser(OptionParser):
    def add_option(self, dest, action=None, nargs=1, const=None, obj=None):
        """added support for +- flags"""
        if dest.startswith('+-') or dest.startswith('-+'):
            dest = '+' + dest.strip('+-')
            super().add_option([dest], dest, action, nargs, const, obj)
            dest = '-' + dest.strip('+-')
            super().add_option([dest], dest, action, nargs, const, obj)
        else:
            super().add_option([dest], dest, action, nargs, const, obj)


