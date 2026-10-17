import SwiftUI
import UIKit
import WebKit

struct BiteLogWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        configuration.userContentController.add(context.coordinator, name: "healthkit")

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.isOpaque = false
        webView.backgroundColor = .clear
        context.coordinator.webView = webView

        let bundledURL = Bundle.main.url(forResource: "index", withExtension: "html")
            ?? Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "Resources")

        if let url = bundledURL {
            webView.loadFileURL(url, allowingReadAccessTo: Bundle.main.bundleURL)
        } else {
            webView.loadHTMLString("<h1>BiteLog</h1><p>Could not find the bundled app UI.</p>", baseURL: nil)
        }
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    static func dismantleUIView(_ uiView: WKWebView, coordinator: Coordinator) {
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: "healthkit")
    }

    final class Coordinator: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
        weak var webView: WKWebView?

        func webView(
            _ webView: WKWebView,
            decidePolicyFor navigationAction: WKNavigationAction,
            decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
        ) {
            guard let url = navigationAction.request.url,
                  url.scheme?.lowercased() == "mailto" else {
                decisionHandler(.allow)
                return
            }

            decisionHandler(.cancel)
            UIApplication.shared.open(url, options: [:]) { opened in
                guard !opened else { return }
                DispatchQueue.main.async {
                    webView.evaluateJavaScript("window.emailOpenFailed && window.emailOpenFailed();", completionHandler: nil)
                }
            }
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            sendBridgeState("ready")
            HealthKitManager.shared.authorizationRequestStatus { [weak self] result in
                DispatchQueue.main.async {
                    switch result {
                    case .success(let status): self?.sendAuthorizationStatus(status)
                    case .failure(let error): self?.send(error: error.localizedDescription)
                    }
                }
            }
        }

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == "healthkit",
                  let body = message.body as? [String: Any],
                  let action = body["action"] as? String else { return }

            switch action {
            case "request":
                sendBridgeState("requesting")
                HealthKitManager.shared.requestAuthorization { [weak self] result in
                    DispatchQueue.main.async {
                        switch result {
                        case .success:
                            self?.sendBridgeState("authorized")
                            self?.fetchHealthSnapshot()
                        case .failure(let error):
                            self?.send(error: error.localizedDescription)
                        }
                    }
                }
            case "status":
                HealthKitManager.shared.authorizationRequestStatus { [weak self] result in
                    DispatchQueue.main.async {
                        switch result {
                        case .success(let status): self?.sendAuthorizationStatus(status)
                        case .failure(let error): self?.send(error: error.localizedDescription)
                        }
                    }
                }
            default:
                fetchHealthSnapshot()
            }
        }

        private func fetchHealthSnapshot() {
            sendBridgeState("syncing")
            HealthKitManager.shared.snapshotForToday { [weak self] snapshot in
                DispatchQueue.main.async {
                    self?.send(snapshot: snapshot)
                    self?.sendBridgeState("synced")
                }
            }
        }

        private func send(snapshot: BiteLogHealthSnapshot) {
            guard let webView,
                  let data = try? JSONEncoder().encode(snapshot),
                  let json = String(data: data, encoding: .utf8) else { return }
            webView.evaluateJavaScript("window.receiveHealthData && window.receiveHealthData(\(json));") { _, error in
                if let error { print("BiteLog HealthKit bridge error: \(error.localizedDescription)") }
            }
        }

        private func sendBridgeState(_ state: String) {
            webView?.evaluateJavaScript("window.healthBridgeState && window.healthBridgeState('\(escape(state))');", completionHandler: nil)
        }

        private func sendAuthorizationStatus(_ status: String) {
            webView?.evaluateJavaScript("window.healthAuthorizationStatus && window.healthAuthorizationStatus('\(escape(status))');", completionHandler: nil)
        }

        private func send(error: String) {
            webView?.evaluateJavaScript("window.healthSyncFailed && window.healthSyncFailed('\(escape(error))');", completionHandler: nil)
        }

        private func escape(_ string: String) -> String {
            string
                .replacingOccurrences(of: "\\", with: "\\\\")
                .replacingOccurrences(of: "'", with: "\\'")
                .replacingOccurrences(of: "\n", with: "\\n")
        }
    }
}
