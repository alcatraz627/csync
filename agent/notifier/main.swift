// csync's Mac notifier: shows a notification for something the mesh agent received, with
// buttons to open it, show it in Finder, or copy its path. A plain click does what --click says.
//
// Posting:  csync-notifier --title T --body B --path PATH [--click copy|open] [--image PATH]
// Exit codes: 0 posted, 3 notifications not allowed, 4 posting failed, 2 bad arguments.
// Launched with no arguments (which macOS does when a notification is clicked), it waits
// for the click to be handed over, acts on it, and quits.

import Cocoa
import UserNotifications

final class Notifier: NSObject, NSApplicationDelegate, UNUserNotificationCenterDelegate {
    func applicationDidFinishLaunching(_ note: Notification) {
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        center.setNotificationCategories([UNNotificationCategory(identifier: "csync-item", actions: [
            UNNotificationAction(identifier: "open", title: "Open", options: [.foreground]),
            UNNotificationAction(identifier: "reveal", title: "Show in Finder", options: [.foreground]),
            UNNotificationAction(identifier: "copy", title: "Copy path", options: []),
        ], intentIdentifiers: [], options: [])])
        let args = CommandLine.arguments
        if args.contains("--title") {
            post(args, center)
        } else {
            // Opened for a click: the response arrives through the delegate shortly.
            DispatchQueue.main.asyncAfter(deadline: .now() + 15) { NSApp.terminate(nil) }
        }
    }

    private func value(_ args: [String], _ flag: String) -> String? {
        guard let i = args.firstIndex(of: flag), i + 1 < args.count else { return nil }
        return args[i + 1]
    }

    private func post(_ args: [String], _ center: UNUserNotificationCenter) {
        guard let title = value(args, "--title") else { exit(2) }
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = value(args, "--body") ?? ""
        if let subtitle = value(args, "--subtitle") { content.subtitle = subtitle }
        content.sound = .default
        if let path = value(args, "--path") {
            content.userInfo = ["path": path, "click": value(args, "--click") ?? "copy"]
            content.categoryIdentifier = "csync-item"
        }
        // macOS moves an attachment's file into its own store, so it gets a copy, never the original.
        if let image = value(args, "--image") {
            let copy = FileManager.default.temporaryDirectory
                .appendingPathComponent(UUID().uuidString + "-" + (image as NSString).lastPathComponent)
            if (try? FileManager.default.copyItem(atPath: image, toPath: copy.path)) != nil,
               let attachment = try? UNNotificationAttachment(identifier: "picture", url: copy) {
                content.attachments = [attachment]
            }
        }
        center.requestAuthorization(options: [.alert, .sound]) { granted, _ in
            guard granted else { exit(3) }
            let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
            center.add(request) { error in exit(error == nil ? 0 : 4) }
        }
    }

    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse,
                                withCompletionHandler done: @escaping () -> Void) {
        let info = response.notification.request.content.userInfo
        if let path = info["path"] as? String {
            let url = URL(fileURLWithPath: path)
            var action = response.actionIdentifier
            if action == UNNotificationDefaultActionIdentifier { action = info["click"] as? String ?? "copy" }
            switch action {
            case "reveal": NSWorkspace.shared.activateFileViewerSelecting([url])
            case "open": NSWorkspace.shared.open(url)
            case "copy":
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(path, forType: .string)
            default: break
            }
        }
        done()
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) { NSApp.terminate(nil) }
    }

    // Shown even if this helper happens to be running when the notification arrives.
    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification,
                                withCompletionHandler done: @escaping (UNNotificationPresentationOptions) -> Void) {
        done([.banner, .sound])
    }
}

let app = NSApplication.shared
let notifier = Notifier()
app.delegate = notifier
app.setActivationPolicy(.accessory)
app.run()
