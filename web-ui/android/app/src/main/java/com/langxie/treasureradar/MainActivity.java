package com.langxie.treasureradar;
import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
public class MainActivity extends BridgeActivity {
    @Override public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ExternalItemPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
