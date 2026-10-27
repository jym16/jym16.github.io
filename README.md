# Personal homepage

Jun Yamamoto's academic website, built with Quarto.

## Build and check

Use Quarto 1.6 and Python 3.10 or newer. The website itself needs no npm packages.

```sh
quarto render
python3 .github/validate_site.py
quarto preview --no-browser --port 5343
```

GitHub Pages runs the same validation before uploading the generated site. The
check covers page languages, local links and anchors, CSS resources, the search
index, and accidental inclusion of private or source files.

## Content and layout

The six English pages are at the repository root. Japanese Home and Research
live in `ja/`, inheriting `lang: ja` from `ja/_metadata.yml`. Keep research claims,
publication links, and homepage news aligned between languages.

Japanese Research keeps `lang: ja` but uses `_filters/english-citations.lua`
to format citations and references in English. Keep its `citeproc: false` and
filter settings together: the filter runs Pandoc's citation processor once with
`en-US`, then restores the document language.

`_quarto.yml` defines the eight rendered pages, shared content grid, and native
navigation. The navbar's language variants are intentional: CSS shows the
appropriate links without JavaScript. Keep English destinations first, Japanese
destinations next, and language-switch destinations last, because Quarto marks
the first matching URL active. Language tabs connect matching Home and Research
pages; other English pages link to Japanese Home.

`_includes/profile-links.html` supplies the shared social icons. Each homepage
keeps its own localized accessibility label. Publication icon styles load only
on the Publications page.

## Figures and public resources

Figure builders, retained data, and provenance stay in the ignored local
`scripts/` directory. They are not included in the public repository and are not
needed to build the website. Quarto uses the prebuilt figure exports in
`assets/images/research/`.

Quarto discovers linked images and styles automatically. The only additional
resources copied explicitly are the public CV, PDF downloads in `assets/files/`,
fonts, and their licenses. Resource globs start with `/` to prevent matching
folders inside local archives. Keep private academic documents, unpublished details, and local archives
outside public asset directories. `_backup/` is excluded from Git and rendering.

Generated directories such as `_site/`, `.quarto/`, and `*_files/` are ignored and
can be recreated. They are not source files.

