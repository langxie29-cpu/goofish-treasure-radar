package com.langxie.treasureradar;
import android.content.Intent;
import android.net.Uri;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
@CapacitorPlugin(name = "ExternalItem")
public class ExternalItemPlugin extends Plugin {
    @PluginMethod public void open(PluginCall call) {
        String value = call.getString("url");
        if (value == null) { call.reject("Missing URL"); return; }
        Uri uri = Uri.parse(value);
        if (!"https".equals(uri.getScheme()) || !("www.goofish.com".equals(uri.getHost()) || "goofish.com".equals(uri.getHost()))) {
            call.reject("Invalid Goofish URL"); return;
        }
        try {
            Intent app = new Intent(Intent.ACTION_VIEW, uri).setPackage("com.taobao.idlefish");
            getActivity().startActivity(app);
        } catch (Exception unavailable) {
            try { getActivity().startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
            catch (Exception error) { call.reject("No app or browser can open this item"); return; }
        }
        call.resolve();
    }
}
