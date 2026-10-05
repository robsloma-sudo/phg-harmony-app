-- PROPOSAL ONLY - not applied. Review, then apply as migration 'garnish_catalogue_v1'.
-- Garnish catalogue + placement rules for the Cocktail Design view and the Blender builder.
-- phg.drink_visuals.garnish stores an ordered list using this grammar:
--   [{"type":"orange_half_moon","count":1,"placement":"pick"},{"type":"cherry","count":1,"placement":"pick"}]
-- Pick items are skewered on ONE pick in list order. count expands in place ("2 cherries" = count 2).

create table if not exists phg.garnish_types (
  garnish_key text primary key,
  name text not null,
  kind text not null check (kind in ('fruit','citrus_cut','citrus_peel','herb','olive_brine','other')),
  allowed_placements text[] not null,
  default_placement text not null,
  ingredient_id uuid references phg.ingredients(id),   -- links to inventory / costing
  yield_per_unit numeric,                               -- e.g. 8 wedges per lime, 12 half moons per orange
  unit_note text,
  allergens text[] default '{}',
  builder_key text not null,                            -- primitive in phg_drink_builder.py
  notes text
);
alter table phg.garnish_types enable row level security;

create table if not exists phg.garnish_placements (
  placement_key text primary key,
  description text not null,
  builder_rule text not null
);
alter table phg.garnish_placements enable row level security;

insert into phg.garnish_placements values
 ('pick','Skewered on a cocktail pick resting across the rim','single pick, items in list order, pick at 68 deg resting on the back rim'),
 ('rim','Slit and seated on the rim','plane radial to the glass, spread round the front-right of the rim'),
 ('dropped','Dropped into the drink','sinks to the bowl bottom / rests on ice'),
 ('float','Floated on the surface','lies flat on the liquid surface'),
 ('drape','Expressed then hung over the rim','half inside / half outside the glass'),
 ('inside_wall','Pressed against the inside wall before ice','bent to the wall curvature, faces the guest')
on conflict do nothing;

-- yield_per_unit values are working figures that need confirming at the bench before they drive costing.
insert into phg.garnish_types (garnish_key,name,kind,allowed_placements,default_placement,yield_per_unit,unit_note,allergens,builder_key,notes) values
 ('cherry','Cocktail cherry (e.g. Luxardo / amarena)','fruit','{pick,dropped}','dropped',null,'per cherry','{}','cherry','Check brand syrup for sulphites if declaring.'),
 ('olive','Cocktail olive','olive_brine','{pick,dropped}','pick',null,'per olive','{}','olive','Stuffed olives: declare filling (e.g. blue cheese = milk).'),
 ('orange_half_moon','Orange half moon','citrus_cut','{pick,rim,inside_wall,float}','pick',null,'slices per orange - bench test','{}','orange_half_moon',null),
 ('orange_wheel','Orange wheel','citrus_cut','{rim,inside_wall,float}','rim',null,null,'{}','orange_wheel',null),
 ('lemon_half_moon','Lemon half moon','citrus_cut','{pick,rim,inside_wall,float}','rim',null,null,'{}','lemon_half_moon',null),
 ('lemon_wheel','Lemon wheel','citrus_cut','{rim,inside_wall,float}','rim',null,null,'{}','lemon_wheel',null),
 ('lime_half_moon','Lime half moon','citrus_cut','{pick,rim,inside_wall,float}','rim',null,null,'{}','lime_half_moon',null),
 ('lime_wheel','Lime wheel','citrus_cut','{rim,float,inside_wall}','rim',null,null,'{}','lime_wheel',null),
 ('lime_wedge','Lime wedge','citrus_cut','{rim,dropped}','rim',8,'wedges per lime (eighths)','{}','lime_wedge',null),
 ('lemon_wedge','Lemon wedge','citrus_cut','{rim,dropped}','rim',8,'wedges per lemon (eighths)','{}','lemon_wedge',null),
 ('orange_peel','Orange peel (expressed swath)','citrus_peel','{drape,float,dropped}','drape',null,null,'{}','orange_peel',null),
 ('lemon_peel','Lemon peel (expressed swath)','citrus_peel','{drape,float,dropped}','drape',null,null,'{}','lemon_peel',null),
 ('lime_peel','Lime peel (expressed swath)','citrus_peel','{drape,float,dropped}','drape',null,null,'{}','lime_peel',null),
 ('lemon_twist','Lemon twist (spiral)','citrus_peel','{drape,dropped}','drape',null,null,'{}','lemon_twist',null),
 ('orange_twist','Orange twist (spiral)','citrus_peel','{drape,dropped}','drape',null,null,'{}','orange_twist',null),
 ('mint_sprig','Mint sprig','herb','{rim,float}','float',null,null,'{}','mint_sprig','Slap before garnishing; the builder places the sprig as a crown.')
on conflict do nothing;

-- Service styles + surface drops (v1.1)
create table if not exists phg.serve_styles (
  serve_key text primary key, description text not null, default_ice jsonb not null, requires_stemware boolean, chilled boolean not null
);
alter table phg.serve_styles enable row level security;
insert into phg.serve_styles values
 ('up','Shaken/stirred, strained, no ice, stemmed glass','{"type":"none"}',true,true),
 ('neat','Straight pour, room temperature, no ice, no dilution','{"type":"none"}',null,false),
 ('down','Over ice in a rocks glass (default large cube)','{"type":"large_cube"}',false,true),
 ('on_large_cube','Over one large clear cube','{"type":"large_cube"}',false,true),
 ('on_sphere','Over an ice sphere','{"type":"sphere"}',false,true),
 ('on_cubes','Over cubed ice, filled to the rim','{"type":"cubes"}',false,true),
 ('on_spear','Collins spear','{"type":"spear"}',false,true),
 ('on_crushed','Over crushed / pebble ice, domed','{"type":"crushed"}',false,true)
on conflict do nothing;
insert into phg.garnish_placements values ('surface','Drops on the drink surface (bitters on foam, oil on a martini)','count + pattern line|ring|triangle|random, sits on foam if present')
on conflict do nothing;
insert into phg.garnish_types (garnish_key,name,kind,allowed_placements,default_placement,unit_note,allergens,builder_key,notes) values
 ('drops','Surface drops (bitters / oil)','other','{surface}','surface','count = drops; liquid = angostura|peychauds|orange_bitters|olive_oil|chili_oil|sesame_oil|citrus_oil','{}','drops',
  'Allergens follow the liquid: e.g. sesame_oil = SESAME (declare). Bitters drops count toward ABV/cost as ~0.05 ml per drop - bench check.')
on conflict do nothing;
-- drink_visuals carries the service style
alter table phg.drink_visuals add column if not exists serve text references phg.serve_styles(serve_key);
