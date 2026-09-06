package dev.csync.jot;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.view.View;
import android.widget.RemoteViews;
import java.util.List;

/** The home-screen widget: the three oldest open tasks, each tappable to tick off. */
public class JotWidget extends AppWidgetProvider {

    public static final String TOGGLE = "dev.csync.jot.TOGGLE";
    public static final String REFRESH = "dev.csync.jot.REFRESH";
    private static final int[] ROW_ID = { R.id.row0, R.id.row1, R.id.row2 };

    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        for (int id : ids) render(context, mgr, id);
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (TOGGLE.equals(action)) {
            Store.toggle(context, intent.getIntExtra("index", -1));
        }
        if (TOGGLE.equals(action) || REFRESH.equals(action)) {
            AppWidgetManager mgr = AppWidgetManager.getInstance(context);
            int[] ids = mgr.getAppWidgetIds(new ComponentName(context, JotWidget.class));
            for (int id : ids) render(context, mgr, id);
        }
        super.onReceive(context, intent);
    }

    /** Ask every placed widget to redraw, after the list changed elsewhere. */
    public static void refresh(Context context) {
        Intent i = new Intent(context, JotWidget.class);
        i.setAction(REFRESH);
        context.sendBroadcast(i);
    }

    private void render(Context context, AppWidgetManager mgr, int widgetId) {
        RemoteViews v = new RemoteViews(context.getPackageName(), R.layout.widget);
        List<Store.Item> items = Store.load(context);

        int open = Store.openCount(context);
        v.setTextViewText(R.id.header, open == 0 ? "Jot: all clear" : "Jot: " + open + " open");

        int shown = 0;
        for (int idx = 0; idx < items.size() && shown < ROW_ID.length; idx++) {
            Store.Item it = items.get(idx);
            if (it.done) continue;
            v.setTextViewText(ROW_ID[shown], "○  " + it.text);
            v.setViewVisibility(ROW_ID[shown], View.VISIBLE);

            Intent toggle = new Intent(context, JotWidget.class);
            toggle.setAction(TOGGLE);
            toggle.putExtra("index", idx);
            toggle.setData(android.net.Uri.parse("jot://toggle/" + idx));
            v.setOnClickPendingIntent(ROW_ID[shown], PendingIntent.getBroadcast(
                    context, idx, toggle, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));
            shown++;
        }
        for (int r = shown; r < ROW_ID.length; r++) {
            v.setViewVisibility(ROW_ID[r], View.GONE);
        }
        if (shown == 0) {
            v.setTextViewText(R.id.row0, "nothing to do");
            v.setViewVisibility(R.id.row0, View.VISIBLE);
        }

        Intent open_app = new Intent(context, MainActivity.class);
        v.setOnClickPendingIntent(R.id.header, PendingIntent.getActivity(
                context, 0, open_app, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));

        mgr.updateAppWidget(widgetId, v);
    }
}
