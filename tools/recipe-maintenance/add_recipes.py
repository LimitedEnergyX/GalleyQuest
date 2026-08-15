# -*- coding: utf-8 -*-
"""Add ~50 Crohn's-friendly (anti-inflammatory + gut-gentle) recipes to live
GalleyQuest. Fresh proteins, olive oil, turmeric/ginger, well-cooked veg; no
deep-frying, processed/cured meat, heavy cream, or refined sugar. Inserts into
recipes (theme + taxonomy notes + instructions) then recipe_ingredients.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

def R(name, theme, cuisine, category, method, ings):
    notes = "Category: %s\nCuisine: %s\nTags: anti-inflammatory, gut-friendly" % (category, cuisine)
    return {"name": name, "theme": theme, "notes": notes, "instructions": method, "ings": ings}

RECIPES = [
 # ---------------- Grab Night (quick / minimal-cook) ----------------
 R("Avocado Salmon Salad","Grab Night","Seafood","Grab","Mash avocado with lemon, a pinch of salt and garlic powder. Fold in flaked canned salmon, cucumber and celery. Top with green onion; serve over rice or in a wrap.",
   [("canned salmon","6 oz"),("avocado","1"),("cucumber","1/3 cup"),("celery","1 stalk"),("green onion","1 tbsp"),("lemon","1/2"),("olive oil","1 tsp"),("garlic powder","1 tsp")]),
 R("Tuna Avocado Rice Bowl","Grab Night","Seafood","Grab","Flake canned tuna over warm rice. Top with diced avocado and cucumber, drizzle olive oil and lemon, finish with a splash of tamari.",
   [("canned tuna","6 oz"),("cooked white rice","1 cup"),("avocado","1/2"),("cucumber","1/3 cup"),("olive oil","1 tsp"),("lemon","1/2"),("tamari","1 tsp")]),
 R("Chicken & Avocado Wrap","Grab Night","American","Grab","Warm a soft tortilla. Layer cooked shredded chicken, mashed avocado and cooked spinach; drizzle olive oil, roll and serve.",
   [("cooked chicken","1 cup"),("avocado","1/2"),("baby spinach","1 cup"),("soft flour tortilla","1"),("olive oil","1 tsp"),("lemon","1/2")]),
 R("Egg & Spinach Scramble Wrap","Grab Night","American","Breakfast","Soft-scramble eggs in olive oil with wilted spinach. Spoon into a warm tortilla, add a little cheese if wanted.",
   [("eggs","3"),("baby spinach","1 cup"),("olive oil","1 tsp"),("soft flour tortilla","1"),("shredded cheese","2 tbsp")]),
 R("Salmon & Cucumber Rice Cakes","Grab Night","Seafood","Grab","Spread mashed avocado on rice cakes. Top with flaked cooked salmon and thin cucumber; finish with dill and lemon.",
   [("cooked salmon","4 oz"),("rice cakes","2"),("avocado","1/2"),("cucumber","1/3 cup"),("fresh dill","1 tbsp"),("lemon","1/2")]),
 R("Greek Yogurt Berry Oat Bowl","Grab Night","American","Breakfast","Layer plain yogurt with cooked-soft oats and blueberries. Drizzle a little honey and a pinch of cinnamon.",
   [("plain yogurt","3/4 cup"),("rolled oats","1/3 cup"),("blueberries","1/2 cup"),("honey","1 tsp"),("cinnamon","1 pinch")]),
 R("Banana Ginger Oat Smoothie","Grab Night","American","Breakfast","Blend banana, oats, yogurt and a little grated ginger with milk until smooth.",
   [("banana","1"),("rolled oats","1/4 cup"),("plain yogurt","1/2 cup"),("milk","3/4 cup"),("fresh ginger","1/2 tsp"),("honey","1 tsp")]),
 R("Quick Chicken & Ginger Rice Noodle Bowl","Grab Night","Asian","Grab","Warm bone broth with grated ginger. Pour over cooked rice noodles and shredded chicken; wilt in spinach.",
   [("chicken bone broth","2 cups"),("cooked chicken","1 cup"),("rice noodles","3 oz"),("fresh ginger","1 tsp"),("baby spinach","1 cup"),("green onion","1 tbsp")]),
 R("Turkey & Rice Power Bowl","Grab Night","American","Grab","Warm cooked ground turkey and rice; add steamed carrots. Dress with olive oil, lemon and herbs.",
   [("cooked ground turkey","1 cup"),("cooked white rice","1 cup"),("carrot","1/2 cup"),("olive oil","1 tsp"),("lemon","1/2"),("parsley","1 tbsp")]),
 R("Baked Eggs with Spinach & Tomato","Grab Night","Mediterranean","Breakfast","Simmer tomato in olive oil, wilt spinach, crack in eggs and bake until just set.",
   [("eggs","3"),("baby spinach","2 cups"),("diced tomato","1 cup"),("olive oil","1 tbsp"),("garlic","1 clove")]),

 # ---------------- Crock Pot (soft, slow-cooked) ----------------
 R("Slow-Cooker Turkey & Sweet Potato Stew","Crock Pot","Comfort","Dinner","Add cubed turkey, peeled sweet potato, potato and carrot to the pot with tomato, garlic and spices. Add water to cover and cook on low ~8 hours.",
   [("turkey breast","1 lb"),("sweet potato","2"),("potato","2"),("carrot","2"),("diced tomato","1 can"),("turmeric","2 tbsp"),("paprika","1 tbsp"),("cinnamon","1 tsp"),("garlic","3 cloves")]),
 R("Slow-Cooker Lemon-Herb Chicken","Crock Pot","American","Dinner","Nestle chicken breasts over halved baby potatoes. Add olive oil, lemon, herbs and a splash of broth; cook low 6 hours.",
   [("chicken breast","1.5 lb"),("baby potatoes","1 lb"),("olive oil","2 tbsp"),("lemon","1"),("thyme","1 tsp"),("chicken broth","1/2 cup"),("garlic","2 cloves")]),
 R("Low-FODMAP Coconut Chicken Curry","Crock Pot","Thai","Dinner","Combine chicken, coconut milk, turmeric, ginger and carrot in the pot; cook low 6 hours. Serve over rice.",
   [("chicken thighs","1.5 lb"),("coconut milk","1 can"),("turmeric","1 tsp"),("fresh ginger","1 tbsp"),("carrot","2"),("garlic-infused olive oil","1 tbsp"),("cooked rice","2 cups")]),
 R("Slow-Cooker Salmon & Potato Chowder","Crock Pot","Seafood","Soup","Cook potato, carrot and broth low ~4 hours until soft; add salmon in the last 30 minutes. Finish with dill.",
   [("salmon fillet","1 lb"),("potato","3"),("carrot","2"),("chicken broth","3 cups"),("milk","1 cup"),("fresh dill","2 tbsp"),("olive oil","1 tbsp")]),
 R("Crock Pot Chicken & Rice Soup","Crock Pot","American","Soup","Add chicken, carrot, celery, rice and broth; cook low 6 hours. Shred chicken and stir in turmeric.",
   [("chicken breast","1 lb"),("carrot","2"),("celery","2 stalks"),("white rice","1/2 cup"),("chicken broth","6 cups"),("turmeric","1 tsp")]),
 R("Slow-Cooker Beef & Root Vegetable Stew","Crock Pot","Comfort","Dinner","Layer lean beef with carrot, potato and parsnip; add tomato, broth and herbs. Cook low 8 hours until fork-tender.",
   [("lean beef stew meat","1.5 lb"),("carrot","3"),("potato","3"),("parsnip","1"),("diced tomato","1 can"),("beef broth","2 cups"),("rosemary","1 tsp")]),
 R("Crock Pot Turkey Meatballs in Tomato","Crock Pot","Italian","Dinner","Roll turkey meatballs, settle into tomato sauce with garlic and herbs; cook low 5 hours. Serve over whole-wheat pasta.",
   [("ground turkey","1 lb"),("egg","1"),("whole wheat breadcrumbs","1/3 cup"),("crushed tomato","1 can"),("garlic","2 cloves"),("basil","1 tbsp"),("whole wheat pasta","8 oz")]),
 R("Slow-Cooker Ginger-Turmeric Chicken & Squash","Crock Pot","Thai","Dinner","Combine chicken, butternut squash, coconut milk, ginger and turmeric; cook low 6 hours. Serve over rice.",
   [("chicken thighs","1.5 lb"),("butternut squash","2 cups"),("coconut milk","1 can"),("fresh ginger","1 tbsp"),("turmeric","1 tsp"),("cooked rice","2 cups")]),
 R("Crock Pot White Fish & Vegetable Stew","Crock Pot","Mediterranean","Soup","Cook potato, carrot, fennel and tomato low ~4 hours; add white fish in the last 30 minutes.",
   [("cod fillet","1 lb"),("potato","2"),("carrot","2"),("fennel","1/2 bulb"),("diced tomato","1 can"),("olive oil","1 tbsp"),("parsley","2 tbsp")]),
 R("Slow-Cooker Pumpkin Ginger Soup","Crock Pot","Comfort","Soup","Cook pumpkin, carrot, ginger and broth low 5 hours; blend smooth and finish with olive oil.",
   [("pumpkin","4 cups"),("carrot","2"),("fresh ginger","1 tbsp"),("vegetable broth","4 cups"),("olive oil","1 tbsp")]),

 # ---------------- Asian ----------------
 R("Baked Turmeric-Ginger Salmon","Asian","Asian","Dinner","Rub salmon with olive oil, turmeric and grated ginger. Bake at 425F ~12 minutes; serve over rice.",
   [("salmon fillet","1 lb"),("olive oil","1 tbsp"),("turmeric","1 tsp"),("fresh ginger","1 tbsp"),("cooked rice","2 cups"),("lemon","1/2")]),
 R("Ginger-Sesame Baked Salmon over Rice","Asian","Asian","Dinner","Brush salmon with tamari, ginger and a touch of honey. Bake with bok choy; serve over rice, sprinkle sesame.",
   [("salmon fillet","1 lb"),("tamari","2 tbsp"),("fresh ginger","1 tbsp"),("honey","1 tsp"),("bok choy","2 cups"),("cooked rice","2 cups"),("sesame seeds","1 tsp")]),
 R("Steamed Ginger Chicken & Rice","Asian","Asian","Dinner","Steam chicken with ginger until tender; serve over rice with wilted spinach and a little tamari.",
   [("chicken breast","1 lb"),("fresh ginger","1 tbsp"),("cooked rice","2 cups"),("baby spinach","2 cups"),("tamari","1 tbsp")]),
 R("Miso-Baked Cod","Asian","Asian","Dinner","Spread cod with a thin miso-ginger glaze and bake ~12 minutes. Serve over rice with steamed greens.",
   [("cod fillet","1 lb"),("white miso","1 tbsp"),("fresh ginger","1 tsp"),("cooked rice","2 cups"),("bok choy","2 cups")]),
 R("Chicken & Bok Choy Rice Bowl","Asian","Asian","Dinner","Gently cook chicken in olive oil with ginger; add bok choy until soft. Serve over rice with a splash of tamari.",
   [("chicken thighs","1 lb"),("bok choy","3 cups"),("fresh ginger","1 tbsp"),("olive oil","1 tbsp"),("tamari","1 tbsp"),("cooked rice","2 cups")]),
 R("Ginger Egg Drop Soup","Asian","Asian","Soup","Simmer broth with ginger; stream in beaten egg. Wilt spinach and finish with green onion.",
   [("chicken broth","4 cups"),("eggs","2"),("fresh ginger","1 tsp"),("baby spinach","1 cup"),("green onion","1 tbsp")]),
 R("Light Teriyaki Baked Chicken","Asian","Asian","Dinner","Bake chicken glazed with tamari, ginger and a little honey. Serve over rice with steamed carrots.",
   [("chicken thighs","1.5 lb"),("tamari","2 tbsp"),("fresh ginger","1 tbsp"),("honey","1 tbsp"),("cooked rice","2 cups"),("carrot","1 cup")]),
 R("Turmeric Chicken Congee","Asian","Asian","Breakfast","Simmer rice in extra broth with chicken, ginger and turmeric until porridge-soft. Top with green onion.",
   [("chicken breast","1/2 lb"),("white rice","3/4 cup"),("chicken broth","6 cups"),("fresh ginger","1 tbsp"),("turmeric","1 tsp"),("green onion","1 tbsp")]),

 # ---------------- Thai ----------------
 R("Thai Red Curry with Salmon","Thai","Thai","Dinner","Simmer mild red curry paste with coconut milk; add carrot, then salmon and cook gently. Finish with basil; serve over rice.",
   [("salmon fillet","3/4 lb"),("red curry paste","2 tbsp"),("coconut milk","1 can"),("carrot","1"),("Thai basil","6 leaves"),("fish sauce","1 tbsp"),("cooked rice","2 cups")]),
 R("Coconut Chicken & Turmeric Curry","Thai","Thai","Dinner","Cook chicken in coconut milk with turmeric, ginger and sweet potato until tender. Serve over rice.",
   [("chicken thighs","1 lb"),("coconut milk","1 can"),("turmeric","1 tsp"),("fresh ginger","1 tbsp"),("sweet potato","1 cup"),("cooked rice","2 cups")]),
 R("Mild Tom Kha Chicken Soup","Thai","Thai","Soup","Simmer coconut milk with ginger and lime leaf; add chicken and mushroom until cooked. Finish with lime.",
   [("chicken breast","3/4 lb"),("coconut milk","1 can"),("fresh ginger","1 tbsp"),("mushroom","1/2 cup"),("lime","1"),("fish sauce","1 tbsp")]),
 R("Baked Thai Salmon in Foil","Thai","Thai","Dinner","Wrap salmon with coconut, ginger, lime and cilantro; bake ~15 minutes. Serve over rice.",
   [("salmon fillet","1 lb"),("coconut milk","1/2 cup"),("fresh ginger","1 tbsp"),("lime","1"),("cilantro","2 tbsp"),("cooked rice","2 cups")]),
 R("Thai Turmeric Fish & Rice","Thai","Thai","Dinner","Poach white fish in coconut milk with turmeric and ginger. Serve over rice with cooked greens.",
   [("white fish fillet","1 lb"),("coconut milk","1 can"),("turmeric","1 tsp"),("fresh ginger","1 tbsp"),("cooked rice","2 cups"),("baby spinach","2 cups")]),
 R("Chicken & Pumpkin Coconut Curry","Thai","Thai","Dinner","Simmer chicken and pumpkin in coconut milk with mild curry paste until soft. Serve over rice.",
   [("chicken thighs","1 lb"),("pumpkin","2 cups"),("coconut milk","1 can"),("red curry paste","1 tbsp"),("cooked rice","2 cups")]),

 # ---------------- Mexican (gentle) ----------------
 R("Mild Chicken & Rice Burrito Bowl","Mexican","Mexican","Dinner","Warm shredded chicken and rice; add cooked bell pepper, tomato and avocado. Squeeze lime.",
   [("cooked chicken","1.5 cups"),("cooked rice","2 cups"),("bell pepper","1"),("diced tomato","1/2 cup"),("avocado","1"),("lime","1"),("olive oil","1 tbsp")]),
 R("Turkey & Sweet Potato Taco Skillet","Mexican","Tex-Mex","Dinner","Brown turkey with mild cumin and paprika; add cooked sweet potato. Spoon into soft tortillas.",
   [("ground turkey","1 lb"),("sweet potato","1 cup"),("cumin","1 tsp"),("paprika","1 tsp"),("soft flour tortilla","6"),("avocado","1")]),
 R("Gentle Chicken Tortilla Soup","Mexican","Mexican","Soup","Simmer chicken with tomato and well-cooked carrot in broth. Serve with soft tortilla strips and lime.",
   [("chicken breast","1 lb"),("diced tomato","1 can"),("carrot","2"),("chicken broth","5 cups"),("soft corn tortilla","2"),("lime","1"),("cumin","1 tsp")]),
 R("Baked Fish Tacos with Slaw","Mexican","Mexican","Dinner","Bake seasoned white fish. Serve in soft tortillas with finely shredded cooked cabbage, avocado and lime.",
   [("white fish fillet","1 lb"),("soft flour tortilla","6"),("cabbage","1 cup"),("avocado","1"),("lime","1"),("olive oil","1 tbsp"),("cumin","1 tsp")]),
 R("Chicken & Avocado Rice Bowl","Mexican","Mexican","Dinner","Layer rice, warm chicken, tomato and avocado; dress with olive oil and lime.",
   [("cooked chicken","1.5 cups"),("cooked rice","2 cups"),("diced tomato","1/2 cup"),("avocado","1"),("olive oil","1 tbsp"),("lime","1")]),
 R("Mild Beef & Potato Picadillo","Mexican","Mexican","Dinner","Cook lean beef with tomato, potato and mild spices until soft. Serve over rice.",
   [("lean ground beef","1 lb"),("potato","2"),("diced tomato","1 can"),("cumin","1 tsp"),("cinnamon","1 pinch"),("cooked rice","2 cups")]),
 R("Chicken Fajita Bowl","Mexican","Tex-Mex","Dinner","Cook chicken with soft-sauteed bell pepper and onion. Serve over rice with avocado.",
   [("chicken breast","1 lb"),("bell pepper","2"),("onion","1"),("olive oil","1 tbsp"),("cooked rice","2 cups"),("avocado","1")]),
 R("Sweet Potato & Rice Burrito Bowl","Mexican","Mexican","Dinner","Roast cubed sweet potato; layer over rice with tomato and avocado. Finish with lime and olive oil.",
   [("sweet potato","2 cups"),("cooked rice","2 cups"),("diced tomato","1/2 cup"),("avocado","1"),("lime","1"),("olive oil","1 tbsp")]),

 # ---------------- Open ----------------
 R("Baked Salmon with Sweet Potato & Spinach","Open","Seafood","Dinner","Roast salmon and cubed sweet potato in olive oil; serve over wilted spinach with lemon.",
   [("salmon fillet","1 lb"),("sweet potato","2"),("baby spinach","3 cups"),("olive oil","2 tbsp"),("lemon","1")]),
 R("Turmeric Chicken Quinoa Bowl","Open","Mediterranean","Dinner","Cook chicken with turmeric; serve over quinoa with soft-roasted vegetables and olive oil.",
   [("chicken breast","1 lb"),("quinoa","1 cup"),("zucchini","1"),("carrot","1"),("turmeric","1 tsp"),("olive oil","2 tbsp")]),
 R("Mediterranean Baked Cod with Tomato","Open","Mediterranean","Dinner","Bake cod over tomato and olive oil with herbs; serve with soft potatoes.",
   [("cod fillet","1 lb"),("diced tomato","1 cup"),("potato","3"),("olive oil","2 tbsp"),("oregano","1 tsp"),("garlic","2 cloves")]),
 R("Gentle Chicken & Vegetable Soup","Open","American","Soup","Simmer chicken with carrot, potato and celery in broth until soft; shred and serve.",
   [("chicken breast","1 lb"),("carrot","2"),("potato","2"),("celery","2 stalks"),("chicken broth","6 cups"),("parsley","2 tbsp")]),
 R("Herb-Baked Chicken with Rice & Carrots","Open","American","Dinner","Bake herb-rubbed chicken; serve over rice with steamed carrots and olive oil.",
   [("chicken thighs","1.5 lb"),("cooked rice","2 cups"),("carrot","2"),("olive oil","1 tbsp"),("thyme","1 tsp"),("lemon","1/2")]),
 R("Red Lentil & Carrot Soup","Open","Mediterranean","Soup","Simmer red lentils with carrot, ginger and turmeric until very soft; blend smooth and finish with olive oil.",
   [("red lentils","1 cup"),("carrot","3"),("fresh ginger","1 tbsp"),("turmeric","1 tsp"),("vegetable broth","5 cups"),("olive oil","1 tbsp")]),
 R("Turkey Meatballs with Marinara over Pasta","Open","Italian","Dinner","Bake turkey meatballs; simmer in tomato-basil sauce and serve over whole-wheat pasta.",
   [("ground turkey","1 lb"),("egg","1"),("whole wheat breadcrumbs","1/3 cup"),("crushed tomato","1 can"),("basil","1 tbsp"),("whole wheat pasta","8 oz"),("olive oil","1 tbsp")]),
 R("Poached Salmon with Dill & Potatoes","Open","Seafood","Dinner","Gently poach salmon in broth with dill and lemon; serve with soft boiled potatoes.",
   [("salmon fillet","1 lb"),("potato","3"),("fresh dill","2 tbsp"),("lemon","1"),("chicken broth","2 cups"),("olive oil","1 tbsp")]),

 # ---------------- None (misc) ----------------
 R("Overnight Oats with Berries","None","American","Breakfast","Stir oats with milk and yogurt; rest overnight. Top with blueberries, honey and cinnamon.",
   [("rolled oats","1/2 cup"),("milk","3/4 cup"),("plain yogurt","1/4 cup"),("blueberries","1/2 cup"),("honey","1 tsp"),("cinnamon","1 pinch")]),
 R("Golden Turmeric Chicken Broth","None","Comfort","Soup","Simmer chicken broth with ginger, turmeric and shredded chicken; add soft rice for a gentle bowl.",
   [("chicken broth","6 cups"),("cooked chicken","1 cup"),("fresh ginger","1 tbsp"),("turmeric","1 tsp"),("cooked white rice","1 cup"),("green onion","1 tbsp")]),
]

# ---- insert recipes, then their ingredients ----
rec_payload = [{"name": r["name"], "theme": r["theme"], "notes": r["notes"], "instructions": r["instructions"]} for r in RECIPES]
st, body = _db.insert("recipes", rec_payload)
if st >= 400 or not isinstance(body, list):
    raise SystemExit("recipe insert failed: HTTP %s %s" % (st, str(body)[:300]))
print("inserted recipes:", len(body))

ing_payload = []
for r, ins in zip(RECIPES, body):
    for nm, qty in r["ings"]:
        ing_payload.append({"recipe_id": ins["id"], "ingredient_name": nm, "quantity": qty})

added_ing = 0
for i in range(0, len(ing_payload), 400):
    chunk = ing_payload[i:i+400]
    st2, body2 = _db.insert("recipe_ingredients", chunk)
    if st2 >= 400:
        raise SystemExit("ingredient insert failed at %d: HTTP %s %s" % (i, st2, str(body2)[:300]))
    added_ing += len(chunk)
print("inserted ingredient rows:", added_ing)

# theme tally + totals
from collections import Counter
themes = Counter(r["theme"] for r in RECIPES)
print("by theme:", dict(themes))
print("recipes total now:", _db.count("recipes"), "| recipe_ingredients now:", _db.count("recipe_ingredients"))
