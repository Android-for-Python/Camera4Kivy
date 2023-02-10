__all__ = ('CameraOpenCV')

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, Rotate, Fbo
import cv2    
from . import CameraBase

class CameraOpenCV(CameraBase):

    def __init__(self, **kwargs):
        self._device = None
        self._update_ev = None
        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        self._format = 'bgr'
        if platform == 'win':
            self._index = self._index + cv2.CAP_DSHOW
        self._device = cv2.VideoCapture(self._index)
        self._device.set(cv2.CAP_PROP_FRAME_WIDTH,  self._resolution[0])
        self._device.set(cv2.CAP_PROP_FRAME_HEIGHT, self._resolution[1])
        ret, frame = self._device.read()
        self._resolution = (int(frame.shape[1]), int(frame.shape[0]))
        self.fps = self._device.get(cv2.CAP_PROP_FPS)
        if self.fps == 0 or self.fps == 1:
            self.fps = 1.0 / 30
        elif self.fps > 1:
            self.fps = 1.0 / self.fps
        self.crop = self._context.crop_for_aspect_orientation(*self._resolution)
        self.stopped = True

    def update(self, dt):
        if self.stopped:
            return
        if self._texture is None:
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self._context.on_load()
        try:
            ret, frame = self._device.read()
            if ret:
                self._buffer = frame.reshape(-1)
                self._copy_to_gpu()
                if self.photo_capture:
                    self.photo_capture = False
                    cropped = frame[self.crop[1]: self.crop[1]+self.crop[3],
                                    self.crop[0]: self.crop[0]+self.crop[2], :]
                    cv2.imwrite(self.photo_path, cropped)
                    if self.photo_callback:
                        self.photo_callback(self.photo_path)
                if self.video_capture:
                    cropped = frame[self.crop[1]: self.crop[1]+self.crop[3],
                                    self.crop[0]: self.crop[0]+self.crop[2], :]
                    self.video_stream.write(cropped) 

        except Exception as e:
            Logger.exception('OpenCV: Couldn\'t get image from Camera')

    def start(self):
        self.stopped = False
        self.photo_capture = False
        self.video_capture = False
        if self._update_ev is not None:
            self._update_ev.cancel()
        self._update_ev = Clock.schedule_interval(self.update, 1/30) 

    def stop(self):
        self.stopped = True
        self._device = None
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None

    def photo(self, path, callback):
        self.photo_capture = True
        self.photo_path = path
        self.photo_callback = callback

    def video_start(self, path, callback):
        self.video_capture = True
        self.video_path = path
        self.video_callback = callback
        size = (self.crop[2], self.crop[3])
        rate = Clock.get_fps()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_stream = cv2.VideoWriter(path, fourcc, rate, size)
        
    def video_stop(self):
        self.video_capture = False
        self.video_stream.release()

