package dev.csync.jot;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.ArrayList;
import java.util.List;

/** The task list itself. One line per task, a leading "x " meaning done. */
public class Store {
    private static final String PREFS = "jot";
    private static final String KEY = "items";

    public static class Item {
        public final String text;
        public final boolean done;
        Item(String text, boolean done) { this.text = text; this.done = done; }
    }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static List<Item> load(Context c) {
        List<Item> out = new ArrayList<Item>();
        String raw = prefs(c).getString(KEY, "");
        if (raw.length() == 0) return out;
        for (String line : raw.split("\n")) {
            boolean done = line.startsWith("x ");
            String text = (done ? line.substring(2) : line).trim();
            if (text.length() == 0) continue;
            out.add(new Item(text, done));
        }
        return out;
    }

    public static void save(Context c, List<Item> items) {
        StringBuilder sb = new StringBuilder();
        for (Item i : items) {
            if (i.done) sb.append("x ");
            sb.append(i.text).append("\n");
        }
        prefs(c).edit().putString(KEY, sb.toString()).commit();
    }

    public static void add(Context c, String text) {
        List<Item> items = load(c);
        items.add(0, new Item(text, false));
        save(c, items);
    }

    public static void toggle(Context c, int index) {
        List<Item> items = load(c);
        if (index < 0 || index >= items.size()) return;
        Item i = items.get(index);
        items.set(index, new Item(i.text, !i.done));
        save(c, items);
    }

    public static void clearDone(Context c) {
        List<Item> items = load(c);
        List<Item> keep = new ArrayList<Item>();
        for (Item i : items) if (!i.done) keep.add(i);
        save(c, keep);
    }

    /** How many are still open, for the widget's header. */
    public static int openCount(Context c) {
        int n = 0;
        for (Item i : load(c)) if (!i.done) n++;
        return n;
    }
}
