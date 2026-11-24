USE consciouscart_db;

INSERT INTO product_categories (slug, name, icon_name, description) VALUES
('personal-care', 'Personal care', 'sparkles', 'Daily skin, oral, and hair care essentials'),
('bath-and-body', 'Bath and body', 'droplets', 'Cleansing bars, body washes, and bathing supplies'),
('food-and-groceries', 'Food and groceries', 'wheat', 'Grains, pulses, and pantry staples'),
('fruits-and-vegetables', 'Fruits and vegetables', 'apple', 'Fresh seasonal produce'),
('dairy', 'Dairy', 'milk', 'Milk, curd, and chilled dairy products'),
('household-cleaning', 'Household cleaning', 'shield-check', 'Surface, dish, and laundry cleaners'),
('cooking-essentials', 'Cooking essentials', 'flame', 'Oils, spices, and kitchen basics'),
('other-essentials', 'Other essentials', 'package', 'General household necessities');

INSERT INTO brands (name, transparency_rating, sourcing_notes) VALUES
('Prakriti Botanicals', 9.2, 'Publishes batch-level farm origin and NPOP organic certificates'),
('VanaVeda Naturals', 8.0, 'Discloses full INCI list and RSPO-certified plant oils'),
('Sudha Everyday', 6.8, 'Lists complete ingredients and BIS compliance on pack'),
('MahaValue Basics', 5.2, 'Meets statutory BIS labeling norms; limited upstream sourcing disclosure'),
('Kaveri Organic Farms', 9.4, 'Direct farmer cooperative with India Organic / NPOP certification'),
('Namma Harvest', 7.9, 'Single-origin unpolished grains with pesticide-residue test summaries'),
('Annapurna Staples', 6.5, 'Standard graded retail grains with batch traceability'),
('Janata Ration Co.', 5.0, 'Economy bulk-packed staple grains');

-- Four-Level Soap Alternatives (Keyword: soap)
INSERT INTO products (
  category_id, brand_id, search_keyword, name, variant_label, tier_category,
  quantity_value, quantity_unit, image_url, packaging_material, packaging_recyclable,
  packaging_notes, environmental_summary, manufacturer_claims, safety_compliance_notes,
  ingredient_transparency_level
) VALUES
(2, 1, 'soap', 'Cold-Processed Neem & Shea Bath Bar', '100g Single Bar', 'premium_organic',
 100, 'g', '/static/images/soap_premium.svg', 'Unbleached Recycled Kraft Paper Box', TRUE,
 'Plastic-free FSC-certified kraft carton printed with soy ink.',
 'Biodegradable plant-oil soap base; zero palm-oil derivatives; low-energy cold process.',
 'Made with 82% certified organic cold-pressed oils.',
 'BIS IS 2888 Type 1 compliant; TFM 78% documented.', 'full'),

(2, 2, 'soap', 'Coconut & Vetiver Gentle Cleansing Bar', '125g Single Bar', 'conscious_choice',
 125, 'g', '/static/images/soap_conscious.svg', 'Recyclable Paper Wrapper', TRUE,
 'Single-layer coated paper wrapper without inner plastic film.',
 'RSPO-certified coconut/palm kernel oil blend; biodegradable surfactants.',
 'Dermatologically tested; free from synthetic dyes.',
 'BIS IS 2888 Type 1 compliant; TFM 76% documented.', 'full'),

(2, 3, 'soap', 'Glycerin & Aloe Daily Bath Soap', '125g Single Bar', 'budget_conscious',
 125, 'g', '/static/images/soap_budget.svg', 'BOPP Plastic Flow-Wrap', FALSE,
 'Multi-layer flexible plastic wrapper; not accepted in curbside recycling.',
 'Standard soap noodle formulation; moderate water footprint.',
 'Enriched with vegetable glycerin for mild cleansing.',
 'BIS IS 2888 Type 2 compliant; TFM 70%.', 'partial'),

(2, 4, 'soap', 'Family Value Carbolic-Free Bath Bar', '150g Economy Bar', 'economy_choice',
 150, 'g', '/static/images/soap_economy.svg', 'LDPE Wrapper', FALSE,
 'Thin plastic film wrapper.',
 'Conventional sodium tallowate/palmate blend; upstream sourcing undisclosed.',
 'High-lather value bar for daily family use.',
 'BIS IS 2888 Type 3 compliant; TFM 62%.', 'basic');

INSERT INTO product_prices (product_id, unit_price, effective_date, is_current) VALUES
(1, 185.00, CURDATE(), TRUE),
(2, 95.00, CURDATE(), TRUE),
(3, 52.00, CURDATE(), TRUE),
(4, 32.00, CURDATE(), TRUE);

INSERT INTO organic_certifications (product_id, certifier_name, certificate_code, scope, verified_status) VALUES
(1, 'NPOP / India Organic (Control Union)', 'CU-IN-849201', 'organic_ingredients', TRUE),
(2, 'RSPO Supply Chain Certified', 'RSPO-110492', 'eco_label', TRUE),
(3, 'None Declared', NULL, 'none', FALSE),
(4, 'None Declared', NULL, 'none', FALSE);

