-- Applied live 2026-09-29 (migration v_venue_pins_with_prices): venue map pins + cocktail avg/median price + ZIP income/age.
create or replace view public.v_venue_pins as
select p.state_code, p.venue, p.city, p.venue_type, p.rating, p.lat, p.lng, p.venue_key, p.drink_items,
       pr.cocktail_avg_price, pr.cocktail_median_price, pr.cocktail_items, pr.income, pr.median_age
  from public.mv_dash_pins p
  left join public.mv_menu_dev_venue_profile pr on pr.venue_key = p.venue_key;
revoke all on public.v_venue_pins from public, anon, authenticated;
grant select on public.v_venue_pins to service_role;
