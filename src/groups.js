// One entry per Wikimedia group. To add one: create module/<slug>/ with a view and list it here.
export const groups = [
  {
    slug: 'wmfr',
    name: 'Wikimédia France',
    description: 'Spendings published by the chapter, filterable by project, person, date…',
    view: () => import('../module/wmfr/WmfrView.vue'),
  },
]
