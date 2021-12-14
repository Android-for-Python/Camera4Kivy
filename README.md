Camera4Kivy
===========

*Yet Another Kivy Camera*

This document has seven sections [Overview](https://github.com/Android-for-Python/camera4kivy#overview), [Install](https://github.com/Android-for-Python/camera4kivy#install), [Examples](https://github.com/Android-for-Python/camera4kivy#examples), [Preview Widget](https://github.com/Android-for-Python/camera4kivy#preview-widget), [Image Analysis](https://github.com/Android-for-Python/camera4kivy#image-analysis), [Camera Behavior](https://github.com/Android-for-Python/camera4kivy#camera-behavior), and [Known Issues](https://github.com/Android-for-Python/camera4kivy#known-issues).

## Overview

Available on all the usual platforms.

```python
from camera4kivy import Preview
```

Camera4Kivy consists of a `Preview` widget with an api to connect it to the physical camera unit. The Preview has optional layout properties, for example:

In .kv
```
    Preview:
        id: preview
	aspect_ratio: '16:9'
```

In Python
```
    self.preview = Preview(aspect_ratio = '16:9')
```

To connect the camera unit to the Preview call the preview's `connect_camera()` method. The connect_camera method has optional parameters, for example enabling the image analysis api. 

```python
    self.preview.connect_camera(enable_analyze_pixels = True)
```

Well behaved apps disconnect the camera when it is no longer in use. It is important to be well behaved.

```python
    self.preview.disconnect_camera()
```

To take a photo:

```python
   self.preview.capture_photo()
```

The captured file location may be specified and is also reported in a callback. A data analysis api allows per frame analysis and preview annotation or preview image replacement.

On Android a pinch/spread gesture controls zoom, and a tap overrides any automatic focus and metering (if available). Some connect_camera options are platform specific.

## Install

First install a camera provider if necessary. Then install Camera4Kivy.

### Install a Camera Provider

Camera4Kivy depends on a 'camera provider' to access the OS camera api. On most platforms this uses the same provider as Kivy, with modified defaults.

| Platform    | Provider      | Requires       |
|-------------|---------------|----------------|
| Windows     | [OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv)                      |
|             | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)                      |
| Macos       | [AVFoundation](https://github.com/Android-for-Python/camera4kivy#avfoundation)| OSX >= 10.7    |   
| Linux       | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)                      |
|             | [OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv)                      |
| Rasberry    | [Picamera](https://github.com/Android-for-Python/camera4kivy#picamera)    | <= Buster      |
|             | [Picamera2](https://github.com/Android-for-Python/camera4kivy#pycamera2)   | >= Bullseye    |
|             | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)                      |
|             |[OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv)                      |
| Android     | [CameraX](https://github.com/Android-for-Python/camera4kivy#android-camerax_provider)                      |]| Android >= 5.0 |
| iOS         | [AVFoundation](https://github.com/Android-for-Python/camera4kivy#avfoundation)                      |

Some camera provider specific behavior should be expected. For example a switch to a camera that does not exist will be ignored on MacOS and Rasberry Pi, but generate a screen message with OpenCV or GStreamer. Camera resolution defaults to the maximum available sensor resolution, except on Raspberry Pi where the default is (1024, 768).

#### Android camerax_provider

On the Buildozer host:

`cd <project directory>`

`git clone https://github.com/Android-for-Python/camerax_provider.git`

`rm -rf camerax_provider/.git`

#### OpenCV

`pip3 install opencv-python`

#### GStreamer

Depends on the Linux flavor, but commonly:

`sudo apt-get install gstreamer-1.0`

`sudo apt-get install gstreamer1.0-dev`

#### Picamera
Pre-installed

#### Picamera2
[Not available](https://www.raspberrypi.com/news/bullseye-camera-system/)

#### AVFoundation
Pre-installed

### Install Camera4Kivy on Desktop

`pip3 install camera4kivy`

### Install Camera4Kivy on Android

Camera4Kivy depends on the 'master' version of Buildozer. Currently `1.2.0.dev0`

`pip3 install git+https://github.com/kivy/buildozer.git`

#### buildozer.spec:

`requirements = python3, kivy, camera4kivy`

`android.permissions =  CAMERA, RECORD_AUDIO`    

`android.api = 30`   (or higher, min 29)

These two enable the camera provider:

`p4a.local_recipes =  ./camerax_provider/recipes`  

`p4a.hook = ./camerax_provider/gradle_options.py`

#### Run Time Permissions

The following run time permissions must be in be requested in the app. As usual request these in build() or after on_start(). See the examples.

Always required: `CAMERA`

Required to record video with audio: `RECORD_AUDIO`

Required when capturing photo, screenshot, or video and saving to shared storage, and only on devices running api_version < 29: `WRITE_EXTERNAL_STORAGE`

## Examples

A prerequisite is a working camera is installed. Test this with the platform's camera app before proceeding. All examples use the platform specific camera provider, and assume the typical default camera_id of '0'. If you find the example does not connect to a camera review your camera provider choice.

### Tested Examples and Platforms 

The Photo example illustrates basic camera usage, try this first. The remaining examples illustrate image analysis using various packages. Not tested : iOS, set your expectations accordingly.

On Android `orientation = all` is available, on the desktop you can change the window size to simulate orientation and rotating a mobile device. 

| Example | Windows | Macos | Linux | Android | iOS | Coral |
|---------|---------|-------|-------|---------|-----|-------|
| Photo   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| QR   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| OpenCV | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| MLKit | | | | :heavy_check_mark: | | |
| TFLite   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | | :heavy_check_mark: |

Windows : Windows 11, i7-10 @ 1.1GHz
Macos   : Big Sur,  i5-10 @ @ 1.1GHz
Linux   : Raspberry Buster, Cortex-A72 @ 1.5GHz
Android : Android 12, Pixel 5
iOS     : not tested
Coral   : [Accelerator](https://coral.ai/products/accelerator) tested with Windows 11 , gave very approximately an order of magnitude speed up.

### C4K-Photo-Example
Basic layout using screens. Basic camera functionality including photo capture, screenshot capture, and on Android capture of video with audio.
On Raspberry PI a mouse must be used, a touch pad does not work correctly.

### C4K-QR-Example.
Everything you need to read a restaurant menu. Long press or double tap on a highlighted QR code to open a webrowser. Illustrates basic analysis, screen annotation, and user interaction. 

### C4K-OpenCV-Example.
Edge detect the video stream. Illustrates using OpenCV analysis and replacing the original preview with the transformed image.

### C4K-MLKit-Example
Face detect, MLKit is Android only. Illustrates using the ImageProxy api.

### C4K-TFLite-Example
Object classification. Illustrates a computationally expensive algorithm (not necessarily a characteristic of Tensorflow Lite), and writing text to the Preview image.

## Preview Widget

An app can have multiple `Preview` widgets, but only one can be connected to the physical camera unit at a time. A natural way to implement this is to add a preview widget to a screen's contents, then connect to the camera unit `on_enter` and disconnect `on_pre_leave`. The C4K-Photo-Example illustrates this, the other examples simply connect the camera after `on_start()` and disconnect `on_stop()`.

### Preview Widget Properties

The widget has these Kivy properties:

#### aspect_ratio
A string property. Either '4:3' (default) or '16:9'. 

#### letterbox_color
A color property. Geometry tells us that layout of a fixed aspect ratio widget almost always results in letterboxing. Art tells us we can hide letterboxes by filling them with a color that matches the surrounding widgets. 

#### orientation
A string property. One of 'portrait' , 'landscape', 'same', 'opposite'.  The default is the 'same' as the device or window. Best not to change this until you have read [this section](). 

### Preview Widget API

The widget has these methods:

#### Connect Camera 

```python
    def connect_camera(self,kwargs):
```

Optional arguments:
    
##### camera_id
Specify which camera to connect to. For example `camera_id = 'front'`. A string containing an integer (default '0'), or on Android 'back' (default), or 'front'.

##### mirror
Boolean default True. For example `mirror = False`. Ignored on Android where by convention 'front' is always mirrored and 'back' is never mirrored.

##### filepath_callback
On a capture of a photo, video, or screenshot, this callback returns the path and name of the saved file. For example `filepath_callback = my_method`, where `my_method` is an app supplied method with a string argument.

##### sensor_resolution
Overrides the default sensor resolution, which is the highest resolution available, except Raspberry Pi where it is (1024, 768). Tuple of two integers, for example `sensor_resolution = (640, 480)`. The resulting capture resolution obtained depends on the behavior of the camera provider (for example it is ignored by GStreamer). The capture resolution also depends on the relative orientation and aspect ratio of the Preview. Treat the value specified as a request that may not be exactly honored.

##### analyze_pixels_resolution
Sets the pixels resolution passed by `analyze_pixels_callback()`. A scalar, representing the number of pixels on the long edge, the short edge is determined using the aspect ratio. For example `analyze_pixels_resolution = 720`. The default is the minimum of cropped sensor resolution and 1024.

##### enable_analyze_pixels
Use `enable_analyze_pixels = True` to enable the `analyze_pixels_callback()`

##### enable_analyze_imageproxy
Use `enable_analyze_imageproxy = True` to enable the `analyze_imageproxy_callback()`
Android only.

##### enable_zoom_gesture
Default True.  Android only.

##### enable_focus_gesture
Default True. Android only.
       
##### imageproxy_data_format:
Applies only to the Android ImageProxy api. 'yuv420' (default) or 'rgba'.


#### Disconnect Camera

Always do this. It is sometimes critically important to disconnect the camera when it is no longer used. 
```python
    def disconnect_camera(self):
```
  
#### Capture
```python
    def capture_photo(self, kwargs):
    def capture_screenshot(self, kwargs):
    def capture_video(self, kwargs):      # Android only
    def stop_capture_video(self):         # Android only
```    
   Optional arguments:

##### location :
A directory that must exist. Default '.' except on Android where can be 'shared' (default) or 'private'.

##### subdir
A single directory that will be created. Default value is the date.

##### name
The file name, default value is the time and '.jpg' or '.mp4'

#### Select Camera

Change the currently connected camera, camera_id must specify a physically connected camera.

```python
    def select_camera(self, camera_id):
```

#### Zoom
Android only, zoom_delta() called by pinch/spread gesture unless disabled.
```python 
    def zoom_delta(self, delta_scale):  
    def zoom_abs(self, scale):  
```

#### Flash
Android only. For capture photo only, ignored for video and data.
Sequence flash : off, on, auto (default), 
```python 
    def flash(self)
```

#### Focus
Android only, if available on device. Called by a tap gesture unless disabled
```python
    def focus(x, y): 
```

## Image analysis

### Overview

Implement video data analysis by creating a subclass of `Preview` and defining two methods. One to analyze the frame the second to update the Preview image. In general like this:

```python
class CustomAnalyzer(Preview):
      def analyze_pixels_callback(self, pixels, size, image_pos, image_scale, mirror):
	### Add your image analysis code here
				
      def canvas_instructions_callback(self, texture, size, pos):
	### Add your Preview annotation code here

      # On Android this is an alternative to analyze_pixels_callback()
      def analyze_imageproxy_callback(self, image_proxy, image_pos, image_scale, mirror, degrees):
	### Add your imageproxy specific analysis code here
```

### Examples

Wondering what this pattern looks like in practice? Look at some examples: [QR Reader](https://github.com/Android-for-Python/C4K_QR/qrreader.py), and [OpenCV](https://github.com/Android-for-Python/C4K_ocv/edgedetect.py).

### Implementation Details

Image analysis must be enabled with a `connect_camera()` parameter, either `connect_camera(enable_analyze_pixels = True)` or `connect_camera(enable_analyze_imeageproxy = True)`

The `image_pos, image_scale, mirror` parameters enable mapping the analysis results coordinates to Preview coordinates. 

The pixels api provides images with the same orientation and aspect ratio as the Preview.

The imageproxy api provides images in landscape, regardless of the preview orientation. A degrees parameter enables adjusting the analysis accordingly.

### Performance

The camera provides a stream of images for analysis via the `analyze_pixels_callback()` callback. Images arrive at typically 30 fps, so the app has less than 30mS to do the analysis. The api has a fallback mechanism so that images are analyzed only when the previous analysis is complete. If the analysis results are 'jerky' it is because the analysis algorithm is too slow for the hardware.

The analysis code must be lean. So for example Keras is a development environment, a whole bunch of stuff you don't need to run an inference. Port the application to Tensorflow Lite.

## Camera Behavior

### A Physical Camera

A camera is a single physical device with a software api, it is not a software object though it can look like one. It is a physical object with physical constraints.

### Resolution

In the context of a camera, resolution has several uses. It is always a tuple, in this context (width, height).

#### Sensor Resolution

This is a phyical property of the sensor module. The default behavior of `connect_camera()` is to use the maximum resolution provided by the camera provider. Is can be overridden with the `sensor_resolution` option, but in general camera providers take this a a hint which may be ignored or re-interpreted. `GStreamer` ignores this option, `picamera` may require it.

#### Cropped Sensor Resolution

The sensor resolution cropped according to the orientation of the sensor, the orientation of the Preview, and the aspect ratio of the Preview.

#### Preview Resolution

Is a physical property of the screen (display resolution) and the Preview widget size on the screen. The preview resolution can be less than or greater than the sensor resolution.

#### Capture Resolution

The resolution of a capture. A photo capture resolution is cropped sensor resolution. Video resolution is one to the standard resolutions, depending on the cropped sensor resolution. A screenshot capture resolution is the Preview resolution. 

#### Analysis Resolution

Analysis resolution is less than or equal to cropped sensor resolution. It may be useful to reduce this in order to decrease analysis time, at the cost of analysis resolution.  

The `analyze_pixels_callback()` resolution may be changed with the `analyze_pixels_resolution` camera connect option. The scale parameter allows re-scaling of the analysis results to the Preview resolution.

The `analyze_imageproxy_callback()` implements a graceful degradation mechanism. This automatically reduces frame rate and/or image resolution. A very slow frame analysis will case the feed to stop.  

#### Display Resolution.

Nothing to do with a camera, it is a physical property of a screen. A scalar measured in dpi. 


## Known Issues

### Issue: iOS implementation is not tested.

Some things probably don't work yet, set your expectations accordingly or kick back and wait a while.

### Issue: Raspberry PI video frame rate is lower than other platforms.

Functional, but low. The issue is probably either in the picamera package or the design of the Kivy camera provider wrapper. A gating item would be the [picamera2 package](https://www.raspberrypi.com/news/bullseye-camera-system/) which is in development.  

### Issue: Android Rotation

Rotating the physical device through 'inverted portrait' may result in an 'inverted landscape' display. An additional rotation to 'portrait' and back to 'landscape' corrects the display. 

### Issue: Android .mp4 Orientation

Video file orientation is incorrect if the preview orientation is not the same as the device orientation. Do not use this layout configuration when recording video. [Google issue tracker](https://issuetracker.google.com/issues/201085351).

### Issue: Android .jpg Orientation.

Some third party image viewers will incorrectly display a .jpg as rotated by 90 degrees. This occurs if the capture preview orientation is not the same as the device orientation, and the third party viewer does not use the Exif metadata.   

### Issue: Android connect_camera during on_start()

On Android, a `connect_camera()` called during `on_start()` will result in intermittent crashes during app start. The unfiltered logcat will contain: 'library "libdexfile.so" not found'.
Use Kivy clock to schedule the `connect_camera()` one time step later. 