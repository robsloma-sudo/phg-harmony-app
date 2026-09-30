# Source rows transcribed from public.staging_menu_extract (account ACC-IA-LIC-LC0049193, superseded_at is null).
# (staging id, source section, source item_name, source price or None, source notes/brands)
RAW = [
 (173908,'Margaritas','Blackberry',12,'Blanco tequila'),
 (173909,'Margaritas','Coa Margarita',11,'Blanco tequila'),
 (173910,'Margaritas','Coa Mezcal Margarita',12,'Banhez mezcal'),
 (173911,'Margaritas','Cucumber Jalapeno',13,'Blanco tequila'),
 (173912,'Margaritas','Mango',14,'Blanco tequila'),
 (173913,'Margaritas','Peach',12,'Blanco tequila'),
 (173914,'Margaritas','Pineapple',12,'Blanco tequila'),
 (173915,'Margaritas','Strawberry',12,'Blanco tequila'),
 (173916,'Cocktails','Bloody Maria',8,'Blanco tequila'),
 (173917,'Cocktails','Cantaritos',12,'Blanco tequila'),
 (173918,'Cocktails','Coa Paloma',10,'Blanco tequila, Aperol'),
 (173919,'Cocktails','Mexican Ashtray',7,'tequila'),
 (173920,'Cocktails','Michelada',8,'Dos Equis'),
 (173921,'Cocktails','Ranch Water',11,'Blanco tequila'),
 (184680,'Coa Paloma','Our Paloma is made with blanco tequila, fresh lime, grapefruit, Aperol, and grapefruit soda with a salted rim | Upgrade to Don Julio Blanco add',4,'Our Paloma is made with blanco tequila, fresh lime, grapefruit, Aperol, and grapefruit soda with a salted rim | Upgrade to Don Julio Blanco add 4.00'),
 (184681,'Ranch Water','Blanco tequila, fresh lime juice, and Topo Chico sparkling water | Upgrade to Deleon Platinum add',2,'Blanco tequila, fresh lime juice, and Topo Chico sparkling water | Upgrade to Deleon Platinum add $2.00'),
 (173922,'Frozen Drinks','Fro Po',10,'Blanco tequila'),
 (173923,'Frozen Drinks','Mango Margarita',12,'Blanco tequila'),
 (173924,'Frozen Drinks','Strawberry Margarita',10,'Blanco tequila'),
 (173925,'Frozen Drinks','Tropical Twist Margarita',11,'Blanco tequila'),
 (173926,'Drafts','Dos Equis',6,''),
 (173927,'Drafts','Modelo Negra',7,''),
 (173928,'Drafts','Pacifico',6,''),
 (173929,'Drafts','Busch Light',4,''),
 (173930,'Drafts','Exile Swarm Golden Ale',6,''),
 (173931,'Drafts','Clockhouse Witch Slap IPA',8,''),
 (173932,'Bottles & Cans','Bud Light',4,''),
 (173933,'Bottles & Cans','Coors Light',4,''),
 (173934,'Bottles & Cans','High Life',4,''),
 (173935,'Bottles & Cans','Busch Light',4,''),
 (173936,'Bottles & Cans','Victoria',5,''),
 (173937,'Bottles & Cans','Modelo Especial',5,''),
 (173938,'Bottles & Cans','Tecate',4,''),
 (173939,'Bottles & Cans','Angry Orchad Green Apple',6,''),
 (173940,'Bottles & Cans','Ultra',4,''),
 (173941,'Bottles & Cans','Corona',6,''),
 (173942,'Bottles & Cans','Sol',6,''),
 (173943,'Bottles & Cans','High Noon Peach',8,''),
 (173944,'Bottles & Cans','High Noon Passion',8,''),
 (173945,'Bottles & Cans','High Noon Pineapple',8,''),
 (173946,'Bottles & Cans','White Claw Black Cherry',6,''),
 (173947,'Bottles & Cans','White Claw Mango',6,''),
 (173948,'Bottles & Cans','High Noon Tequila Lime',8,''),
 (173949,'Bottles & Cans','High Noon Tequila Passion Fruit',8,''),
 (173950,'Bottles & Cans','High Noon Tequila Strawberry',8,''),
 (173951,'Bottles & Cans','High Noon Tequila Grapefruit',8,''),
 (173952,'Vodka','Swarm',6,''),
 (173953,'Vodka','Grey Goose',8,''),
 (173954,'Vodka','Ketel One',7,''),
 (173955,'Vodka','Ketel One Botanical',7,'Cucumber & Mint, Grapefruit & Rose, Peach & Orange Blossom'),
 (173956,'Vodka','Smirnoff',6,'Grape, Orange, Citrus, Raspberry, Watermelon'),
 (173957,'Vodka','Titos',7,''),
 (173958,'Rum','Bacardi',6,''),
 (173959,'Rum','Bacardi Dragon Berry',6,''),
 (173960,'Rum','Captain Morgan',6,''),
 (173961,'Rum',"Gosling's",6,''),
 (173962,'Gin','Aviation',7,''),
 (173963,'Gin','Bombay Sapphire',8,''),
 (173964,'Gin',"Hendrick's",8,''),
 (173965,'Gin','Tanqueray',6,''),
 (173966,'Whiskey','Cedar Ridge',8,''),
 (173967,'Whiskey','Crown Apple',7,''),
 (173968,'Whiskey','Crown Royal',7,''),
 (173969,'Whiskey','Jack Daniels',7,''),
 (173970,'Whiskey','Jameson',7,''),
 (173971,'Whiskey',"Maker's Mark",None,''),
 (173972,'Whiskey','Templeton Rye',8,''),
 (173973,'Scotch','Glenlivet 12',12,''),
 (173974,'Scotch','Johnny Walker Red',6,''),
 (173975,'Alcohol Free','Ritual Alternative Zero Proof',7,'Tequila, Gin, Whiskey'),
 (174103,'Misc','Café Patron',9,''),
 (174104,'Misc','Clase Azul Gold',125,''),
]

