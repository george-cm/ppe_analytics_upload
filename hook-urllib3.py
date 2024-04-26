"""urllib3 hook for PyInstaller"""  # pylint: disable=invalid-name

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("urllib3")
