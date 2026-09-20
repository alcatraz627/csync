# pihub

A small web console for a Raspberry Pi, reachable from any browser on the LAN.
Two tabs today: a live camera preview with a capture button, and a system
readout. It installs no packages.

```
http://<pi>:8642
```

## What makes it cheap to leave installed

systemd owns the listening socket, so the port answers from boot with no process
running at all. The first connection starts the service, and the service exits
itself after five idle minutes. Watching the stream counts as use, so it stays up
while you are looking at it and stands down shortly after you close the tab.

```
pihub.socket    enabled, always listening, costs one file descriptor
pihub.service   exists only while someone is using it
```

Measured on a Pi 4: 0.34 s from a dead service to a served response.

## Install

From a machine that can reach the Pi:

```
csync push rpi examples/pihub /home/<user>/pihub-src --overwrite
csync run  rpi -- sudo bash /home/<user>/pihub-src/pihub/install.sh
```

Or on the Pi itself, `sudo bash install.sh`. Set `PIHUB_PORT` to move it off 8642.

## Camera

Uses `picamera2`, which ships with Raspberry Pi OS. One encoder runs inside the
camera pipeline and writes JPEGs to a shared buffer that every viewer reads, so
two open tabs do not queue behind each other on the hardware. Photos are the
latest frame written to `~/pihub-photos`, which means there is no second capture
path and no mode switching to go wrong.

When the camera cannot start, the page says so and shows what `rpicam-hello`
reports about the hardware, rather than showing a broken image.

## Endpoints

| Path | What it returns |
|---|---|
| `/` | the page |
| `/api/stream` | `multipart/x-mixed-replace` MJPEG, roughly 8 fps |
| `/api/frame` | one JPEG, or a 503 carrying the reason |
| `/api/capture` | POST; saves a photo and returns its name |
| `/api/photos` | the 24 most recent photos |
| `/api/sysinfo` | model, kernel, temperature, throttling, memory, disks |
| `/api/camera` | whether the camera is up, and what the Pi says about it |

## Development

```
python3 server.py --port 8642
```

Standalone mode binds the port itself. Under systemd it adopts the inherited
socket instead.

## Known

The preview is whatever way the camera is physically mounted; there is no
rotation control yet. `/api/sysinfo` surfaces `throttled` from `vcgencmd` as a
raw hex word, which is honest but not yet readable.
