package dev.csync.jot;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.text.Editable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.List;

/** The app screen: add a task, tick one off, clear what is done. */
public class MainActivity extends Activity {

    private LinearLayout list;
    private EditText input;

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#101214"));
        root.setPadding(32, 48, 32, 32);

        TextView title = new TextView(this);
        title.setText("Jot");
        title.setTextSize(28);
        title.setTextColor(Color.parseColor("#E8EAED"));
        root.addView(title);

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setPadding(0, 24, 0, 16);

        input = new EditText(this);
        input.setHint("what needs doing");
        input.setTextColor(Color.parseColor("#E8EAED"));
        input.setHintTextColor(Color.parseColor("#7A8085"));
        input.setLayoutParams(new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        row.addView(input);

        Button add = new Button(this);
        add.setText("Add");
        add.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Editable e = input.getText();
                String text = e == null ? "" : e.toString().trim();
                if (text.length() > 0) {
                    Store.add(MainActivity.this, text);
                    input.setText("");
                    redraw();
                }
            }
        });
        row.addView(add);
        root.addView(row);

        ScrollView scroll = new ScrollView(this);
        list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(list);
        root.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        Button pin = new Button(this);
        pin.setText("Put widget on home screen");
        pin.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                android.appwidget.AppWidgetManager m =
                        android.appwidget.AppWidgetManager.getInstance(MainActivity.this);
                android.content.ComponentName cn =
                        new android.content.ComponentName(MainActivity.this, JotWidget.class);
                if (m.isRequestPinAppWidgetSupported()) {
                    m.requestPinAppWidget(cn, null, null);
                }
            }
        });
        root.addView(pin);

        Button clear = new Button(this);
        clear.setText("Clear done");
        clear.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Store.clearDone(MainActivity.this);
                redraw();
            }
        });
        root.addView(clear);

        setContentView(root);
        redraw();
    }

    private void redraw() {
        list.removeAllViews();
        List<Store.Item> items = Store.load(this);
        if (items.isEmpty()) {
            TextView empty = new TextView(this);
            empty.setText("nothing yet");
            empty.setTextColor(Color.parseColor("#7A8085"));
            empty.setGravity(Gravity.CENTER);
            empty.setPadding(0, 48, 0, 0);
            list.addView(empty);
        }
        for (int i = 0; i < items.size(); i++) {
            final int index = i;
            Store.Item it = items.get(i);
            CheckBox cb = new CheckBox(this);
            cb.setText(it.text);
            cb.setChecked(it.done);
            cb.setTextColor(Color.parseColor(it.done ? "#7A8085" : "#E8EAED"));
            cb.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    Store.toggle(MainActivity.this, index);
                    redraw();
                }
            });
            list.addView(cb);
        }
        JotWidget.refresh(this);
    }
}
