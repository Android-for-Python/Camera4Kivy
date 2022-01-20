Camera4Kivy
===========

*Yet Another Camera for Kivy*

This document has these sections [Overview](https://github.com/Android-for-Python/camera4kivy#overview), [Install](https://github.com/Android-for-Python/camera4kivy#install), [Examples](https://github.com/Android-for-Python/camera4kivy#examples), [Preview Widget](https://github.com/Android-for-Python/camera4kivy#preview-widget), [Image Analysis](https://github.com/Android-for-Python/camera4kivy#image-analysis), [Camera Behavior](https://github.com/Android-for-Python/camera4kivy#camera-behavior), [Camera Provider](https://github.com/Android-for-Python/camera4kivy#camera-provider), and [Known Behavior](https://github.com/Android-for-Python/camera4kivy#known-behaviors).

On Android only:
- Do not [install an arm7 build on an arm8 device](#behavior-android-armeabi-v7a-build-installed-on-an-arm64-v8a-device).

## Overview

Available on all the usual platforms except iOS.

```python
from camera4kivy import Preview
```

Camera4Kivy consists of a `Preview` widget with an api to connect to the physical camera unit. The Preview widget layout is [configured with Kivy properties](https://github.com/Android-for-Python/Camera4Kivy#preview-widget-properties) , the camera unit and image analysis behavior are [configured with an api](https://github.com/Android-for-Python/Camera4Kivy#preview-widget-api). For example:

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

To connect the camera unit to the Preview call the preview's `connect_camera()` method, **after on_start()**. For example to connect the camera with the image analysis api enabled :

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

On Android a pinch/spread gesture controls zoom, and a tap overrides any automatic focus and metering (if available). Some `connect_camera()` options are platform specific.

## Install

A [camera provider](https://github.com/Android-for-Python/camera4kivy#camera-provider) may be required. On a destop the camera provider is installed once. On Android the camera provider is [added to each project](https://github.com/Android-for-Python/camera4kivy#android-camera-provider).

### Install Camera4Kivy on Desktop

`pip3 install camera4kivy`

### Install Camera4Kivy on Android

Camera4Kivy depends on the 'master' version of Buildozer. Currently `1.2.0.dev0`

`pip3 install git+https://github.com/kivy/buildozer.git`


#### buildozer.spec:

`android.api = 30`   (or higher, min 29)

`requirements = python3, kivy, camera4kivy, gestures4kivy`

Set `p4a.hook` to enable the app's use of the [camera provider](https://github.com/Android-for-Python/camera4kivy#android-camera-provider). This sets the required p4a options.

`p4a.hook = camerax_provider/gradle_options.py`

The implementation of the camerax gradle dependencies is architecture specific, an app built for armeabi-v7a will crash on an arm64-v8a device.

#### Run Time Permissions

The following run time permissions must be in be requested in the app. As usual request these in build() or after on_start(). See the examples.

Always required: `CAMERA`

Required to record video with audio: `RECORD_AUDIO`

Required when capturing photo, screenshot, or video and saving to shared storage, and only on devices running api_version < 29: `WRITE_EXTERNAL_STORAGE`

## Examples

A prerequisite is that a working camera is installed. Test this with the platform's camera app before proceeding. All examples use the platform specific camera provider, and assume the typical default camera_id of '0'. If you find the example does not connect to a camera review the available camera ids and your camera provider choice.

### Tested Examples and Platforms 

The Photo example illustrates basic camera usage, try this first. The remaining examples illustrate image analysis using various packages. Not tested : iOS, set your expectations accordingly.

On Android `orientation = all` is available, on the desktop you can change the window size to simulate orientation, and thus rotating a mobile device. 

| Example | Windows | Macos | Linux | Android | iOS | Coral |
|---------|---------|-------|-------|---------|-----|-------|
| Photo   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| QR   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| OpenCV | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | |
| MLKit | | | | :heavy_check_mark: | | |
| TFLite   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | | | :heavy_check_mark: |

- Windows : Windows 11, i7-10 @ 1.1GHz, Python 3.8.2  Kivy==2.1.0.dev0
- Windows : Windows 10, i3-7 @ 2.4GHz, Python 3.9.7 Kivy==2.0.0
- Macos   : Big Sur,  i5-10 @ @ 1.1GHz, Python 3.9.9 Kivy==2.0.0
- Linux   : Raspberry Buster, Cortex-A72 @ 1.5GHz Python3.7.3 Kivy==2.0.0
- Android : build : arm64-v8a  device: Android 12, Pixel 5
- Android : build : armeabi-v7a device: Android 6, Nexus 5  Start is somewhat slow.
- iOS     : not tested
- Coral   : [Accelerator](https://coral.ai/products/accelerator) tested with Windows 11 , gave very approximately an order of magnitude speed up.

### [C4K-Photo-Example](https://github.com/Android-for-Python/c4k_photo_example)
Illustrates basic layout using screens. Basic camera functionality including photo capture, screenshot capture, and on Android capture of video with audio.
On Raspberry PI a mouse must be used, a touch pad does not work correctly.

### [C4K-QR-Example](https://github.com/Android-for-Python/c4k_qr_example)
Everything you need to read a restaurant menu. Long press or double click on a highlighted QR code to open a web browser. Illustrates basic analysis, screen annotation, and user interaction. 

### [C4K-OpenCV-Example.](https://github.com/Android-for-Python/c4k_opencv_example)
Edge detect the video stream. Illustrates using OpenCV analysis and replacing the original preview with the transformed image.

### [C4K-MLKit-Example](https://github.com/Android-for-Python/c4k_mlkit_example)
Face detect, MLKit is Android only. Illustrates using the ImageProxy api.

### [C4K-TFLite-Example](https://github.com/Android-for-Python/c4k_tflite_example)
Object classification. Illustrates using a large Tensorflow Lite model, and writing text to the Preview image.

## Preview Widget

An app can have multiple `Preview` widgets, but only one can be connected to the physical camera unit at a time. A natural way to implement this is to add a preview widget to a screen's contents, then connect to the camera unit `on_enter` and disconnect `on_pre_leave`. The C4K-Photo-Example illustrates this, the other examples simply connect the camera after `on_start()` and disconnect `on_stop()`.

### Preview Widget Properties

The widget has these Kivy properties that configure its layout:

#### aspect_ratio
A string property. Either '4:3' (default) or '16:9'. 

#### letterbox_color
A color property. Geometry tells us that layout of a fixed aspect ratio widget almost always results in letterboxing. Art tells us we can hide letterboxes by filling them with a color that matches the surrounding widgets. 

#### orientation
A string property. One of 'portrait' , 'landscape', 'same', 'opposite'.  The default is the 'same' as the device or window. This choice modifies effective resolution, [see](https://github.com/Android-for-Python/camera4kivy#cropped-sensor-resolution). The best resolution is always obtained with 'same'.

### Preview Widget API

The widget has these methods:

#### Connect Camera 

This may only be called after `on_start()`.

```python
    def connect_camera(self,kwargs):
```

Optional arguments:
    
##### camera_id
Specify which camera to connect to. For example `camera_id = 'front'`. A string containing an integer (default '0'), or on Android 'back' (default), or 'front'.

##### mirrored
Boolean default True. Mirrors the preview image. Ignored on Android where by convention 'front' is always mirrored and 'back' is never mirrored.

##### filepath_callback
On a capture of a photo, video, or screenshot, this callback returns the path and name of the saved file. For example `filepath_callback = my_method`, where `def my_method(self, path):` is an app supplied method with a string argument.

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

Captures are saved to `<location>/<subdir>/<name>.jpg` or `.mp4`.

The default values are as follows. On a desktop `<location>` is the current directory `.`, on Android `<location>` is `DCIM/<appname>`. The value of `<subdir>` is the current date, the format is 'YYYY_MM_DD'. The value of `<name>` is the current time, the format is 'hh_mm_ss_xx' (xx is 1/100 sec).

The [filepath_callback](https://github.com/Android-for-Python/Camera4Kivy#filepath_callback) reports the actual path for a particular capture.

Be aware that on Android >= 10 shared storage files are saved in a database, called MediaStore, and not in a file system. The characteristics of Android storage are outside the scope of this document. 

The values of `<location>`, `<subdir>`, and `<name>` can be modified with optional keyword arguments:

##### location

The value replaces the default value of `<location>`.

On a desktop the value is directory that must exist. 

On Android the value can only be `'shared'` or `'private'`, other values are ignored. The value `'shared'` specifies Android shared storage `DCIM/<appname>` (this is also the default). The value `'private'` specifies app local storage `app_storage_path()/DCIM`. If you want a different location use 'private' and move the resulting file based on the path provided by filepath_callback.

##### subdir

The value replaces the default value of `<subdir>`, the subdirectory will be created. 

##### name

The value replaces the default value of `<name>`, the `.jpg` or `.mp4` extensions will be added automatically.

Note that it is a characteristic of Android >= 10 shared storage that a second capture with a same subdir and name values as the first will not overwrite the first. It will create a second file named `<subdir>/<name> (1).jpg`, the name is created by Android MediaStore. The MediaStore may crash if it creates too many (31 ?) such names.

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

### Overview and Examples

The programming pattern for video data analysis is to create a subclass of `Preview` and implement two predefined methods. One to analyze the frame, the second to modify the Preview image with the analysis result. In general like this:

```python
class CustomAnalyzer(Preview):
      def analyze_pixels_callback(self, pixels, size, image_pos,
                                  image_scale, mirror):
	### Add your pixels analysis code here
	### Add your coordinate transforms here
				
      def canvas_instructions_callback(self, texture, tex_size, tex_pos):
	### Add your Preview annotation or image replacement code here
```

On Android this is an alternative to analyze_pixels_callback(), it is used for Android only analysis packages.
```
      def analyze_imageproxy_callback(self, image_proxy, image_pos,
                                      image_scale, mirror, degrees):
	### Add your imageproxy specific analysis code here
```

Keep to this pattern. Perform analysis and coordinate transforms in the 'analyze_pixel_callback' (or imageproxy) method. And in 'canvas_instructions_callback' only display the results of previous calculations. Data passed from the analysis method to the display method must be passed in a thread safe way.

The `analyze_pixels_callback` method is used to analyze its RGBA `pixels` and `size` arguments. The `pos`, `scale`, and `mirror` arguments enable mapping the analyzed pixels coordinates to Preview coordinates. The `mirror` parameter is required because `pixels` image is never mirrored, but the Preview may be. An example:

```python
   def analyze_pixels_callback(self, pixels, image_size, image_pos,
                               scale, mirror):
	# Convert the image encoding		       
        pil_image = Image.frombytes(mode='RGBA', size=image_size,
	                            data= pixels)
        # Analyze the image				    
        barcodes = pyzbar.decode(pil_image, symbols=[ZBarSymbol.QRCODE])
	# Collect the results and transform the coordinates
        found = []
        for barcode in barcodes:
            text = barcode.data.decode('utf-8')
            if 'https://' in text or 'http://' in text:
                x, y, w, h = barcode.rect
                # Map Zbar coordinates to Kivy coordinates
                y = image_size[1] -y -h
                # Map Analysis coordinates to Preview coordinates
                if mirror:
                    x = image_size[0] -x -w
                x = round(x * scale + image_pos[0])
                y = round(y * scale + image_pos[1])
                w = round(w * scale)
                h = round(h * scale)
                found.append({'x':x, 'y':y, 'w':w, 'h':h, 't':text})
	# Save the results in a thread safe way
        self.make_thread_safe(list(found)) ## A COPY of the list
```

Analysis and canvas annotation callbacks occur on different threads. The result of the analysis must be saved in a thread safe way, so that it is available for the canvas callback. We pass a **copy** of the result to:

```python
    @mainthread
    def make_thread_safe(self, found):
        self.annotations = found
```

And add the thread safe annotations to the canvas. 

```python
    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        # Add the annotations determinined during analyze callback.
        Color(1,0,0,1)
        for r in self.annotations:
            Line(rectangle=(r['x'], r['y'], r['w'], r['h']), width = dp(2))	
```
We can also replace the existing Preview image with some other texture, positioned with the 'tex_size' and 'tex_pos' arguments. Use a thread safe texture created as a result of some image analysis like this:

```python
    def canvas_instructions_callback(self, texture, tex_size, tex_pos):
        # Add a different preview image, which is a transformed camera image
	# this image has 'analyze_pixels_resolution'
        if self.analyzed_texture:
	    # 'self.analyzed_texture' contents created
	    # by analyze_pixels_callback()
            Color(1,1,1,1)
            Rectangle(texture= self.analyzed_texture,
	              size = tex_size, pos = tex_pos)
```	   
The new texture will be automatically mirrored by 'text_size' and 'tex_pos' if required. These 'text_size' and 'tex_pos' arguments are for adding a texture, and not valid for coordinate calculations as they are potentially mirrored.

See the OpenCV example for details on creating a thread safe texture. 

The above code fragments are fully implemented in two examples: [QR Reader](https://github.com/Android-for-Python/c4k_qr_example/blob/main/qrreader.py), and [OpenCV](https://github.com/Android-for-Python/c4k_opencv_example/blob/main/edgedetect.py). Similar examples exhibiting this pattern are [tflite](https://github.com/Android-for-Python/c4k_tflite_example/blob/main/classifyobject.py) and [mlkit](https://github.com/Android-for-Python/c4k_mlkit_example/blob/main/facedetect.py).

### User Interaction

But wait, there is more, a user can interact with the analysis results in the Preview. The Preview subclass may have multiple inheritance, for example to allow the user to interact with annotations on the screen. The QR Reader example illustrates this, by inheriting from a gestures package:

```python
    class QRReader(Preview, CommonGestures):
```

That package's gesture callbacks, and an annotation location test are used to initiate some action. In this case open a web browser based on a URL in a QR code, and a long press or mouse double click inside the box drawn around the QR code.

```python
    def cg_long_press(self, touch, x, y):
        self.open_browser(x, y)

    def cg_double_tap(self, touch, x, y):
        self.open_browser(x, y)

    def open_browser(self, x, y):
        for r in self.annotations:
            if x >= r['x'] and x <= r['x'] + r['w'] and\
               y >= r['y'] and y <= r['y'] + r['h']:
                webbrowser.open_new_tab(r['t'])
```

### Coordinates and image encoding

**Important**, be aware of different coordinate systems and image encoding. A test with a print statement of third party analysis code coordinates can be valuable. 

- Kivy image coordinates have their origin at the bottom left. Most other systems use top left (with positive y increaing downwards) as their origin.

- Kivy image properties are a (width, height) tuple. Some packages, notably numpy images, reverse the order to (height, width).

- Kivy pixels are encoded RGBA. Third party analysis code may expect some other encoding, both Pillow and OpenCV provide encoding converions. Some image recodings are computationally expensive.

- The 'canvas_instructions_callback()' arguments 'tex_size' and 'tex_pos' are potentially mirrored and their values are not valid for coordinate mapping. Perform mapping in 'analyze_pixels_callback()' using the 'image_size' and 'image_pos' arguments.


### Analysis Configuration

Image analysis is enabled with a parameter to `connect_camera()`:

`connect_camera(enable_analyze_pixels = True)`

To change the default analysis resolution specify the number of pixels in the long edge (the default is the smaller of 1024 or the cropped resolution):

`connect_camera(enable_analyze_pixels = True, analyze_pixels_resolution = 720)`

The pixels api provides images with the same orientation and aspect ratio as the Preview.

On Android only, the imageproxy api is an alternative to the pixels api. 

`connect_camera(enable_analyze_imageproxy = True)`

The imageproxy api provides images in landscape, regardless of the preview orientation. A degrees parameter enables adjusting the analysis accordingly. Android implements automatic changes to frame rate and resolution in the case of slow analysis.

### Debugging

Check that the app analysis code is doing what you expect. If the result of this is coordinates (most cases) then check these with a print statement. Move whatever you expect to be detected to the four corners of the camera view. Look the printed values, do they reflect the analysed image pixels size and orientation? Repeat for the coordinates after they are mapped to a Kivy widget.

Measure the time the analysis algorithm takes to execute on one frame. Do this in the cases of detection and nothing to detect. This along with some overhead will define the maximum analysis frame rate. The [tflite example](https://github.com/Android-for-Python/c4k_tflite_example/blob/main/classifyobject.py) monitors analysis frame rate as part of its normal operation.

### Performance

The camera provides a stream of images for analysis via `analyze_pixels_callback()`. Images arrive at typically 30 fps, so given some overhead the app has probably less than 30mS to do the analysis.

The api has a builtin mechanism so that images are analyzed only when the previous analysis is complete. This mechanism does not alter the canvas instructions frame rate. If the analysis results are 'jerky' it is because the analysis algorithm is slow for the hardware.

One way to improve performance is to reduce the `analyze_pixels_resolution` as shown above. This option may alter the qualitative behavior, perhaps because of resolution bias in some third party analyzers. Experiment, some analysis code will work well at much less than VGA resolution. 

The analysis code must be lean. So for example Keras is a complete development environment, a whole bunch of stuff you don't need to run an inference. Port the application to Tensorflow Lite, then use the tflite-runtime not the full Tensorflow Lite.

## Camera Behavior

### A Physical Camera

A camera is a single physical device with a software api, it is not a software object though it can look like one. It is a physical object with physical constraints. 

### Resolution

In the context of a camera, resolution has several uses. It is always a tuple, in this context (width, height).

#### Sensor Resolution

This is a phyical property of the sensor module. The default behavior of `connect_camera()` is to use the maximum resolution provided by the camera provider. Is can be overridden with the `sensor_resolution` option, but in general camera providers take this a a hint which may be ignored or re-interpreted. `GStreamer` ignores this option, `picamera` may require it.

#### Cropped Sensor Resolution

The sensor resolution cropped according to the orientation of the sensor, the orientation of the Preview, and the aspect ratio of the Preview. The will impact the capture resolution, for example a 16:9 aspect image maybe cropped from a 4:3 sensor image. Thus the product of width and height will less for 16:9 that for 4:3 in this case.

Rotating a mobile device also rotates the sensor, the highest resolution images are obtained when the Priview widget orientation is the same as the device orientation. Conversly for example a landscape preview with the device in portrait orientation will result in an image width resolution that is the sensor height resolution.

This behaviour is a characteric of the camera having a physical constraint resolution. It is mostly transparent to the app user unless the sensor resolution is low, or a photo capture has lower than expected resolution.

#### Preview Resolution

Is a physical property of the screen (display resolution) and the Preview widget size on the screen. The preview resolution can be less than or greater than the cropped sensor resolution.

#### Capture Resolution

The resolution of a capture. A photo capture resolution is cropped sensor resolution. Video resolution is one to the standard resolutions, depending on the cropped sensor resolution. A screenshot capture resolution is the Preview resolution. 

#### Analysis Resolution

Analysis resolution is less than or equal to cropped sensor resolution. It may be useful to reduce this in order to decrease analysis time, at the cost of analysis resolution.  

The `analyze_pixels_callback()` resolution may be changed with the `analyze_pixels_resolution` camera connect option. The scale parameter allows re-scaling of the analysis results to the Preview resolution.

The `analyze_imageproxy_callback()` implements a graceful degradation mechanism. This automatically reduces frame rate and/or image resolution. A very slow frame analysis will case the feed to stop.  

#### Display Resolution.

Nothing to do with a camera, it is a physical property of a screen. A scalar measured in dpi.


## Camera Provider

Camera4Kivy depends on a 'camera provider' to access the OS camera api. On most platforms this uses the same provider as Kivy, with modified defaults.

| Platform    | Provider      | Requires       |
|-------------|---------------|----------------|
| Windows     | [OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv)                      |
|             | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)                      |
| Macos       | [AVFoundation](https://github.com/Android-for-Python/camera4kivy#avfoundation)| OSX >= 10.7    |   
| Linux       | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)                      |
|             | [OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv)                      |
| Rasberry    | [Picamera](https://github.com/Android-for-Python/camera4kivy#picamera)    | <= Buster      |
|             | [Gstreamer](https://github.com/Android-for-Python/camera4kivy#gstreamer)  |  <= Buster |
|             |[OpenCV](https://github.com/Android-for-Python/camera4kivy#opencv) |  <= Buster  |
|             | [Picamera2](https://github.com/Android-for-Python/camera4kivy#picamera2)    | >= Bullseye      |
| Android     | [CameraX](https://github.com/Android-for-Python/camera4kivy#android-camera-provider)                      |  Android >= 5.0 |
| iOS         | [AVFoundation](https://github.com/Android-for-Python/camera4kivy#avfoundation)                      |

Like Kivy, the first available provider is selected. Some camera provider specific behavior should be expected. For example a switch to a camera that does not exist will be ignored on MacOS and Rasberry Pi, but generate a screen message with OpenCV or GStreamer. Camera resolution defaults to the maximum available sensor resolution, except on Raspberry Pi where the default is (1024, 768).

You can remove a camera provider ('picamera' in the example below) from the above lists by inserting this code **before** `from kivy.app import App`.

```python
from kivy import kivy_options
providers= list(kivy_options['camera'])
providers.remove('picamera')
kivy_options['camera'] = tuple(providers)
```

### Android Camera Provider

`cd <project directory>`

`git clone https://github.com/Android-for-Python/camerax_provider.git`

`rm -rf camerax_provider/.git`

Set `p4a.hook` to enable the app's use of the camera provider.

`p4a.hook = camerax_provider/gradle_options.py`

### OpenCV

`pip3 install opencv-python`

### GStreamer

Depends on the Linux flavor, but commonly:

`sudo apt-get install gstreamer-1.0`

`sudo apt-get install gstreamer1.0-dev`

### Picamera
Pre-installed

### Picamera2
[Raspberry PI Bullseye not available](https://github.com/Android-for-Python/camera4kivy#behavior-raspberry-pi-bullseye-not-available).

### AVFoundation
Pre-installed


## Known Behavior

### Behavior: Preview has no aspect_ratio = 'fit'

There is no way to specify inverted letterboxing. Where the Preview exactly fits the space available, resulting in one axis of the captured image being partially shown to the user.

### Behavior: iOS implementation is not tested.

It probably will have issues, don't expect it to work.

### Behavior: Raspberry PI video frame rate is lower than other platforms.

Functional, but with a low frame rate. The issue is probably related to the current picamera implementation, try Gstreamer or OpenCV.

### Behavior: Raspberry PI Bullseye not available

The RaspberryPI video stack changed with Bullseye. In Bullseye currently the only working camera source is `libcamera`. Picamera is not availible, [apparently](https://www.raspberrypi.com/news/bullseye-camera-system/) a RPI Picamera2 Python interface is in development. And `libcamera` is not compatible with OpenCV or Kivy's GStreamer implementation. 

### Behavior: Android Rotation

Rotating the physical device through 'inverted portrait' may result in an 'inverted landscape' display. An additional rotation to 'portrait' and back to 'landscape' corrects the display. 

### Behavior: Android .mp4 Orientation

Video file orientation is incorrect if the preview orientation is not the same as the device orientation. Do not use this layout configuration when recording video. [Google issue tracker](https://issuetracker.google.com/issues/201085351).

### Behavior: Android .jpg Orientation.

Some third party image viewers will incorrectly display a .jpg as rotated by 90 degrees. This occurs if the capture preview orientation is not the same as the device orientation, and the third party viewer does not use the Exif metadata.   

### Behavior: Android connect_camera during on_start()

On Android, a `connect_camera()` called during `on_start()` will result in intermittent crashes during app start. The unfiltered logcat will contain: 'library "libdexfile.so" not found'.
Use Kivy clock to schedule the `connect_camera()` one time step later.

### Behavior: Android switching cameras, short duration inverted image.

When switching cameras there may be a short duration inverted image, this is more likely on older Android devices.

### Behavior: Android armeabi-v7a build installed on an arm64-v8a device

The implementation of Google's camerax gradle dependencies is architecture specific, an app built for armeabi-v7a will crash on an arm64-v8a device. To rin on an arm64-v8a device you **must** build for arm64-v8a.



