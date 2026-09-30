# Menu Designer: data access

The designer can read everything menu-related in Supabase and change nothing (Rob, 2026-09-28).

## How to query

Always go through the read-only gateway:

```sql
select public.phg_designer_query($q$  <one SELECT or WITH ... SELECT>  $q$, 500, '<task id or null>');
```

What the gateway guarantees:
- Queries run as role `phg_menu_designer` inside a read-only transaction.
- Up to 5,000 rows are returned, with a 20-second limit.
- Every call is logged in `phg.menu_designer_query_log`.

What the database refuses (tested 2026-09-28):
- writes of any kind, including a write hidden inside a WITH clause;
- a second statement;
- functions that write;
- sequences;
- secrets (`internal_secrets`);
- login and auth data;
- the Menu Studio project token hash.

Never run SQL outside the gateway, and never call `apply_migration`.

## What you can read

| Need | Tables / views |
|---|---|
| **The draft you are designing** | `phg.menu_projects` (`editor_state->'doc'` is the Menu Studio document), `phg.menu_items` (name, `menu_description`, `menu_price`, section, recipe links), `phg.menu_item_prices` |
| **Real ingredients and recipes (the venue's own)** | `phg.recipe_projects`, `phg.recipe_versions` (recipe_name, method, glassware, garnish, ingredients, rationale), `phg.recipe_components` (ingredient, quantity, unit, role), `phg.ingredients` (name, type, category, ABV, aliases), `phg.prep_recipes` / `phg.prep_recipe_versions` / `phg.prep_components` (syrups, infusions, cordials), `phg.ingredient_products` |
| **Classic cocktail specs** (for standard recipes; mark them as standard) | `public.cocktail_reference` (consensus_spec, base_spirit, glassware, garnish, method), `public.cocktail_specs` and `public.cocktail_spec_components` (449 specs), `public.cocktail_spec_terms`, `public.v_cocktail_build_combinations` |
| **Spirits, brands, products** | `public.spirit_lexicon`, `public.brands`, `public.brand_products`, `public.products`, `public.beverage_categories`, `public.product_*` |
| **Costs and sales** (price and margin placement) | `phg.purchase_costs`, `phg.recipe_cost_snapshots`, `phg.menu_engineering_snapshots`, `phg.menu_item_evaluations`, `phg.sales_items`, `phg.sales_item_menu_map` |
| **Library of real menus** (references) | `public.phg_menu_doc_class` (menu type, lists, per-list counts), `public.menu_visual_documents` + `public.menu_visual_pages` (page images), `public.phg_page_text`, `public.staging_menu_extract` (item, price, section, ingredient notes), `public.menus` / `menu_sections` / `menu_items` / `menu_item_brands`, `public.v_menu_composition`, `public.v_cocktail_items_filterable`, `public.v_venue_cocktail_profile`, `public.mv_venue_cocktail_similarity` |
| **Venue and demographics** | `public.accounts` (name, address, ZIP, type), `public.phg_census_zcta` (income, age, 21–34 share, $100k+ households, degree share, Hispanic/Latino share) |
| **Design tasks** | `phg.menu_design_tasks`, `phg.menu_design_proposals` (read-only; you submit through the Coordinator) |

## Example queries

```sql
-- the venue's own recipe for each draft item
select public.phg_designer_query($q$
  select mi.name, mi.menu_description, rv.recipe_name, rv.glassware, rv.garnish,
         (select json_agg(json_build_object('ingredient', i.name, 'qty', rc.quantity, 'unit', rc.unit) order by rc.sort_order)
            from phg.recipe_components rc left join phg.ingredients i on i.id = rc.ingredient_id
           where rc.recipe_version_id = mi.current_recipe_version_id) ingredients
  from phg.menu_items mi where mi.menu_project_id = 'ddc4bb5b-70e6-4581-8aae-1b4042cd75ef'
$q$);

-- the classic spec when the venue has no recipe yet (label it "standard")
select public.phg_designer_query($q$
  select cocktail_name, consensus_spec, glassware, garnish from public.cocktail_reference where cocktail_name = 'Manhattan'
$q$);

-- reference drinks menus near the venue with a tequila list
select public.phg_designer_query($q$
  select d.id, a.account_name, k.lists from public.menu_visual_documents d
  join public.accounts a using (account_id) join public.phg_menu_doc_class k on k.document_id = d.id
  where k.menu_kind = 'beverage' and k.tags @> array['tequila'] and a.postal_code like '100%' limit 20
$q$);
```

## Rules that still apply

- Ingredients come from the venue's own recipes first. If there's no venue recipe, you may use a classic spec, but label it **standard**. If neither exists, flag `missing_ingredients` and ask; never invent one.
- Prices come only from the draft or the inputs.