B = """173976|818|11
173977|Astral Blanco|8
173978|Avion|12
173979|Casa Dragones|15
173980|Casa Noble|10
173981|Casamigos|12
173982|Centenario|11
173983|Cincoro|15
173984|Clase Azul|30
173985|Codigo|9
173986|Codico Rosa|11
173987|Corallejo|6
173988|Corazon|6
173989|Deleon Platinum|9
173990|Don Julio|12
173991|El Mayor|7
173992|El Tesoro|12
173993|Espolon|6
173994|Exotico|6
173995|Fleche Azul|15
173996|Fortaleza|18
173997|Herradura|9
173998|House Infused Jalapeno Tequila|9
173999|Ja Ja|8
174000|Jose Cuervo de la Familia Platino|11
174001|Lunazul|6
174002|Milagro|7
174003|Milagro Select Barrel Reserve|10
174004|Number Juan|9
174005|Olmeca Altos|6
174006|Pasote|15
174007|Patron|10
174008|Roca Patron|16
174009|Siete Leguas|11
174010|Tremana|7
174011|Tequila Ocho|15
174012|Tres Generaciones|11"""
R = """174013|818|13
174014|Aman|25
174015|Asombroso Rose|13
174016|Avion|12
174017|Casamigos|11
174018|Casamigos Cristalino|18
174019|Casa Noble|12
174020|Centenario|12
174021|Cincoro|20
174022|Clase Azul|40
174023|Codigo|12
174024|Corallejo|7
174025|Corazon Blantons|11
174026|Corazon E.H. Taylor|11
174027|Corazon Weller|10
174028|Deleon|14
174029|Don Julio|12
174030|Don Julio 1942 Primavera|30
174031|Don Julio Rosado|40
174032|El Mayor|9
174033|El Tesoro|12
174034|Espolon|6
174035|Fleche Azul|13
174036|Fortaleza|20
174037|Gran Coramino Cristalino|15
174038|Hacienda Vieja|9
174039|Herradura|11
174040|Hussongs|12
174041|Ja Ja|10
174042|Komos Rosa|30
174043|Tequila Ocho|12
174044|La Gritona|14
174045|Lunazul|7
174046|Milagro|7
174047|Milagro Select Barrel Reserve|11
174048|Number Juan|11
174049|Olmeca Altos|6
174050|Pasote|17
174051|Patron|11
174052|Patron Barrel Select|13
174053|Siete Leguas|15
174054|Tapatio|12
174055|Tremana|7
174056|Tres Generaciones|12
174057|Tres Generaciones la Colonial|20"""
A = """174058|818|15
174059|818 Reserve|65
174060|Aman|40
174061|Asombroso|25
174062|Avion Reserva 44|30
174063|Casa Noble|15
174064|Casamigos|15
174065|Centenario|13
174066|Cincoro|25
174067|Clase Azul|200
174068|Corazon Eagle Rare|25
174069|Corralejo Extra 1821|40
174070|Corralejo|8
174071|Corralejo Extra|15
174072|Don Julio|13
174073|Don Julio 1942|40
174074|Don Julio 70|16
174075|Don Julio Real Extra|110
174076|El Mayor|12
174077|El Tesoro|16
174078|Espolon|7
174079|Espolon Cristalino|10
174080|Fleche Azul|17
174081|Gran Corralejo|25
174082|Gran Coramino|35
174083|Hacienda Vieja|7
174084|Herradura|12
174085|Herradura Cristalino|13
174086|Herradura Seleccion Suprema|70
174087|Hussongs Platinum|12
174088|Jose Cuervo Reserva de la Familia|40
174089|Komos Cristalnio|25
174090|Komos Ultra|100
174091|Milagro|8
174092|Milagro Select Barrel Reserve|15
174093|Number Juan|13
174094|Pasote|22
174095|Patron|12
174096|Patron Sherry Cask|14
174097|Patron Extra|20
174098|Roca Patron|19
174099|Siete Leguas|17
174100|Tequila Ocho|14
174101|Teremana|10
174102|Tres Generaciones|13"""

