-- =================================================================
-- OORUMART MULTI-TENANT SUPABASE DATABASE SCHEMA
-- Execute this script in your Supabase Dashboard SQL Editor
-- =================================================================

-- 1. SHOPS TABLE
CREATE TABLE IF NOT EXISTS shops (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    tagline VARCHAR(255),
    category VARCHAR(128) NOT NULL,
    template_key VARCHAR(128) NOT NULL DEFAULT 'gift_novelty_chumbak',
    phone VARCHAR(32) NOT NULL,
    announcement_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. SHOP THEMES TABLE
CREATE TABLE IF NOT EXISTS shop_themes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    shop_id UUID REFERENCES shops(id) ON DELETE CASCADE UNIQUE NOT NULL,
    primary_color VARCHAR(32) NOT NULL DEFAULT '#00A896',
    secondary_color VARCHAR(32) DEFAULT '#F4F4F9',
    accent_color VARCHAR(32) DEFAULT '#E63946',
    font_title VARCHAR(128) DEFAULT 'Playfair Display',
    font_body VARCHAR(128) DEFAULT 'Montserrat'
);

-- 3. CATEGORIES TABLE
CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(64) NOT NULL,
    shop_id UUID REFERENCES shops(id) ON DELETE CASCADE NOT NULL,
    label VARCHAR(255) NOT NULL,
    image_url TEXT,
    sort_order INT DEFAULT 0,
    PRIMARY KEY (id, shop_id)
);

-- 4. PRODUCTS TABLE
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(64) NOT NULL,
    shop_id UUID REFERENCES shops(id) ON DELETE CASCADE NOT NULL,
    category_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    mrp NUMERIC(10, 2),
    image_url TEXT NOT NULL,
    stock INT DEFAULT 100,
    badge VARCHAR(64),
    tags JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    PRIMARY KEY (id, shop_id)
);

-- 5. HERO SLIDES TABLE
CREATE TABLE IF NOT EXISTS hero_slides (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    shop_id UUID REFERENCES shops(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle TEXT,
    bg_gradient VARCHAR(255),
    cta_text VARCHAR(128),
    cta_link TEXT,
    image_url TEXT,
    sort_order INT DEFAULT 0
);

-- 6. ORDERS TABLE
CREATE TABLE IF NOT EXISTS orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    order_id VARCHAR(64) UNIQUE NOT NULL,
    shop_id UUID REFERENCES shops(id) ON DELETE CASCADE NOT NULL,
    shop_slug VARCHAR(64) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    phone VARCHAR(32) NOT NULL,
    address TEXT,
    items JSONB NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    status VARCHAR(64) DEFAULT 'Order Placed & Processing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- INDEXES FOR FAST SSR & CATALOG QUERIES
CREATE INDEX IF NOT EXISTS idx_shops_slug ON shops(slug);
CREATE INDEX IF NOT EXISTS idx_products_shop_cat ON products(shop_id, category_id);
CREATE INDEX IF NOT EXISTS idx_categories_shop ON categories(shop_id);
CREATE INDEX IF NOT EXISTS idx_orders_shop_phone ON orders(shop_slug, phone);

-- ENABLE ROW LEVEL SECURITY (RLS) FOR PUBLIC ACCESS
ALTER TABLE shops ENABLE ROW LEVEL SECURITY;
ALTER TABLE shop_themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE hero_slides ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- PUBLIC READ & WRITE POLICIES
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public Read Access for Shops') THEN
        CREATE POLICY "Public Read Access for Shops" ON shops FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public Read Access for Shop Themes') THEN
        CREATE POLICY "Public Read Access for Shop Themes" ON shop_themes FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public Read Access for Categories') THEN
        CREATE POLICY "Public Read Access for Categories" ON categories FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public Read Access for Products') THEN
        CREATE POLICY "Public Read Access for Products" ON products FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public Read Access for Hero Slides') THEN
        CREATE POLICY "Public Read Access for Hero Slides" ON hero_slides FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public Access for Orders') THEN
        CREATE POLICY "Public Access for Orders" ON orders FOR ALL USING (true);
    END IF;
END $$;

-- 7. ENABLE SUPABASE REALTIME WEBSOCKET PUSH FOR ORDERS
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE orders;
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- Ignore if already added
END $$;

