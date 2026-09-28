
## Round 3

item | before | after | source (table + id)
--- | --- | --- | ---
Margarita | "...agave syrup; lime wheel. Shaken, served on the rocks over fresh ice." | "...agave syrup. Shaken, served over fresh ice." | draft doc components + serve_format ("Shake with ice and strain over fresh ice"), phg.menu_items 14555870-57d2-4dd1-9722-bfd1cff8f6ce / recipe_versions f06abb74-762a-4f89-81b2-76a9e4714f3c: no garnish component, so "lime wheel" removed; "on the rocks" redundant
Manhattan | "...Stirred, served up in a coupe." | "...Stirred and served up." | draft doc serve_format "Stir with ice and strain", menu_items bf732e78-8130-474b-af6f-bf8a25f0122a / recipe_versions 9fb77eaa-c5eb-477c-8e21-acbc89a0e942: no glassware, so "coupe" removed; Cocktail Cherry (Garnish) kept
Brown Butter Old Fashioned | "...aromatic bitters; orange peel. Stirred..." | "...aromatic bitters. Stirred, served over a large cube." | draft doc components, menu_items 0cc4e912-1640-4410-b5b0-b1c6ebae0ee3 / recipe_versions 7095fd3d-58fb-43f5-8e8f-1a0afadeafa7: no garnish component, so "orange peel" removed
House Daiquiri | "...demerara syrup; lime coin. Shaken, served up in a coupe." | "...demerara syrup. Shaken and served up." | draft doc serve_format "Shake with ice and fine strain", menu_items 44dcba6e-20db-46b2-b887-626ed63cf0de / recipe_versions 14d45e57-72fa-4d23-8274-24e5c80e4b12: no garnish or glassware, so "lime coin" and "coupe" removed

Note: the gateway join menu_items->recipe_versions returned 0 rows for this project (menu_items has no recipe_version_id column). The draft doc build/draft_doc.json (phg.recipe_version_id per item) was used as the source.

### Round 3 edit REVERTED by the Coordinator
The editor's gateway join used a non-existent column (menu_items has current_recipe_version_id, not
recipe_version_id), its lookup returned 0 rows, and it removed garnish/glass wording that IS in phg.recipe_versions
(verified by three round-2 accuracy reviewers, gateway log_ids 74, 88, 90, 91: Margarita lime wheel / rocks,
Old Fashioned orange peel / large cube, Daiquiri lime coin / coupe, Manhattan cocktail cherry / coupe). The designer's
round-3 copy is restored. Correct join: phg.menu_items.current_recipe_version_id = phg.recipe_versions.id.
