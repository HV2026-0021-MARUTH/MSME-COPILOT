-- Seed Data for MARUTHI Demo Shop: Sri Lakshmi General Store

-- 1. Demo Shop
INSERT INTO shops (id, name, owner_name, phone, latitude, longitude, locality, city, created_at)
VALUES (
    'shop_001',
    'Sri Lakshmi General Store',
    'Ramesh Kumar',
    '+91-9876543210',
    17.4399,
    78.4483,
    'Ameerpet',
    'Hyderabad',
    CURRENT_TIMESTAMP
) ON CONFLICT (id) DO NOTHING;

-- 2. Demo Products
INSERT INTO products (id, shop_id, sku, name, category, brand, unit, purchase_price, selling_price, reorder_level, created_at)
VALUES
    ('prod_001', 'shop_001', 'SKU-001', 'Coca-Cola 250ml', 'Beverages', 'Coca-Cola', 'bottle', 15.00, 20.00, 15, CURRENT_TIMESTAMP),
    ('prod_002', 'shop_001', 'SKU-002', 'Lays Classic Salted 50g', 'Snacks', 'Lays', 'pack', 16.00, 20.00, 20, CURRENT_TIMESTAMP),
    ('prod_003', 'shop_001', 'SKU-003', 'Amul Taaza Milk 500ml', 'Dairy', 'Amul', 'packet', 24.00, 27.00, 10, CURRENT_TIMESTAMP),
    ('prod_004', 'shop_001', 'SKU-004', 'Tata Salt 1kg', 'Staples', 'Tata', 'pack', 22.00, 28.00, 10, CURRENT_TIMESTAMP),
    ('prod_005', 'shop_001', 'SKU-005', 'Surf Excel Easy Wash 500g', 'Personal & Home Care', 'Unilever', 'pack', 62.00, 72.00, 5, CURRENT_TIMESTAMP),
    ('prod_006', 'shop_001', 'SKU-006', 'Thums Up 750ml', 'Beverages', 'Coca-Cola', 'bottle', 32.00, 40.00, 12, CURRENT_TIMESTAMP),
    ('prod_007', 'shop_001', 'SKU-007', 'Parle-G Gold 100g', 'Snacks', 'Parle', 'pack', 8.50, 10.00, 25, CURRENT_TIMESTAMP),
    ('prod_008', 'shop_001', 'SKU-008', 'Maggi 2-Min Noodles 70g', 'Snacks', 'Nestle', 'pack', 11.50, 14.00, 20, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- 3. Initial Inventory
INSERT INTO inventory (id, shop_id, product_id, quantity, updated_at)
VALUES
    ('inv_001', 'shop_001', 'prod_001', 6, CURRENT_TIMESTAMP),   -- Low stock item (6 < 15 reorder level)
    ('inv_002', 'shop_001', 'prod_002', 45, CURRENT_TIMESTAMP),  -- Good stock
    ('inv_003', 'shop_001', 'prod_003', 8, CURRENT_TIMESTAMP),   -- Low stock item
    ('inv_004', 'shop_001', 'prod_004', 30, CURRENT_TIMESTAMP),  -- Moderate stock
    ('inv_005', 'shop_001', 'prod_005', 4, CURRENT_TIMESTAMP),   -- Low stock item
    ('inv_006', 'shop_001', 'prod_006', 22, CURRENT_TIMESTAMP),  -- Good stock
    ('inv_007', 'shop_001', 'prod_007', 80, CURRENT_TIMESTAMP),  -- High stock / top seller
    ('inv_008', 'shop_001', 'prod_008', 50, CURRENT_TIMESTAMP)   -- Good stock
ON CONFLICT (id) DO NOTHING;

-- 4. Initial Purchases Record
INSERT INTO purchases (id, shop_id, supplier_name, invoice_number, total_amount, invoice_image_url, created_at)
VALUES
    ('purch_001', 'shop_001', 'Sri Venkateswara Wholesale Depot', 'INV-2026-0801', 4520.00, NULL, CURRENT_TIMESTAMP - INTERVAL '5 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO purchase_items (id, purchase_id, product_id, quantity, unit_cost)
VALUES
    ('pi_001', 'purch_001', 'prod_001', 100, 15.00),
    ('pi_002', 'purch_001', 'prod_002', 100, 16.00),
    ('pi_003', 'purch_001', 'prod_007', 160, 8.50)
ON CONFLICT (id) DO NOTHING;

-- 5. Historical Sales Record
INSERT INTO sales (id, shop_id, total_amount, total_cost, profit, source, created_at)
VALUES
    ('sale_001', 'shop_001', 100.00, 77.00, 23.00, 'voice_text', CURRENT_TIMESTAMP - INTERVAL '1 day'),
    ('sale_002', 'shop_001', 78.00, 59.00, 19.00, 'voice_text', CURRENT_TIMESTAMP - INTERVAL '2 hours')
ON CONFLICT (id) DO NOTHING;

INSERT INTO sale_items (id, sale_id, product_id, quantity, unit_price, unit_cost, profit)
VALUES
    ('si_001', 'sale_001', 'prod_001', 3, 20.00, 15.00, 15.00),
    ('si_002', 'sale_001', 'prod_002', 2, 20.00, 16.00, 8.00),
    ('si_003', 'sale_002', 'prod_003', 2, 27.00, 24.00, 6.00),
    ('si_004', 'sale_002', 'prod_007', 2, 10.00, 8.50, 3.00),
    ('si_005', 'sale_002', 'prod_008', 1, 14.00, 11.50, 2.50)
ON CONFLICT (id) DO NOTHING;

-- 6. Initial Insights
INSERT INTO business_insights (id, shop_id, type, title, description, severity, confidence, created_at)
VALUES
    ('ins_001', 'shop_001', 'restock', 'RESTOCK: Coca-Cola 250ml', 'Current stock (6) is below reorder level (15). Stock-out expected within 1 day.', 'warning', 'high', CURRENT_TIMESTAMP),
    ('ins_002', 'shop_001', 'slow_moving', 'SLOW MOVING: Surf Excel Easy Wash 500g', 'Stock velocity is low. Consider promotional bundle with detergents.', 'info', 'medium', CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;
