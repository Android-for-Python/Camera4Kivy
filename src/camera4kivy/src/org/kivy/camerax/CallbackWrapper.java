package org.kivy.camerax;

import androidx.camera.core.ImageProxy;
import android.graphics.Rect;
import android.util.Size;
import java.util.Dictionary;

public interface CallbackWrapper {
    public void callback_string(String filepath);
    public void callback_image(ImageProxy image);
    public void callback_config(Rect croprect, Size resolution, int rotation);
}



