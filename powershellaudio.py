from subprocess import Popen
from os.path import exists


class WaveObject:
    """ Quick hack class to use powershell to play a wav """

    def __init__(self, file_path):
            if not exists(file_path):
                raise IOError("No such file")
            self.audio_file = file_path

    @staticmethod
    def from_wave_file(file_path):
        """ Just to have a similar API as simpleaudio """
        return WaveObject(file_path)

    def play(self):
        Popen(["powershell", "-c", r'(New-Object Media.SoundPlayer "' + \
                self.audio_file+r'").PlaySync();'])
