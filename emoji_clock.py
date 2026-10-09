"""EmojiClock — dancing sun/moon emojis for IST + UTC, floating in the top-left corner.

Run:   ~/Documents/EmojiClock/.venv/bin/python ~/Documents/EmojiClock/emoji_clock.py
Use:   drag to move · hover to make them dance faster · right-click for 12h/24h and Quit
"""

import fcntl
import json
import math
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import objc
from AppKit import (
    NSAffineTransform,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSAppearance,
    NSAppearanceNameVibrantDark,
    NSAttributedString,
    NSBackingStoreBuffered,
    NSBaselineOffsetAttributeName,
    NSBezierPath,
    NSColor,
    NSCompositingOperationSourceAtop,
    NSCompositingOperationSourceOver,
    NSFont,
    NSFontAttributeName,
    NSFontWeightBold,
    NSFontWeightHeavy,
    NSFontWeightMedium,
    NSForegroundColorAttributeName,
    NSGraphicsContext,
    NSImage,
    NSMakeRect,
    NSMenu,
    NSMenuItem,
    NSMutableAttributedString,
    NSRectFillUsingOperation,
    NSObject,
    NSScreen,
    NSTimer,
    NSTrackingActiveAlways,
    NSTrackingArea,
    NSTrackingMouseEnteredAndExited,
    NSView,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialHUDWindow,
    NSVisualEffectStateActive,
    NSVisualEffectView,
    NSWindow,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
    NSFloatingWindowLevel,
)
from Foundation import NSRunLoop, NSRunLoopCommonModes

SETTINGS_FILE = Path(__file__).with_name("settings.json")
WIDTH, HEIGHT, RADIUS = 280, 140, 20


def rgb(r, g, b, a=1.0):
    return NSColor.colorWithRed_green_blue_alpha_(r, g, b, a)


def text(s, font, color):
    return NSAttributedString.alloc().initWithString_attributes_(
        s, {NSFontAttributeName: font, NSForegroundColorAttributeName: color}
    )


_emoji_images = {}


def emoji_image(emoji, tint=None):
    """Render an emoji to an image once and cache it. `tint` recolors it while keeping its shading."""
    key = (emoji, tint is not None)
    if key not in _emoji_images:
        s = NSAttributedString.alloc().initWithString_attributes_(emoji, {NSFontAttributeName: EMOJI_FONT})
        size = s.size()
        img = NSImage.alloc().initWithSize_(size)
        img.lockFocus()
        s.drawAtPoint_((0, 0))
        if tint is not None:
            tint.set()  # paint only where the emoji already has pixels
            NSRectFillUsingOperation(NSMakeRect(0, 0, size.width, size.height), NSCompositingOperationSourceAtop)
        img.unlockFocus()
        _emoji_images[key] = img
    return _emoji_images[key]


def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except (OSError, ValueError):
        return {}


class Zone:
    def __init__(self, label, tz_name, color):
        self.label = label
        self.tz = ZoneInfo(tz_name)
        self.color = color

    def now(self):
        return datetime.now(self.tz)

    @staticmethod
    def dancer(dt):
        """☀️ in the daytime (6 AM–6 PM), 🌙 at night."""
        return "☀️" if 6 <= dt.hour < 18 else "🌙"

    @staticmethod
    def clock_face(dt):
        """Clock-face emoji matching the time (🕐…🕛, 🕜…🕧)."""
        hour12 = dt.hour % 12 or 12
        return chr(0x1F550 + hour12 - 1 + (12 if dt.minute >= 30 else 0))


ZONES = [
    Zone("IST", "Asia/Kolkata", rgb(1.0, 0.55, 0.2)),
    Zone("UTC", "UTC", rgb(0.3, 0.6, 1.0)),
]

