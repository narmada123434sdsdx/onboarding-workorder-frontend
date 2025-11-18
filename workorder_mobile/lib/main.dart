import 'dart:io';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:url_launcher/url_launcher_string.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Enable hybrid composition (required for Android)
  if (Platform.isAndroid) {
    WebViewPlatform.instance = AndroidWebViewPlatform();
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: WebApp(),
    );
  }
}

class WebApp extends StatefulWidget {
  const WebApp({super.key});

  @override
  State<WebApp> createState() => _WebAppState();
}

class _WebAppState extends State<WebApp> {
  late final WebViewController controller;
  bool isLoading = true;

  // 👉 Your React website URL here
  final String webUrl = "https://onboarding-workorder-frontend.vercel.app";

  @override
  void initState() {
    super.initState();

    controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(false)
      ..setUserAgent(
        "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120 Mobile Safari/537.36",
      )
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (NavigationRequest request) {
            Uri uri = Uri.parse(request.url);

            print("🔗 NAVIGATE: ${request.url}");

            // 👉 Allow all internal React routes
            if (uri.host.contains("onboarding-workorder-frontend.vercel.app")) {
              return NavigationDecision.navigate;
            }

            // 👉 Open external links in browser
            launchUrlString(
              request.url,
              mode: LaunchMode.externalApplication,
            );
            return NavigationDecision.prevent;
          },

          // When page finished loading
          onPageFinished: (_) async {
            setState(() => isLoading = false);

            // 👉 Fix target="_blank" so links open within WebView
            await controller.runJavaScript(
              """
              document.querySelectorAll('a[target="_blank"]').forEach(a => {
                a.removeAttribute('target');
              });
              """
            );
          },
        ),
      )
      ..loadRequest(Uri.parse(webUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          WebViewWidget(controller: controller),

          // Loading indicator
          if (isLoading)
            const Center(
              child: CircularProgressIndicator(color: Colors.blue),
            ),
        ],
      ),
    );
  }
}
