-- Rob, 2026-09-30: "Assume zero." Policy for sweet ingredients whose titratable acidity is not published:
-- liqueurs and sweeteners (e.g. Cointreau, agave syrup) with ta_g_100ml NULL are counted as ~0 g/100 mL TA by the
-- calculator, labelled per line ('ta_assumed_zero') and listed in warnings/assumptions. NOT applied to wine-based
-- products (vermouth, aromatised wine), carbonated mixers (cola = phosphoric acid), juices or anything flagged
-- 'resolve' (unresolved composition stays unresolved). Data stays NULL in ingredient_profiles; the assumption lives in
-- the calculator and in claim fc_policy_unpublished_sweet_acid so it can be revisited or reversed in one place.
-- Rob, same day: products we cannot source stay flagged (on hold) - no change needed for that.

insert into phg_mix.formulation_claims (key, topic, claim_type, statement, quantitative, conditions, limitations, confidence, verification, status) values
 ('fc_policy_unpublished_sweet_acid', 'acidity', 'principle',
  'PHG policy (Rob, 2026-09-30): when a liqueur or sweetener has no published titratable acidity, count it as ~0 g/100 mL TA and label the line as an assumption.',
  '{"assumed_ta_g_100ml":0,"applies_to_classes":["liqueur","sweetener"]}',
  '{"excludes":["vermouth/aromatised wine","wine","carbonated mixers","juices","profiles flagged resolve"]}',
  'Some liqueurs are acidulated (e.g. citric acid in some fruit liqueurs); a measured TA replaces the assumption as soon as one exists.',
  'medium', 'derived', 'active')
on conflict (key) do nothing;

do $$ declare d text := pg_get_functiondef('phg_mix.calc_recipe_balance(text,numeric)'::regprocedure);
  o text := $o$      v_t100 := r.ta_g_100ml; v_t_lo := coalesce(r.ta_min_g_100ml, v_t100); v_t_hi := coalesce(r.ta_max_g_100ml, v_t100);$o$;
  n text := $n$      v_t100 := r.ta_g_100ml;
      if v_t100 is null and r.ingredient_class in ('liqueur','sweetener') and r.resolution_state = 'mapped' then
        v_t100 := 0;  -- fc_policy_unpublished_sweet_acid (Rob 2026-09-30)
        warn := warn || format('"%s": titratable acidity not published - assumed ~0 (PHG policy fc_policy_unpublished_sweet_acid)', r.ingredient_raw);
      end if;
      v_t_lo := coalesce(r.ta_min_g_100ml, v_t100); v_t_hi := coalesce(r.ta_max_g_100ml, v_t100);$n$;
begin
  if position(o in d) = 0 then raise exception 'calc body not as expected'; end if;
  execute replace(d, o, n);
end $$;
