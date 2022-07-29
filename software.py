import platform
def create_software():
    system=platform.uname()[0]
    if system=="Windows":
        return Windows()
class Windows():
    def __init__(self):
        self.java_path=[r"C:\Program Files\Java",r"C:\Program Files (x86)\Java",".","Java"]
    def get_system_name(self):
        return "windows"
    def get_system_arch(self):
        if platform.architecture()[0]=="32bit":
            return "x86"
        else:
            return "x64"