INSERT INTO ingredients (inci_name, common_name, origin_type, primary_function, environmental_consideration, safety_note) VALUES
('Sodium Cocoate', 'Saponified Coconut Oil', 'plant_derived', 'Primary cleansing surfactant', 'Readily biodegradable in aquatic systems', 'Generally mild; rinses cleanly'),
('Butyrospermum Parkii Butter', 'Shea Butter', 'plant_derived', 'Emollient and skin conditioning', 'Biodegradable; sustainable when wild-harvested fairly', 'Non-irritating emollient'),
('Azadirachta Indica Seed Oil', 'Neem Oil', 'plant_derived', 'Botanical conditioning agent', 'Biodegradable plant lipid', 'Patch test advised for sensitive skin'),
('Glycerin', 'Vegetable Glycerin', 'plant_derived', 'Humectant that retains skin moisture', 'Readily biodegradable', 'Safe and well-tolerated across skin types'),
('Sodium Laureth Sulfate', 'SLES', 'synthetic', 'Foaming cleansing surfactant', 'Biodegradable under aerobic wastewater treatment; ethoxylated synthetic', 'Safe within regulated rinse-off concentrations; can dry sensitive skin'),
('Titanium Dioxide', 'CI 77891', 'mineral', 'Opacifier and white pigment', 'Persistent mineral; non-bioaccumulative in rinse-off soap', 'Approved cosmetic colorant in rinse-off products'),
('Parfum', 'Fragrance Blend', 'unknown', 'Scenting agent', 'Composition undisclosed unless specified by brand', 'Potential allergen for fragrance-sensitive users');

INSERT INTO product_ingredients (product_id, ingredient_id, position_order, is_certified_organic_input, verification_status) VALUES
(1, 1, 1, TRUE, 'verified'),
(1, 2, 2, TRUE, 'verified'),
(1, 3, 3, TRUE, 'verified'),
(1, 4, 4, FALSE, 'verified'),
(2, 1, 1, FALSE, 'verified'),
(2, 4, 2, FALSE, 'verified'),
(2, 7, 3, FALSE, 'manufacturer_claim'),
(3, 1, 1, FALSE, 'manufacturer_claim'),
(3, 4, 2, FALSE, 'manufacturer_claim'),
(3, 6, 3, FALSE, 'manufacturer_claim'),
(3, 7, 4, FALSE, 'manufacturer_claim'),
(4, 5, 1, FALSE, 'manufacturer_claim'),
(4, 6, 2, FALSE, 'manufacturer_claim'),
(4, 7, 3, FALSE, 'unverified');

-- Four-Level Rice Alternatives (Keyword: rice)
INSERT INTO products (
  category_id, brand_id, search_keyword, name, variant_label, tier_category,
  quantity_value, quantity_unit, image_url, packaging_material, packaging_recyclable,
  packaging_notes, environmental_summary, manufacturer_claims, safety_compliance_notes,
  ingredient_transparency_level
) VALUES
(3, 5, 'rice', 'Certified Organic Hand-Pounded Red Matta Rice', '1 kg Pack', 'premium_organic',
 1, 'kg', '/static/images/rice_premium.svg', 'Cloth & Paper Gusset Bag', TRUE,
 'Reusable cotton-lined paper pouch.',
 'Grown without synthetic pesticides or urea; lower methane-emitting SRI cultivation.',
 '100% NPOP Certified Organic single-origin paddy.',
 'FSSAI licensed; aflatoxin & heavy-metal batch tested.', 'full'),

(3, 6, 'rice', 'Unpolished Semi-Brown Sona Masoori Rice', '1 kg Pack', 'conscious_choice',
 1, 'kg', '/static/images/rice_conscious.svg', 'Recyclable Mono-PE Pouch', TRUE,
 'Single-polymer recyclable pouch.',
 'Minimal milling retains bran nutrition and reduces processing energy.',
 'Residue-tested single-origin grain.',
 'FSSAI licensed; pesticide residue within MRL limits.', 'full'),

(3, 7, 'rice', 'Steam-Cured Everyday Sona Masoori Rice', '1 kg Pack', 'budget_conscious',
 1, 'kg', '/static/images/rice_budget.svg', 'Woven Polypropylene Bag', FALSE,
 'Standard woven PP sack.',
 'Conventional irrigated paddy cultivation.',
 'Aged 12 months for non-sticky cooking.',
 'FSSAI licensed; AGMARK Grade A.', 'partial'),

(3, 8, 'rice', 'Economy Broken & Whole Parboiled Rice', '1 kg Pack', 'economy_choice',
 1, 'kg', '/static/images/rice_economy.svg', 'LDPE Polybag', FALSE,
 'Basic heat-sealed polythene bag.',
 'No environmental or farming practice data disclosed.',
 'Affordable daily calorie staple.',
 'FSSAI licensed.', 'basic');

INSERT INTO product_prices (product_id, unit_price, effective_date, is_current) VALUES
(5, 145.00, CURDATE(), TRUE),
(6, 88.00, CURDATE(), TRUE),
(7, 64.00, CURDATE(), TRUE),
(8, 46.00, CURDATE(), TRUE);

INSERT INTO organic_certifications (product_id, certifier_name, certificate_code, scope, verified_status) VALUES
(5, 'NPOP / India Organic (INDOCERT)', 'IN-ORG-33109', '100_organic', TRUE),
(6, 'None Declared (Lab Residue Tested)', NULL, 'none', FALSE),
(7, 'None Declared', NULL, 'none', FALSE),
(8, 'None Declared', NULL, 'none', FALSE);