#!/data/data/com.termux/files/usr/bin/bash
# Build the Jot APK entirely on the phone: aapt for resources, ecj to compile,
# d8 to dex, apksigner to sign. No Gradle, no network.
set -e
cd "$(dirname "$0")"
OUT=build
rm -rf "$OUT"
mkdir -p "$OUT/gen" "$OUT/classes"

echo "== resources + R.java"
aapt package -f -m \
  -M AndroidManifest.xml \
  -S res \
  -I android.jar \
  -J "$OUT/gen" \
  -F "$OUT/jot.unsigned.apk"

echo "== compile java"
# The Termux ecj wrapper already sets a compliance level, so passing one here
# is rejected as a duplicate. The sources need nothing newer than Java 7.
ecj -nowarn \
  -cp android.jar \
  -d "$OUT/classes" \
  $(find src "$OUT/gen" -name '*.java')

echo "== dex"
d8 --min-api 26 --lib android.jar --output "$OUT" $(find "$OUT/classes" -name '*.class')

echo "== add dex to apk"
cd "$OUT"
aapt add -f jot.unsigned.apk classes.dex >/dev/null
cd ..

echo "== keystore"
if [ ! -f jot.keystore ]; then
  keytool -genkeypair -v -keystore jot.keystore -storepass jotjot -keypass jotjot \
    -alias jot -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=csync jot, OU=dev, O=csync, L=NA, S=NA, C=NA" >/dev/null 2>&1
fi

echo "== sign"
apksigner sign --ks jot.keystore --ks-pass pass:jotjot --key-pass pass:jotjot \
  --min-sdk-version 26 \
  --out "$OUT/jot.apk" "$OUT/jot.unsigned.apk"

apksigner verify "$OUT/jot.apk" && echo "== signature verifies"
ls -l "$OUT/jot.apk"
echo "== JOT_BUILD_OK $(pwd)/$OUT/jot.apk"
