package org.kivy.camerax;

import androidx.camera.core.ImageAnalysis;
import androidx.camera.core.ImageProxy;
import org.kivy.camerax.CallbackWrapper;

public class ImageAnalysisAnalyzer implements ImageAnalysis.Analyzer {

    private CallbackWrapper callback_wrapper;

    public ImageAnalysisAnalyzer(CallbackWrapper callback_wrapper) {	
	this.callback_wrapper = callback_wrapper;
    }

    public void analyze(ImageProxy image) {
	this.callback_wrapper.callback_image(image); 
    }
}
