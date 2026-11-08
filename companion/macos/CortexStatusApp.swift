import AppKit
import Foundation

private let boardHost = "127.0.0.1"
private let boardPort = 65200
private let boardURL = URL(string: "http://127.0.0.1:65200/")!
private let serviceIdentifier = "cortex-status-board"
private let assignmentIdentifier = "C004"
private let protocolVersion = 1
private let startupTimeout: TimeInterval = 12

private final class HTTPReply: @unchecked Sendable {
    private let lock = NSLock()
    private var storedResponse: URLResponse?
    private var storedData: Data?

    func set(response: URLResponse?, data: Data?) {
        lock.lock()
        storedResponse = response
        storedData = data
        lock.unlock()
    }

    func get() -> (URLResponse?, Data?) {
        lock.lock()
        defer { lock.unlock() }
        return (storedResponse, storedData)
    }
}

@main
private struct CortexStatusApp {
    static func main() {
        let application = NSApplication.shared
        let delegate = AppDelegate()
        application.delegate = delegate
        application.run()
    }
}

private final class AppDelegate: NSObject, NSApplicationDelegate {
    private let launchQueue = DispatchQueue(label: "com.redhorse.cortex-status.launch")
    private var serverProcess: Process?

    func applicationDidFinishLaunching(_ notification: Notification) {
        installApplicationMenu()
        enqueueOpen()
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows: Bool) -> Bool {
        enqueueOpen()
        return true
    }

    private func installApplicationMenu() {
        let mainMenu = NSMenu()
        let applicationItem = NSMenuItem()
        let applicationMenu = NSMenu(title: "Cortex Status")
        applicationMenu.addItem(
            withTitle: "Quit Cortex Status",
            action: #selector(NSApplication.terminate(_:)),
            keyEquivalent: "q"
        )
        applicationItem.submenu = applicationMenu
        mainMenu.addItem(applicationItem)
        NSApplication.shared.mainMenu = mainMenu
    }

    private func enqueueOpen() {
        launchQueue.async { [weak self] in
            guard let self else { return }
            guard self.ensureBoardReady() else {
                DispatchQueue.main.async { self.showFailure() }
                return
            }
            DispatchQueue.main.async {
                if !NSWorkspace.shared.open(boardURL) {
                    self.showFailure()
                }
            }
        }
    }

    private var supportDirectory: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/Cortex Status Board", isDirectory: true)
    }

    private func identityToken() -> String? {
        let tokenURL = supportDirectory.appendingPathComponent("server.identity")
        guard let value = try? String(contentsOf: tokenURL, encoding: .utf8) else { return nil }
        let token = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard token.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil else { return nil }
        return token
    }

    private func readHTTP(_ path: String, timeout: TimeInterval) -> (HTTPURLResponse, Data)? {
        guard var requestURL = URLComponents(string: "http://\(boardHost):\(boardPort)") else { return nil }
        requestURL.path = path
        guard let url = requestURL.url else { return nil }

        var request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: timeout)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        let semaphore = DispatchSemaphore(value: 0)
        let reply = HTTPReply()
        let task = URLSession.shared.dataTask(with: request) { data, response, _ in
            reply.set(response: response, data: data)
            semaphore.signal()
        }
        task.resume()
        guard semaphore.wait(timeout: .now() + timeout) == .success else {
            task.cancel()
            return nil
        }
        let (response, data) = reply.get()
        guard let response = response as? HTTPURLResponse, let data else { return nil }
        return (response, data)
    }

    private func validHeaders(_ response: HTTPURLResponse) -> Bool {
        response.statusCode == 200
            && response.value(forHTTPHeaderField: "Content-Type")?.lowercased().contains("application/json") == true
            && response.value(forHTTPHeaderField: "Cache-Control") == "no-store"
            && response.value(forHTTPHeaderField: "X-Content-Type-Options") == "nosniff"
    }

    private func isHealthy() -> Bool {
        guard let token = identityToken(),
              let (healthResponse, healthData) = readHTTP("/api/health", timeout: 1.0),
              validHeaders(healthResponse),
              let health = try? JSONSerialization.jsonObject(with: healthData) as? [String: Any],
              health["serviceId"] as? String == serviceIdentifier,
              health["assignmentId"] as? String == assignmentIdentifier,
              health["protocolVersion"] as? Int == protocolVersion,
              health["identityToken"] as? String == token,
              let (statusResponse, statusData) = readHTTP("/api/status", timeout: 1.0),
              validHeaders(statusResponse),
              statusData.count <= 1_048_576,
              let status = try? JSONSerialization.jsonObject(with: statusData) as? [String: Any],
              Set(status.keys) == Set(["schemaVersion", "generatedAt", "chief", "assignments"]),
              status["schemaVersion"] as? Int == 1,
              let assignments = status["assignments"] as? [[String: Any]],
              assignments.contains(where: { $0["assignmentId"] as? String == assignmentIdentifier }) else {
            return false
        }
        return true
    }

    private func startBoardServer() -> Bool {
        let nodePath = Bundle.main.infoDictionary?["CortexNodePath"] as? String
        let serverURL = supportDirectory.appendingPathComponent("server.mjs")
        guard let nodePath,
              nodePath.hasPrefix("/"),
              FileManager.default.isExecutableFile(atPath: nodePath),
              FileManager.default.fileExists(atPath: serverURL.path),
              identityToken() != nil else {
            return false
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: nodePath)
        process.arguments = [serverURL.path]
        process.currentDirectoryURL = supportDirectory
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        do {
            try process.run()
            serverProcess = process
            return true
        } catch {
            return false
        }
    }

    private func ensureBoardReady() -> Bool {
        if isHealthy() { return true }
        guard startBoardServer() else {
            return waitForHealthyServer()
        }
        return waitForHealthyServer()
    }

    private func waitForHealthyServer() -> Bool {
        let deadline = Date().addingTimeInterval(startupTimeout)
        while Date() < deadline {
            if isHealthy() { return true }
            Thread.sleep(forTimeInterval: 0.2)
        }
        return false
    }

    private func showFailure() {
        NSApplication.shared.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = "Cortex Status could not open"
        alert.informativeText = "The local C004 board did not pass its identity and status checks. No other service was opened."
        alert.alertStyle = .warning
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
}
