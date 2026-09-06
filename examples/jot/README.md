# Jot

A tasks list with a home-screen widget, built to prove that csync can carry a
whole development loop to an Android phone. It was written on a Mac, pushed to a
Redmi Note 10 Pro over csync, and compiled on the phone's own CPU with the
Termux toolchain. No Gradle, no Android Studio, no Android SDK on the Mac.

The widget shows the three oldest open tasks and a count. Tapping a row ticks
that task off and the widget redraws. Tapping the header opens the app.

## Building it

The phone needs the toolchain once:

```
pkg install -y aapt apksigner d8 ecj
```

`build.sh` then does the five steps by hand: `aapt` compiles the resources and
generates `R.java`, `ecj` compiles the sources, `d8` produces `classes.dex`,
`aapt add` puts the dex in the archive, and `apksigner` signs it. It needs an
`android.jar` for API 33 beside it, which is not in this repo because of its
size.

Two things the phone taught us, both in `build.sh` comments: the Termux `ecj`
wrapper sets its own compliance level, so passing `-source`, `-target`, or
`-1.8` is rejected; and `d8` wants `--min-api` to match the manifest.

## Installing it

Termux cannot install an APK, so that one step needs either ADB or a tap on the
phone's own package installer. Everything else, including the edit, rebuild and
re-run loop, runs over csync.
