package com.langxie.treasureradar;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class ClientSmokeTest {
    private String js(ActivityScenario<MainActivity> scenario, String code) throws Exception {
        AtomicReference<String> value = new AtomicReference<>("");
        CountDownLatch done = new CountDownLatch(1);
        scenario.onActivity(activity -> activity.getBridge().getWebView().evaluateJavascript(code, result -> {value.set(result);done.countDown();}));
        assertTrue("WebView JS callback", done.await(10, TimeUnit.SECONDS));
        return value.get();
    }
    private void waitFor(ActivityScenario<MainActivity> scenario, String condition) throws Exception {
        for (int i=0;i<60;i++) { if ("true".equals(js(scenario, condition))) return; Thread.sleep(500); }
        fail("WebView condition timed out: " + condition + " body=" + js(scenario, "document.body.innerText"));
    }
    @Test public void packagedClientConnectsOverHttpAndRestoresBackend() throws Exception {
        try(ActivityScenario<MainActivity> scenario = ActivityScenario.launch(MainActivity.class)) {
            waitFor(scenario,"!!document.querySelector('#backend-url')");
            assertTrue(js(scenario,"document.body.innerText").contains("TREASURE RADAR"));
            js(scenario,"var input=document.querySelector('#backend-url'); input.value='http://10.0.2.2:8765'; input.dispatchEvent(new Event('input',{bubbles:true})); document.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})); true");
            waitFor(scenario,"document.body.innerText.includes('ONLINE') && location.hash.includes('/login')");
            // Existing authentication view is still used. Test server validates a synthetic password.
            js(scenario,"var u=document.querySelector('#username'); u.value='test'; u.dispatchEvent(new Event('input',{bubbles:true})); var p=document.querySelector('#password'); p.value='test-only'; p.dispatchEvent(new Event('input',{bubbles:true})); document.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})); true");
            waitFor(scenario,"localStorage.getItem('auth_logged_in')==='true'");
            js(scenario,"location.hash='/candidates'; true");
            waitFor(scenario,"document.body.innerText.includes('LJ64HB34')");
            assertTrue("No horizontal overflow", "true".equals(js(scenario,"document.documentElement.scrollWidth <= innerWidth")));
            assertTrue(js(scenario,"document.body.innerText").contains("OPEN IN XIANYU"));
            js(scenario,"location.reload(); true");
            waitFor(scenario,"document.body.innerText.includes('LJ64HB34') && document.body.innerText.includes('ONLINE')");
            assertTrue(js(scenario,"localStorage.getItem('radar_backend')").contains("10.0.2.2:8765"));
        }
    }
}
