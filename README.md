# foredeck-site

The public site for [Foredeck](https://github.com/kozlovskyaid/foredeck), a
Kubernetes console for iPhone and iPad. Served by GitHub Pages at
<https://kozlovskyaid.github.io/foredeck-site/>.

## Do not edit privacy.html or terms.html by hand

They are generated from the app's own `Foredeck/Settings/LegalTexts.swift`:

```sh
python3 build.py
```

The compliance checklist requires the texts embedded in the app, the texts on
this site and the App Privacy answers in App Store Connect to agree. Two
hand-maintained copies of the same policy diverge on the first edit, and the
divergence is invisible until a reviewer finds it — so there is one source, in
the app, and this site is built from it.

`index.html` and `support.html` are written here; re-run `build.py` after
touching either, since it rewrites all four pages.

The script expects the app repo checked out beside this one as `../foredeck`.
