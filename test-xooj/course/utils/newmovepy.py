# -*- coding: utf-8 -*-
from moviepy.editor import VideoFileClip


class NewVideoFileClip(VideoFileClip):

    def close_audio(self):
        if hasattr(self, 'audio'):
            # AudioFileClip --> FFMPEG_AudioReader
            current_ffmpeg_AudioReader = self.audio.reader  # FFMPEG_AudioReader
            if hasattr(current_ffmpeg_AudioReader, 'proc') and current_ffmpeg_AudioReader.proc is not None:
                current_ffmpeg_AudioReader.proc.terminate()
                for std in [current_ffmpeg_AudioReader.proc.stdout,
                            current_ffmpeg_AudioReader.proc.stderr]:
                    std.close()
                current_ffmpeg_AudioReader.proc.wait()
                del current_ffmpeg_AudioReader.proc

    def close_all_ffmpeg(self):
        self.reader.close()
        self.close_audio()
