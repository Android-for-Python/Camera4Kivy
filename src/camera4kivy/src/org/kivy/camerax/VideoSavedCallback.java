package org.kivy.camerax;

import androidx.camera.core.VideoCapture.OnVideoSavedCallback;
import androidx.camera.core.VideoCapture.OutputFileResults;
import android.net.Uri;
import android.content.Context;
import android.database.Cursor;
import android.provider.MediaStore.MediaColumns;
import org.kivy.camerax.CallbackWrapper;
import org.kivy.android.PythonActivity;

public class VideoSavedCallback implements OnVideoSavedCallback {

    private CallbackWrapper callback_wrapper;

    public VideoSavedCallback(CallbackWrapper callback_wrapper) {	
	this.callback_wrapper = callback_wrapper;
    }    

    public void onVideoSaved(OutputFileResults outputFileResults){
	Uri saveuri = outputFileResults.getSavedUri();
	String result = "";
	if (saveuri != null) {
	    if (saveuri.getScheme().equals("content")) {
		Context context =
		    PythonActivity.mActivity.getApplicationContext();
		Cursor cursor =
		    context.getContentResolver().query(saveuri, null,
						       null, null, null);
		String dn = MediaColumns.DISPLAY_NAME;
		String rp = MediaColumns.RELATIVE_PATH;
		int nameIndex = cursor.getColumnIndex(dn);
		int pathIndex = cursor.getColumnIndex(rp);
		cursor.moveToFirst();
		String file_name = cursor.getString(nameIndex);
		String file_path = cursor.getString(pathIndex);
		cursor.close();
		result = file_path + file_name; 
	    }
	}
	this.callback_wrapper.callback_string(result);
    }
	
    public void onError(int videoCaptureError, String message, Throwable cause){
	this.callback_wrapper.callback_string("ERROR:" + message); 
    }
}