def parse(s, sec):
    out=[]
    for line in s.strip().splitlines():
        i,n,p=line.split('|'); out.append((int(i),sec,n,int(p),''))
    return out
TEQ = parse(B,'Blanco')+parse(R,'Reposado')+parse(A,'Anejo')
ALL = RAW + TEQ

# Name rule (round 2): print the venue's spelling. A change is allowed only when a catalogue row supports it
# (public.brands / public.products id cited below). Accents are never added without such a row.
FIX = {
 'Codico Rosa': ('Codigo Rosa', 'brands 13226856-a0ac-4a4f-af5b-09aa80799bd6 "Codigo 1530"'),
 'Corallejo': ('Corralejo', 'brands 1a7a2d92-8bdb-44f1-b165-335b84ac84df "Corralejo"'),
 'Tremana': ('Teremana', 'brands ff00b87a-599d-4968-acfe-4d822c303872 "Teremana"'),
 'Komos Cristalnio': ('Komos Cristalino', 'brands 677b30fe-fb44-4721-a40d-de037c587662 "Komos" + beverage_categories slug cristalino'),
 'Fleche Azul': ('Flecha Azul', 'brands 5b6902fd-95e3-4a2a-86cb-cc2adf978ab5 "Flecha Azul"'),
 'Ja Ja': ('Jaja', 'brands 0bb1bf79-0262-48ba-a93f-b30df910b8d3 "Jaja"'),
 'Herradura Seleccion Suprema': ('Herradura Selección Suprema', 'brands df036bdd-53d5-4b05-80ba-6c2e29aab0ea "Herradura Selección Suprema de Herradura"'),
}
def fix(n): return FIX[n][0] if n in FIX else n
def fix_cite(n): return FIX[n][1] if n in FIX else None