WHITE = NSColor.whiteColor()
MOON_BLUE = rgb(0.2, 0.5, 1.0, 0.85)  # last number = tint strength (0–1)
EMOJI_FONT = NSFont.systemFontOfSize_(44)
TIME_FONT = NSFont.monospacedDigitSystemFontOfSize_weight_(17, NSFontWeightBold)
AMPM_FONT = NSFont.systemFontOfSize_weight_(10, NSFontWeightBold)
PILL_FONT = NSFont.systemFontOfSize_weight_(10, NSFontWeightHeavy)
DATE_FONT = NSFont.systemFontOfSize_weight_(10, NSFontWeightMedium)


class ClockView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(ClockView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.use24h = load_settings().get("use24h", False)
        self.hovering = False
        self.speed = 1.0   # eases toward 2.2 while hovering
        self.phase = 0.0   # accumulated dance phase
        self.last_frame = time.monotonic()
        return self

    # --- window behaviour ---------------------------------------------------
    def isFlipped(self):
        return True  # y grows downward, like a web page

    def mouseDownCanMoveWindow(self):
        return True

    def updateTrackingAreas(self):
        for area in self.trackingAreas():
            self.removeTrackingArea_(area)
        self.addTrackingArea_(
            NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                self.bounds(), NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways, self, None
            )
        )

    def mouseEntered_(self, event):
        self.hovering = True

    def mouseExited_(self, event):
        self.hovering = False

    # --- drawing ------------------------------------------------------------
    def drawRect_(self, dirty):
        now = time.monotonic()
        self.speed += ((2.2 if self.hovering else 1.0) - self.speed) * 0.08
        self.phase += (now - self.last_frame) * self.speed
        self.last_frame = now

        bounds = self.bounds()
        w, h = bounds.size.width, bounds.size.height

        # Subtle glass edge.
        WHITE.colorWithAlphaComponent_(0.18).setStroke()
        edge = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(0.5, 0.5, w - 1, h - 1), RADIUS, RADIUS
        )
        edge.setLineWidth_(1)
        edge.stroke()

        # Divider between the two clocks.
        WHITE.colorWithAlphaComponent_(0.12).setFill()
        NSBezierPath.fillRect_(NSMakeRect(w / 2 - 0.5, 18, 1, h - 36))

        col = w / len(ZONES)
        for i, zone in enumerate(ZONES):
            self.draw_zone(zone, cx=col * (i + 0.5), offset=i * math.pi / 2)

    def draw_zone(self, zone, cx, offset):
        dt = zone.now()
        t = self.phase + offset
        top_of_hour = dt.minute == 0 and dt.second < 10

        # Dance: hop, wiggle, squash on landing — and a full spin for the first 10s of each hour.
        hop = abs(math.sin(t * 3.2))
        dy = -hop * 10
        angle = t * 6 if top_of_hour else math.sin(t * 4.5) * 0.25
        squash = 1 + (1 - hop) * 0.14

        # Shadow that shrinks as the emoji jumps.
        shadow_w = 34 * (1 - hop * 0.45)
        NSColor.blackColor().colorWithAlphaComponent_(0.35 - hop * 0.2).setFill()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx - shadow_w / 2, 60, shadow_w, 6)).fill()

        dancer = Zone.dancer(dt)
        img = emoji_image(dancer, MOON_BLUE if dancer == "🌙" else None)
        size = img.size()
        ctx_transform = NSAffineTransform.transform()
        ctx_transform.translateXBy_yBy_(cx, 36 + dy)
        ctx_transform.rotateByRadians_(angle)
        ctx_transform.scaleXBy_yBy_(squash, 1 / squash)
        NSGraphicsContext.saveGraphicsState()
        ctx_transform.concat()
        img.drawInRect_fromRect_operation_fraction_respectFlipped_hints_(
            NSMakeRect(-size.width / 2, -size.height / 2, size.width, size.height),
            NSMakeRect(0, 0, 0, 0), NSCompositingOperationSourceOver, 1.0, True, None,
        )
        NSGraphicsContext.restoreGraphicsState()

        # Zone pill: 🕞 IST / 🕙 UTC
        pill_text = text(f"{Zone.clock_face(dt)} {zone.label}", PILL_FONT, WHITE)
        ps = pill_text.size()
        pill = NSMakeRect(cx - ps.width / 2 - 8, 72, ps.width + 16, ps.height + 3)
        zone.color.colorWithAlphaComponent_(0.85).setFill()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            pill, pill.size.height / 2, pill.size.height / 2
        ).fill()
        pill_text.drawAtPoint_((pill.origin.x + 8, pill.origin.y + 1.5))

        # Time, with a small AM/PM suffix in 12-hour mode.
        clock = dt.strftime("%H:%M:%S" if self.use24h else "%-I:%M:%S")
        time_str = NSMutableAttributedString.alloc().initWithAttributedString_(text(clock, TIME_FONT, WHITE))
        if not self.use24h:
            time_str.appendAttributedString_(
                NSAttributedString.alloc().initWithString_attributes_(
                    " " + dt.strftime("%p"),
                    {
                        NSFontAttributeName: AMPM_FONT,
                        NSForegroundColorAttributeName: zone.color.blendedColorWithFraction_ofColor_(0.35, WHITE),
                        NSBaselineOffsetAttributeName: 1,
                    },
                )
            )
        time_str.drawAtPoint_((cx - time_str.size().width / 2, 93))

        date = text(dt.strftime("%a, %-d %b"), DATE_FONT, WHITE.colorWithAlphaComponent_(0.6))
        date.drawAtPoint_((cx - date.size().width / 2, 116))

    # --- right-click menu ---------------------------------------------------
    def menuForEvent_(self, event):
        menu = NSMenu.alloc().init()
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("24-hour time", "toggle24h:", "")
        item.setTarget_(self)
        item.setState_(1 if self.use24h else 0)
        menu.addItem_(item)
        menu.addItem_(NSMenuItem.separatorItem())
        menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit Emoji Clock", "terminate:", "q"))
        return menu

    def toggle24h_(self, sender):
        self.use24h = not self.use24h
        SETTINGS_FILE.write_text(json.dumps({"use24h": self.use24h}))


