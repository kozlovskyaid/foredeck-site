#!/usr/bin/env python3
"""Builds foredeck-site.

`privacy.html` and `terms.html` are generated from the app's own
`LegalTexts.swift` rather than written twice. The compliance checklist requires
the embedded texts, the site and the App Privacy answers in App Store Connect
to agree; two hand-maintained copies of the same policy diverge on the first
edit, and the divergence is invisible until a reviewer finds it.

    python3 build.py
"""

import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
LEGAL = HERE.parent / "foredeck" / "Foredeck" / "Settings" / "LegalTexts.swift"

APP_NAME = "Foredeck"
STORE_NAME = "Foredeck — Kubernetes Console"
TAGLINE = "Your Kubernetes clusters, on your phone."
CONTACT = "kozlovskyaid@icloud.com"

STYLE = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #1d1d1f;
    background: linear-gradient(180deg, #10445a 0%, #04161f 100%);
    background-attachment: fixed;
    min-height: 100vh;
}
code, .mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, monospace; }
.hero { text-align: center; padding: 64px 20px 36px; color: #fff; }
.app-icon {
    width: 116px; height: 116px; border-radius: 26px;
    margin: 0 auto 26px; display: block;
    box-shadow: 0 12px 44px rgba(0,0,0,0.42);
}
h1 { font-size: 2.4em; margin-bottom: 12px; font-weight: 700; letter-spacing: -0.02em; }
.tagline { font-size: 1.15em; opacity: 0.9; }
.container { max-width: 900px; margin: 0 auto; padding: 0 20px 56px; }
.shots {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 18px; padding: 8px 0 30px;
}
.shots img {
    width: 100%; height: auto; border-radius: 20px; display: block;
    box-shadow: 0 10px 34px rgba(0,0,0,0.35);
}
.card {
    background: #fff; border-radius: 18px; padding: 36px;
    margin-bottom: 20px; box-shadow: 0 4px 22px rgba(0,0,0,0.16);
}
.card h2 { text-align: center; margin-bottom: 26px; font-size: 1.5em; letter-spacing: -0.01em; }
.features { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 28px; }
.feature { text-align: center; }
.feature-icon { font-size: 34px; margin-bottom: 12px; }
.feature h3 { font-size: 1.05em; margin-bottom: 6px; }
.feature p { font-size: 0.94em; color: #6e6e73; }
.note {
    background: #e6f6fa; border-radius: 12px; padding: 18px 22px;
    color: #0b5a6e; font-weight: 500; text-align: center;
}
.heads-up { background: #fff8e6; color: #7a5600; text-align: left; }
.heads-up strong { display: block; margin-bottom: 6px; }
.heads-up code {
    background: rgba(0,0,0,0.06); padding: 1px 5px; border-radius: 4px; font-size: 0.92em;
}
.legal h2 { text-align: left; font-size: 1.15em; margin: 30px 0 8px; }
.legal h2:first-of-type { margin-top: 0; }
.legal p { margin-bottom: 12px; color: #3a3a3c; white-space: pre-wrap; }
.legal .updated { color: #86868b; font-size: 0.9em; margin-top: 28px; }
.back { display: inline-block; margin-bottom: 22px; color: #0b7fa0; text-decoration: none; font-size: 0.95em; }
.back:hover { text-decoration: underline; }
.links { text-align: center; padding: 12px 20px 40px; }
.links a { color: rgba(255,255,255,0.88); text-decoration: none; margin: 0 14px; font-size: 0.95em; }
.links a:hover { color: #fff; text-decoration: underline; }
.trademark { color: rgba(255,255,255,0.55); font-size: 0.8em; text-align: center;
    max-width: 640px; margin: 0 auto; padding: 0 20px 40px; line-height: 1.5; }
a { color: #0b7fa0; }
"""


def page(title, description, body, *, extra_class=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" href="icon.png">
<style>{STYLE}</style>
</head>
<body class="{extra_class}">
{body}
<div class="links">
    <a href="index.html">Home</a>
    <a href="privacy.html">Privacy</a>
    <a href="terms.html">Terms</a>
    <a href="support.html">Support</a>
</div>
<p class="trademark">
    Kubernetes is a registered trademark of The Linux Foundation. {APP_NAME} is an
    independent client and is not affiliated with, endorsed by or sponsored by
    The Linux Foundation or the Kubernetes project.
    <br>&copy; 2026 Andrew Kozlowskiy
</p>
</body>
</html>
"""


def parse_sections(name):
    """Pulls one `static let <name>: [Section] = [...]` out of LegalTexts.swift.

    Reads the Swift rather than a copy of the prose, so the site cannot drift
    from what ships in the app.
    """
    source = LEGAL.read_text()
    match = re.search(
        rf"static let {name}: \[Section\] = \[(.*?)\n    \]", source, re.S
    )
    if not match:
        sys.exit(f"Could not find {name} in {LEGAL}")

    sections = []
    for block in re.finditer(
        r'title: "(.*?)",\s*body: """\n(.*?)\n\s*"""', match.group(1), re.S
    ):
        title = block.group(1)
        # Swift multiline literals are indented to the closing delimiter; the
        # closing """ here sits at 12 spaces.
        body = "\n".join(line[12:] if line.startswith(" " * 12) else line
                         for line in block.group(2).split("\n"))
        # \(lastUpdated) is the only interpolation in these strings.
        updated = re.search(r'static let lastUpdated = "(.*?)"', source).group(1)
        body = body.replace("\\(lastUpdated)", updated)
        sections.append((title, body.strip()))

    if not sections:
        sys.exit(f"Found {name} but parsed no sections — has the format changed?")
    return sections


def legal_page(filename, heading, sections, description):
    parts = [f'<div class="hero"><h1>{html.escape(heading)}</h1>'
             f'<p class="tagline">{APP_NAME}</p></div>',
             '<div class="container"><div class="card legal">',
             '<a class="back" href="index.html">&larr; Back to Foredeck</a>']
    for title, body in sections:
        parts.append(f"<h2>{html.escape(title)}</h2>")
        parts.append(f"<p>{html.escape(body)}</p>")
    parts.append("</div></div>")
    (HERE / filename).write_text(
        page(f"{heading} — {APP_NAME}", description, "\n".join(parts))
    )
    print(f"  {filename}  ({len(sections)} sections, from LegalTexts.swift)")


FEATURES = [
    ("🧭", "Every resource the cluster serves",
     "Workloads, network, configuration, storage and RBAC — plus your custom "
     "resources, which get the same lists, details and health as anything built in."),
    ("📡", "Live, not refreshed",
     "Foredeck watches the API server and applies changes as they happen, the "
     "way a dashboard on your desk does."),
    ("🔍", "The status that explains itself",
     "CrashLoopBackOff, ImagePullBackOff, Init:0/2, Not Ready — the container-level "
     "reason, not just “Running”."),
    ("📜", "Logs that follow",
     "Stream any container, switch between them, read the previous instance after "
     "a crash, and filter as it scrolls."),
    ("🔐", "Credentials stay on the device",
     "Tokens and client certificates live in the iOS Keychain. Foredeck talks only "
     "to the clusters you add."),
    ("🛡️", "Actions you are allowed to take",
     "Scale, restart, delete and cordon appear only after the cluster confirms your "
     "credential may do them. Any cluster can be marked read-only."),
]


def index_page():
    features = "\n".join(
        f'<div class="feature"><div class="feature-icon">{icon}</div>'
        f'<h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></div>'
        for icon, title, text in FEATURES
    )
    body = f"""
<div class="hero">
    <img class="app-icon" src="icon.png" alt="{APP_NAME} app icon">
    <h1>{APP_NAME}</h1>
    <p class="tagline">{html.escape(TAGLINE)}</p>
</div>

<div class="container">
    <div class="shots">
        <img src="shots/01-overview.jpg" alt="Cluster overview: nodes ready, pods needing attention, recent warnings">
        <img src="shots/02-pods.jpg" alt="Live pod list with per-container status">
        <img src="shots/03-detail.jpg" alt="Pod detail with containers, restarts and events">
        <img src="shots/04-logs.jpg" alt="Streaming container logs with errors highlighted">
    </div>

    <div class="card">
        <h2>What it does</h2>
        <div class="features">{features}</div>
    </div>

    <div class="card">
        <h2>Before you start</h2>
        <div class="note heads-up">
            <strong>Your credentials need to be self-contained.</strong>
            A kubeconfig written by <code>aws eks update-kubeconfig</code> or by
            <code>gcloud</code> does not carry a token — it carries a command to run for
            one, and iOS has no way to run a command-line tool. Client certificates and
            bearer tokens work everywhere. Foredeck says so at import and shows you the
            two <code>kubectl</code> commands that produce a ServiceAccount token.
        </div>
        <p style="height:14px"></p>
        <div class="note heads-up">
            <strong>The cluster has to be reachable from your phone.</strong>
            Control planes are rarely on the public internet. Connect your VPN — Tailscale,
            WireGuard, whatever your company uses — and Foredeck will reach the address in
            your kubeconfig.
        </div>
    </div>

    <div class="card">
        <div class="note">
            Foredeck runs entirely on your device and connects only to the clusters you add
            yourself. Your kubeconfigs, tokens and keys stay here.
        </div>
    </div>
</div>
"""
    (HERE / "index.html").write_text(
        page(f"{STORE_NAME} — {TAGLINE}",
             f"{APP_NAME} is a Kubernetes console for iPhone and iPad: live resource "
             f"lists, streaming logs, and actions your credential is allowed to take. "
             f"Everything stays on your device.",
             body)
    )
    print("  index.html")


def support_page():
    body = f"""
<div class="hero"><h1>Support</h1><p class="tagline">{APP_NAME}</p></div>
<div class="container"><div class="card legal">
<a class="back" href="index.html">&larr; Back to Foredeck</a>

<h2>Get in touch</h2>
<p>Email <a href="mailto:{CONTACT}">{CONTACT}</a>. Include your iOS version, the
Foredeck version from Settings &rarr; About, and what the cluster is — a managed
service, kubeadm, k3s, Talos — because that usually explains it.</p>

<h2>“It cannot reach the API server”</h2>
<p>Check the VPN first. A Kubernetes control plane is normally reachable only from
inside its own network, and from a phone an unreachable network and a wrong address
look identical. Connect the VPN or join the same network, then open the cluster again.</p>

<h2>“This context cannot be used on a phone”</h2>
<p>The kubeconfig asks a command-line tool to produce a token each time it is used —
<code>aws eks get-token</code>, <code>gke-gcloud-auth-plugin</code>, <code>kubelogin</code>
— and iOS cannot run one. Create a ServiceAccount instead:</p>
<p><code>kubectl create serviceaccount foredeck -n default</code>
<br><code>kubectl create clusterrolebinding foredeck --clusterrole=view --serviceaccount=default:foredeck</code>
<br><code>kubectl create token foredeck -n default --duration=8760h</code></p>
<p>Then put that token into a kubeconfig together with the cluster's
<code>server</code> and <code>certificate-authority-data</code>. Foredeck &rarr; Settings
&rarr; “Making a credential that works” writes the whole file for you and lets you copy it.
Use <code>--clusterrole=edit</code> instead of <code>view</code> if you want to be able to
scale, restart and delete.</p>

<h2>“This context points at files on another machine”</h2>
<p>The kubeconfig references paths like <code>/home/you/.kube/client.crt</code>. Re-export
it with the contents inline:</p>
<p><code>kubectl config view --raw --minify --flatten</code></p>

<h2>“The server's certificate is not issued for this address”</h2>
<p>Clusters reached by IP usually present a certificate for the name
<code>kubernetes</code>. Add <code>tls-server-name: kubernetes</code> to the cluster
entry in your kubeconfig.</p>

<h2>A local cluster will not connect</h2>
<p>iOS asks permission before an app may reach addresses on your local network. Allow it
when prompted, or turn it on in iOS Settings &rarr; Foredeck &rarr; Local Network.</p>

<h2>The buttons to change something are missing</h2>
<p>Two possible reasons, both deliberate. The cluster may be marked read-only in Foredeck
— swipe it in the cluster list and open Settings. Otherwise your credential does not have
permission: Foredeck asks the cluster what you may do before offering to do it.</p>

<h2>Something to add?</h2>
<p>Feature requests are welcome at <a href="mailto:{CONTACT}">{CONTACT}</a>. Exec into a
container and port-forward are the two most asked for, and both are on the way.</p>
</div></div>
"""
    (HERE / "support.html").write_text(
        page(f"Support — {APP_NAME}",
             f"Help with {APP_NAME}: reaching a private cluster, making a kubeconfig "
             f"that works on iOS, and TLS troubleshooting.",
             body)
    )
    print("  support.html")


if __name__ == "__main__":
    print(f"Building from {LEGAL.relative_to(HERE.parent)}")
    index_page()
    legal_page("privacy.html", "Privacy Policy", parse_sections("privacyPolicy"),
               f"How {APP_NAME} handles your information: everything stays on your "
               f"device, and it connects only to the clusters you add.")
    legal_page("terms.html", "Terms of Use", parse_sections("termsOfUse"),
               f"Terms of use for {APP_NAME}.")
    support_page()
    print("Done.")
