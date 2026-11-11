# wmg: Wikimedia groups, searchable

Searchable data published by Wikimedia groups, one view per group. Live at https://wmfr-search.toolforge.org (deployed by [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) on every push to `main`).

Also the `wmg` module of [lingua-deck](https://github.com/hugolpz/lingua-deck) (git submodule at `src/modules/wmg`, route `/transparency/wmfr`).

| Path                                   | Content                                                                                                                                                                       |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `index.html`, `src/`, `vite.config.js` | The app: home page listing the groups, one route per group (`#/wmfr`). `src/components/` holds standalone stand-ins for lingua-deck components the views import through `@/`. |
| `src/groups.js`                        | Registry of the groups                                                                                                                                                        |
| `module/<group>/`                      | Everything of one group: view, components, data, pipeline scripts, sources, README                                                                                            |

## Groups

- [`module/wmfr`](module/wmfr/README.md): Wikimédia France spendings.

## Add a group

1. Create `module/<slug>/` with a `<Name>View.vue` (and its data, scripts, README).
2. Add it to `src/groups.js`. In lingua-deck, add the route to `src/router/index.js` too.

## Development

```bash
npm install
npm run dev
npm run build
npm run data:wmfr      # refresh the WMFR data, see module/wmfr/README.md
```

## CI

`git push` to github triggers `.github/workflows/deploy.yml` which runs the build and deploys it to Toolforge.

## Toolforge

```bash
ssh <your-username>@login.toolforge.org
become wm-docs                      # switch to the tool account
ls -l ~/public_html/index.html      # check that the deploy landed
toolforge webservice php8.2 start   # serves ~/public_html
toolforge webservice status         # should say "Running"
```
