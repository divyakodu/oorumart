# Oorumart (`oorumart.in`) - Dynamic Tenant Rendering Engine

## 1. How YAML Configs Turn into Live Storefronts

Oorumart uses **Dynamic Runtime Edge Rendering** (the same architectural pattern used by Shopify and Wix). You do **NOT** need a build script to generate static code files for every shop. 

Instead, **1 single renderer codebase** dynamically presents `yesfancy.oorumart.in`, `sarveshpan.oorumart.in`, or `bagammaflowers.oorumart.in` based on their YAML/JSON configuration.

---

## 2. Request Lifecycle Diagram

```
Buyer visits: https://yesfancy.oorumart.in
                    |
                    v
    [ Edge Middleware (Cloudflare) ]
    1. Extract host header -> "yesfancy"
    2. Fetch tenant config (yesfancy.yaml or DB row)
                    |
                    v
    [ Astro Template Renderer ]
    1. Inject CSS Variables:
       :root { --primary: #E94E77; --bg: #FAF7F2; }
    2. Render Layout Components:
       <AnnouncementBar text={config.announcement} />
       <HeroCarousel items={config.carousels} />
       <CategoryPills items={config.categories} />
       <ProductGrid products={dbProducts} />
                    |
                    v
    [ Instant HTML Response to Buyer (<0.8s LCP) ]
```

---

## 3. How the Code Interprets `yesfancy.yaml`

Here is the exact code logic inside the Astro storefront template (`src/pages/index.astro`):

```astro
---
// 1. Read Subdomain from Request
const host = Astro.request.headers.get('host') || '';
const slug = host.split('.')[0]; // "yesfancy"

// 2. Load Tenant Configuration (from DB or YAML file)
const tenant = await getTenantConfig(slug); 
const products = await getTenantProducts(tenant.id);
---

<!-- 3. Dynamic Styling via CSS Variables -->
<html style={`--primary: ${tenant.theme.primary}; --bg: ${tenant.theme.background};`}>
  <head>
    <title>{tenant.name}</title>
  </head>
  <body class="bg-[var(--bg)] font-sans">
    
    <!-- Dynamic Announcement Bar -->
    <header class="bg-[var(--primary)] text-white text-center py-2">
      {tenant.announcement_text}
    </header>

    <!-- Dynamic Hero Carousel -->
    <HeroCarousel items={tenant.carousels.offer_banner} />

    <!-- Dynamic Product Grid -->
    <div class="grid grid-cols-2 gap-4 p-4">
      {products.map(product => (
        <ProductCard 
          name={product.name} 
          price={product.price} 
          image={product.image}
          primaryColor={tenant.theme.primary}
        />
      ))}
    </div>

    <!-- Dynamic Bottom Checkout Sheet -->
    <CheckoutBar tenantPhone={tenant.phone} />
  </body>
</html>
```

---

## 4. Key Advantages of Dynamic Runtime Rendering

1. **Instant Updates**: When a shopkeeper changes a price, adds a banner, or updates shop colors in their dashboard, it updates the YAML/DB row. The shop updates **INSTANTLY** without any re-compilation or re-deployment!
2. **Zero Code Duplication**: You maintain 1 single Astro codebase. If you fix a bug or add a new cart feature, all 500 shops get the improvement immediately.
3. **Ultra-Low Storage**: 500 shops take 0 extra disk space. They are just rows in a database or YAML files in storage.