def rounded_mask(rect):
    NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, RADIUS, RADIUS).fill()
    return True


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        vis = (NSScreen.mainScreen() or NSScreen.screens()[0]).visibleFrame()
        x = vis.origin.x + 12
        y = vis.origin.y + vis.size.height - HEIGHT - 12
        frame = NSMakeRect(0, 0, WIDTH, HEIGHT)

        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, WIDTH, HEIGHT), NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        self.window.setMovableByWindowBackground_(True)

        # Frosted-glass background with rounded corners.
        glass = NSVisualEffectView.alloc().initWithFrame_(frame)
        glass.setMaterial_(NSVisualEffectMaterialHUDWindow)
        glass.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        glass.setState_(NSVisualEffectStateActive)
        glass.setAppearance_(NSAppearance.appearanceNamed_(NSAppearanceNameVibrantDark))
        glass.setMaskImage_(NSImage.imageWithSize_flipped_drawingHandler_((WIDTH, HEIGHT), False, rounded_mask))

        self.view = ClockView.alloc().initWithFrame_(frame)
        glass.addSubview_(self.view)
        self.window.setContentView_(glass)
        self.window.orderFrontRegardless()

        self.timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
            1 / 30, self, "tick:", None, True
        )
        NSRunLoop.mainRunLoop().addTimer_forMode_(self.timer, NSRunLoopCommonModes)

    def tick_(self, timer):
        self.view.setNeedsDisplay_(True)


if __name__ == "__main__":
    # Single instance: if another clock already holds the lock, exit quietly.
    _lock = open("/tmp/emojiclock.lock", "w")
    try:
        fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("EmojiClock is already running.")

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)  # no Dock icon
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()
